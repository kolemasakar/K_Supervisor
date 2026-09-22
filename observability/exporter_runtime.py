from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from ipaddress import ip_address
from typing import Callable, Protocol
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .exporters import OpenTelemetryProjectionExporter
from .production import ProductionMetricRegistry


class ExporterHealth(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


@dataclass(frozen=True)
class ExporterSnapshot:
    health: ExporterHealth
    queued: int
    exported: int
    dropped: int
    failures: int


class ProductionTelemetryExporter(Protocol):
    def export(self, records, *, timeout_seconds: float) -> None: ...


class OTLPHTTPTransport(Protocol):
    def send(self, projected_records, *, timeout_seconds: float) -> None: ...


class OTLPHTTPExporter:
    """Production adapter boundary for an OTLP/HTTP transport.

    The transport is responsible for producing valid OTLP protobuf bytes. This keeps
    OpenTelemetry dependencies optional while making queue/timeout/failure semantics
    deterministic in the core package.
    """

    def __init__(self, transport: OTLPHTTPTransport):
        self.transport = transport
        self._projection = OpenTelemetryProjectionExporter()

    def export(self, records, *, timeout_seconds: float) -> None:
        projected = self._projection.export(records)
        self.transport.send(projected, timeout_seconds=timeout_seconds)


class ProtobufOTLPHTTPTransport:
    def __init__(
        self,
        endpoint: str,
        encoder: Callable[[tuple[dict, ...]], bytes],
        *,
        headers: dict[str, str] | None = None,
    ):
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
            raise ValueError("OTLP endpoint must use http or https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("OTLP endpoint must not contain credentials")
        if parsed.scheme == "http":
            host = parsed.hostname.lower()
            loopback = host == "localhost"
            if not loopback:
                try:
                    loopback = ip_address(host).is_loopback
                except ValueError:
                    loopback = False
            if not loopback:
                raise ValueError("cleartext OTLP HTTP is allowed only on loopback")
        self.endpoint = endpoint
        self.encoder = encoder
        self.headers = dict(headers or {})

    def send(self, projected_records, *, timeout_seconds: float) -> None:
        payload = self.encoder(projected_records)
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("OTLP protobuf encoder must return non-empty bytes")
        headers = {
            "Content-Type": "application/x-protobuf",
            **self.headers,
        }
        request = Request(self.endpoint, data=payload, headers=headers, method="POST")
        with urlopen(request, timeout=timeout_seconds) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(f"OTLP HTTP exporter returned status {response.status}")


class BoundedExporterSupervisor:
    def __init__(
        self,
        name: str,
        exporter: ProductionTelemetryExporter,
        *,
        queue_size: int = 256,
        batch_size: int = 32,
        timeout_seconds: float = 5.0,
        max_retries: int = 1,
        retry_backoff_seconds: float = 0.0,
        metrics: ProductionMetricRegistry | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if queue_size < 1:
            raise ValueError("queue_size must be positive")
        if batch_size < 1 or batch_size > queue_size:
            raise ValueError("batch_size must be positive and no larger than queue_size")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_retries < 0 or max_retries > 10:
            raise ValueError("max_retries must be between 0 and 10")
        if retry_backoff_seconds < 0 or retry_backoff_seconds > 60:
            raise ValueError("retry_backoff_seconds must be between 0 and 60")
        self.name = name
        self.exporter = exporter
        self.queue_size = queue_size
        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.metrics = metrics
        self.sleeper = sleeper
        self._queue = deque()
        self._health = ExporterHealth.AVAILABLE
        self._exported = 0
        self._dropped = 0
        self._failures = 0
        self._update_depth()

    def enqueue(self, record) -> bool:
        if len(self._queue) >= self.queue_size:
            self._dropped += 1
            self._health = ExporterHealth.DEGRADED
            if self.metrics is not None:
                self.metrics.record_export_drop(self.name, "queue_full")
            self._update_depth()
            return False
        self._queue.append(record)
        self._update_depth()
        return True

    def flush(self) -> ExporterSnapshot:
        while self._queue:
            batch = tuple(list(self._queue)[: self.batch_size])
            exported = False
            for attempt in range(self.max_retries + 1):
                try:
                    self.exporter.export(batch, timeout_seconds=self.timeout_seconds)
                except Exception:
                    self._failures += 1
                    self._health = ExporterHealth.DEGRADED
                    if attempt < self.max_retries and self.retry_backoff_seconds:
                        self.sleeper(self.retry_backoff_seconds)
                    continue
                exported = True
                break
            for _ in range(len(batch)):
                self._queue.popleft()
            if exported:
                self._exported += len(batch)
                self._health = ExporterHealth.AVAILABLE
                if self.metrics is not None:
                    self.metrics.record_export(self.name, "success")
            else:
                self._dropped += len(batch)
                self._health = ExporterHealth.UNAVAILABLE
                if self.metrics is not None:
                    self.metrics.record_export(self.name, "failed")
                    self.metrics.record_export_drop(self.name, "export_failed", len(batch))
            self._update_depth()
        return self.snapshot()

    def shutdown(self, *, flush: bool = True) -> ExporterSnapshot:
        if flush:
            return self.flush()
        remaining = len(self._queue)
        if remaining:
            self._dropped += remaining
            self._queue.clear()
            self._health = ExporterHealth.DEGRADED
            if self.metrics is not None:
                self.metrics.record_export_drop(self.name, "shutdown_timeout", remaining)
            self._update_depth()
        return self.snapshot()

    def snapshot(self) -> ExporterSnapshot:
        return ExporterSnapshot(
            health=self._health,
            queued=len(self._queue),
            exported=self._exported,
            dropped=self._dropped,
            failures=self._failures,
        )

    def _update_depth(self) -> None:
        if self.metrics is not None:
            self.metrics.set_queue_depth(self.name, len(self._queue))
