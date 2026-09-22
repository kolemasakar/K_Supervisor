from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from threading import RLock
from types import MappingProxyType
from typing import Any

from .telemetry import REDACTED


class UnsafeTelemetryAttributeError(ValueError):
    pass


_EVENT_SCHEMAS = {
    "service.request.started": frozenset({"method", "route"}),
    "service.request.completed": frozenset({"method", "route", "status_class"}),
    "service.request.rejected": frozenset({"method", "route", "status_class", "error_code"}),
    "auth.accepted": frozenset({"result", "method", "route"}),
    "auth.rejected": frozenset({"result", "method", "route", "error_code"}),
    "policy.decision": frozenset({"decision", "operation"}),
    "provider.call.started": frozenset({"provider_type", "operation"}),
    "provider.call.completed": frozenset({"provider_type", "operation", "result"}),
    "provider.call.failed": frozenset({"provider_type", "operation", "result", "error_code"}),
    "repository.operation.started": frozenset({"provider", "operation"}),
    "repository.operation.completed": frozenset({"provider", "operation", "result"}),
    "repository.operation.blocked": frozenset({"provider", "operation", "result", "error_code"}),
    "repository.operation.failed": frozenset({"provider", "operation", "result", "error_code"}),
    "release.prepare.started": frozenset({"target", "operation"}),
    "release.prepare.completed": frozenset({"target", "operation", "result"}),
    "release.prepare.failed": frozenset({"target", "operation", "result", "error_code"}),
    "release.publication_required": frozenset({"target", "operation", "result"}),
    "telemetry.export.completed": frozenset({"exporter", "result", "queue_depth"}),
    "telemetry.export.failed": frozenset({"exporter", "result", "error_code", "queue_depth"}),
    "telemetry.export.dropped": frozenset({"exporter", "reason", "queue_depth"}),
}
PRODUCTION_EVENT_SCHEMAS = MappingProxyType(_EVENT_SCHEMAS)
PRODUCTION_EVENT_NAMES = tuple(sorted(_EVENT_SCHEMAS))

_SECRET_MARKERS = (
    "secret://",
    "bearer ",
    "authorization:",
    "authorization=",
    "cookie:",
    "cookie=",
    "api_key=",
    "apikey=",
    "access_token=",
    "refresh_token=",
)
_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_TOKEN = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


def _safe_text(value: str, *, limit: int = 256) -> str:
    normalized = value.replace("\r", " ").replace("\n", " ")
    lowered = normalized.lower()
    if any(marker in lowered for marker in _SECRET_MARKERS):
        return REDACTED
    if len(normalized) > limit:
        return normalized[:limit]
    return normalized


def safe_production_attributes(
    event_name: str,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    allowed = PRODUCTION_EVENT_SCHEMAS.get(event_name)
    if allowed is None:
        raise UnsafeTelemetryAttributeError(f"unregistered production telemetry event: {event_name}")
    values = attributes or {}
    if len(values) > 16:
        raise UnsafeTelemetryAttributeError("production telemetry attribute count exceeds limit")
    unknown = set(values) - allowed
    if unknown:
        raise UnsafeTelemetryAttributeError(
            "unsafe production telemetry attributes: " + ", ".join(sorted(unknown))
        )
    safe: dict[str, Any] = {}
    for key, value in values.items():
        if value is None or isinstance(value, (bool, int, float)):
            safe[key] = value
        elif isinstance(value, str):
            safe[key] = _safe_text(value, limit=160)
        else:
            raise UnsafeTelemetryAttributeError(
                f"production telemetry attribute {key!r} must be scalar"
            )
    return safe


class StructuredLogger:
    def __init__(self, sink, *, include_project_id: bool = False):
        self._sink = sink
        self._include_project_id = include_project_id

    def emit(
        self,
        *,
        event_name: str,
        component: str,
        level: str = "INFO",
        timestamp: datetime | None = None,
        status: str | None = None,
        duration_ms: float | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        project_id: str | None = None,
        operation: str | None = None,
        error_code: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> bool:
        normalized_level = level.upper()
        if normalized_level not in _LEVELS:
            raise ValueError("unsupported structured log level")
        if not _TOKEN.fullmatch(component):
            raise ValueError("structured log component must use a bounded token")
        if duration_ms is not None and duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        safe_attributes = safe_production_attributes(event_name, attributes)
        at = timestamp or datetime.now(timezone.utc)
        if at.tzinfo is None:
            raise ValueError("structured log timestamp must be timezone-aware")
        at = at.astimezone(timezone.utc)
        payload = {
            "attributes": safe_attributes,
            "component": component,
            "correlation_id": None if correlation_id is None else _safe_text(correlation_id, limit=128),
            "duration_ms": duration_ms,
            "error_code": None if error_code is None else _safe_text(error_code, limit=96),
            "event_name": event_name,
            "level": normalized_level,
            "operation": None if operation is None else _safe_text(operation, limit=96),
            "project_id": (
                _safe_text(project_id, limit=128)
                if self._include_project_id and project_id is not None
                else None
            ),
            "request_id": None if request_id is None else _safe_text(request_id, limit=128),
            "status": None if status is None else _safe_text(status, limit=64),
            "timestamp": at.isoformat().replace("+00:00", "Z"),
        }
        line = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        try:
            self._sink.write(line)
            flush = getattr(self._sink, "flush", None)
            if callable(flush):
                flush()
        except Exception:
            return False
        return True


def normalize_service_route(path: str) -> str:
    route = path.split("?", 1)[0].rstrip("/") or "/"
    prefix = "/api/v1/projects/"
    if route.startswith(prefix):
        remainder = route[len(prefix):]
        parts = remainder.split("/", 1)
        if parts[0]:
            suffix = "" if len(parts) == 1 else "/" + parts[1]
            return prefix + "{project_id}" + suffix
    return route


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    return format(value, ".15g")


class ProductionMetricRegistry:
    DEFAULT_ROUTES = frozenset({
        "/healthz",
        "/readyz",
        "/api/v1/projects",
        "/api/v1/projects/{project_id}",
        "/api/v1/projects/{project_id}/lifecycle-transitions",
        "/api/v1/projects/{project_id}/operational-transitions",
    })
    DEFAULT_PROVIDER_TYPES = frozenset({"MODEL", "TOOL", "EMAIL", "GITHUB"})
    DEFAULT_PROVIDER_OPERATIONS = frozenset({"invoke", "send", "execute", "read", "write"})
    DEFAULT_REPOSITORY_PROVIDERS = frozenset({"FILESYSTEM", "GITHUB"})
    DEFAULT_REPOSITORY_OPERATIONS = frozenset({
        "create_repository", "bootstrap_files", "list_files", "read_file",
        "handoff_pull_request", "create_tag",
    })
    DEFAULT_RELEASE_TARGETS = frozenset({"CHATGPT_PLUGIN", "GPT_STORE", "PYPI"})
    DEFAULT_RELEASE_OPERATIONS = frozenset({"prepare", "validate", "publication_handoff"})
    DEFAULT_EXPORTERS = frozenset({"otlp_http", "prometheus", "structured_log"})

    def __init__(
        self,
        *,
        service_routes: frozenset[str] | None = None,
        provider_types: frozenset[str] | None = None,
        provider_operations: frozenset[str] | None = None,
        repository_providers: frozenset[str] | None = None,
        repository_operations: frozenset[str] | None = None,
        release_targets: frozenset[str] | None = None,
        release_operations: frozenset[str] | None = None,
        exporters: frozenset[str] | None = None,
    ):
        self.service_routes = service_routes or self.DEFAULT_ROUTES
        self.provider_types = provider_types or self.DEFAULT_PROVIDER_TYPES
        self.provider_operations = provider_operations or self.DEFAULT_PROVIDER_OPERATIONS
        self.repository_providers = repository_providers or self.DEFAULT_REPOSITORY_PROVIDERS
        self.repository_operations = repository_operations or self.DEFAULT_REPOSITORY_OPERATIONS
        self.release_targets = release_targets or self.DEFAULT_RELEASE_TARGETS
        self.release_operations = release_operations or self.DEFAULT_RELEASE_OPERATIONS
        self.exporters = exporters or self.DEFAULT_EXPORTERS
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._duration_sum: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._duration_count: dict[tuple[tuple[str, str], ...], int] = defaultdict(int)
        self._lock = RLock()

    @staticmethod
    def _require(value: str, allowed: frozenset[str], field: str) -> str:
        if value not in allowed:
            raise ValueError(f"{field} is outside the configured bounded vocabulary")
        return value

    @staticmethod
    def _labels(**values: str) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(values.items()))

    def _increment(self, family: str, labels: tuple[tuple[str, str], ...], amount: int = 1) -> None:
        with self._lock:
            self._counters[(family, labels)] += amount

    def record_service_request(self, method: str, route: str, status_code: int, duration_ms: float) -> None:
        method = method.upper()
        self._require(method, frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}), "method")
        route = normalize_service_route(route)
        self._require(route, self.service_routes, "route")
        if duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        status_class = f"{status_code // 100}xx"
        if status_class not in {"1xx", "2xx", "3xx", "4xx", "5xx"}:
            raise ValueError("status code is outside HTTP status classes")
        labels = self._labels(method=method, route=route, status_class=status_class)
        self._increment("ksupervisor_service_requests_total", labels)
        duration_labels = self._labels(method=method, route=route)
        with self._lock:
            self._duration_sum[duration_labels] += duration_ms / 1000.0
            self._duration_count[duration_labels] += 1

    def record_auth(self, result: str) -> None:
        self._require(result, frozenset({"accepted", "rejected"}), "auth result")
        self._increment("ksupervisor_auth_attempts_total", self._labels(result=result))

    def record_provider(self, provider_type: str, operation: str, result: str) -> None:
        self._require(provider_type, self.provider_types, "provider_type")
        self._require(operation, self.provider_operations, "provider operation")
        self._require(result, frozenset({"success", "failed", "blocked"}), "provider result")
        self._increment(
            "ksupervisor_provider_calls_total",
            self._labels(provider_type=provider_type, operation=operation, result=result),
        )

    def record_repository(self, provider: str, operation: str, result: str) -> None:
        self._require(provider, self.repository_providers, "repository provider")
        self._require(operation, self.repository_operations, "repository operation")
        self._require(result, frozenset({"success", "failed", "blocked"}), "repository result")
        self._increment(
            "ksupervisor_repository_operations_total",
            self._labels(provider=provider, operation=operation, result=result),
        )

    def record_release(self, target: str, operation: str, result: str) -> None:
        self._require(target, self.release_targets, "release target")
        self._require(operation, self.release_operations, "release operation")
        self._require(result, frozenset({"success", "failed", "required"}), "release result")
        self._increment(
            "ksupervisor_release_operations_total",
            self._labels(target=target, operation=operation, result=result),
        )

    def record_export(self, exporter: str, result: str) -> None:
        self._require(exporter, self.exporters, "exporter")
        self._require(result, frozenset({"success", "failed"}), "export result")
        self._increment(
            "ksupervisor_telemetry_exports_total",
            self._labels(exporter=exporter, result=result),
        )

    def record_export_drop(self, exporter: str, reason: str, amount: int = 1) -> None:
        self._require(exporter, self.exporters, "exporter")
        self._require(reason, frozenset({"queue_full", "export_failed", "shutdown_timeout", "serialization"}), "drop reason")
        if amount < 1:
            raise ValueError("drop amount must be positive")
        self._increment(
            "ksupervisor_telemetry_export_dropped_total",
            self._labels(exporter=exporter, reason=reason),
            amount,
        )

    def set_queue_depth(self, exporter: str, depth: int) -> None:
        self._require(exporter, self.exporters, "exporter")
        if depth < 0:
            raise ValueError("queue depth must be non-negative")
        with self._lock:
            self._gauges[
                ("ksupervisor_telemetry_queue_depth", self._labels(exporter=exporter))
            ] = float(depth)

    def render_prometheus(self) -> str:
        lines = [
            "# HELP ksupervisor_service_requests_total Service requests by bounded route template and status class.",
            "# TYPE ksupervisor_service_requests_total counter",
            "# HELP ksupervisor_service_request_duration_seconds Service request duration in seconds.",
            "# TYPE ksupervisor_service_request_duration_seconds summary",
            "# HELP ksupervisor_auth_attempts_total Authentication attempts by result.",
            "# TYPE ksupervisor_auth_attempts_total counter",
            "# HELP ksupervisor_provider_calls_total Provider calls by bounded provider, operation and result.",
            "# TYPE ksupervisor_provider_calls_total counter",
            "# HELP ksupervisor_repository_operations_total Repository operations by bounded provider, operation and result.",
            "# TYPE ksupervisor_repository_operations_total counter",
            "# HELP ksupervisor_release_operations_total Release operations by bounded target, operation and result.",
            "# TYPE ksupervisor_release_operations_total counter",
            "# HELP ksupervisor_telemetry_exports_total Telemetry export attempts by exporter and result.",
            "# TYPE ksupervisor_telemetry_exports_total counter",
            "# HELP ksupervisor_telemetry_export_dropped_total Telemetry records dropped by exporter and reason.",
            "# TYPE ksupervisor_telemetry_export_dropped_total counter",
            "# HELP ksupervisor_telemetry_queue_depth Current bounded exporter queue depth.",
            "# TYPE ksupervisor_telemetry_queue_depth gauge",
        ]
        with self._lock:
            counters = sorted(self._counters.items())
            gauges = sorted(self._gauges.items())
            duration_sum = sorted(self._duration_sum.items())
            duration_count = dict(self._duration_count)
        for (family, labels), value in counters:
            lines.append(self._render_sample(family, labels, value))
        for labels, value in duration_sum:
            lines.append(self._render_sample(
                "ksupervisor_service_request_duration_seconds_sum", labels, value
            ))
            lines.append(self._render_sample(
                "ksupervisor_service_request_duration_seconds_count",
                labels,
                duration_count[labels],
            ))
        for (family, labels), value in gauges:
            lines.append(self._render_sample(family, labels, value))
        return "\n".join(lines) + "\n"

    @staticmethod
    def _render_sample(
        family: str,
        labels: tuple[tuple[str, str], ...],
        value: float | int,
    ) -> str:
        if labels:
            encoded = ",".join(f'{key}="{_escape_label(item)}"' for key, item in labels)
            family = f"{family}{{{encoded}}}"
        return f"{family} {_number(value)}"
