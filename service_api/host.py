from __future__ import annotations

import json
import socket
from enum import Enum
from http import HTTPStatus
from ipaddress import ip_address, ip_network
from socketserver import ThreadingMixIn
from threading import BoundedSemaphore, Condition, RLock, Thread
from time import monotonic
from typing import Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer


class HostState(str, Enum):
    STARTING = "STARTING"
    READY = "READY"
    DRAINING = "DRAINING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class HostLifecycle:
    def __init__(self):
        self._state = HostState.STARTING
        self._active = 0
        self._condition = Condition(RLock())

    @property
    def state(self) -> HostState:
        with self._condition:
            return self._state

    @property
    def active_requests(self) -> int:
        with self._condition:
            return self._active
    def mark_ready(self) -> None:
        with self._condition:
            if self._state != HostState.STARTING:
                raise RuntimeError("host can become READY only from STARTING")
            self._state = HostState.READY
            self._condition.notify_all()

    def mark_failed(self) -> None:
        with self._condition:
            if self._state == HostState.STARTING:
                self._state = HostState.FAILED
                self._condition.notify_all()

    def begin_request(self) -> bool:
        with self._condition:
            if self._state != HostState.READY:
                return False
            self._active += 1
            return True

    def end_request(self) -> None:
        with self._condition:
            if self._active <= 0:
                raise RuntimeError("host request accounting underflow")
            self._active -= 1
            self._condition.notify_all()

    def begin_draining(self) -> None:
        with self._condition:
            if self._state in {HostState.STOPPED, HostState.FAILED}:
                return
            self._state = HostState.DRAINING
            self._condition.notify_all()

    def wait_for_drain(self, timeout: float | None) -> bool:
        deadline = None if timeout is None else monotonic() + timeout
        with self._condition:
            while self._active:
                remaining = None if deadline is None else deadline - monotonic()
                if remaining is not None and remaining <= 0:
                    return False
                self._condition.wait(remaining)
            return True
    def mark_stopped(self) -> None:
        with self._condition:
            if self._active:
                raise RuntimeError("cannot stop host while requests are active")
            self._state = HostState.STOPPED
            self._condition.notify_all()


class _QuietRequestHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return


class _BoundedThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = False
    block_on_close = False
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        request_handler,
        *,
        workers: int,
        socket_timeout: float,
    ):
        self._worker_slots = BoundedSemaphore(workers)
        self._socket_timeout = socket_timeout
        self.request_queue_size = max(1, workers * 2)
        super().__init__(server_address, request_handler)

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(self._socket_timeout)
        return request, address

    def process_request(self, request, client_address) -> None:
        self._worker_slots.acquire()
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._worker_slots.release()
            raise

    def process_request_thread(self, request, client_address) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._worker_slots.release()

    def handle_error(self, request, client_address) -> None:
        return
class ServiceHostApplication:
    """Operational WSGI surface around the authoritative Phase-2 application."""

    def __init__(self, runtime, lifecycle: HostLifecycle, config):
        self.runtime = runtime
        self.lifecycle = lifecycle
        self.config = config
        self._trusted_networks = tuple(
            ip_network(value, strict=False) for value in config.trusted_proxies
        )

    def __call__(self, environ: dict[str, Any], start_response):
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/")).rstrip("/") or "/"
        if path in {"/healthz", "/readyz"} and method != "GET":
            return self._json_error(start_response, 405, "method not allowed")
        if path == "/healthz":
            live = self.lifecycle.state not in {HostState.FAILED, HostState.STOPPED}
            return self._probe(start_response, live, "live" if live else "not-live")
        if path == "/readyz":
            ready = self._ready()
            return self._probe(start_response, ready, "ready" if ready else "not-ready")

        proxy_error = self._proxy_error(environ)
        if proxy_error is not None:
            return self._json_error(start_response, proxy_error[0], proxy_error[1])

        if not self.lifecycle.begin_request():
            return self._json_error(start_response, 503, "service is draining")
        try:
            return self.runtime.app(environ, start_response)
        finally:
            self.lifecycle.end_request()

    def _ready(self) -> bool:
        if self.lifecycle.state != HostState.READY:
            return False
        try:
            return bool(self.runtime.health.readiness().ready)
        except Exception:
            return False
    def _proxy_error(self, environ: dict[str, Any]) -> tuple[int, str] | None:
        if not self.config.proxy_mode:
            return None
        remote = str(environ.get("REMOTE_ADDR", ""))
        try:
            peer = ip_address(remote)
        except ValueError:
            return 403, "untrusted proxy peer"
        if not any(peer in network for network in self._trusted_networks):
            return 403, "untrusted proxy peer"
        forwarded = str(environ.get("HTTP_X_FORWARDED_PROTO", ""))
        scheme = forwarded.split(",", 1)[0].strip().lower()
        if scheme != "https":
            return 400, "secure forwarded scheme is required"
        return None

    @staticmethod
    def _probe(start_response, ok: bool, status: str):
        code = 200 if ok else 503
        payload = json.dumps({"status": status}, separators=(",", ":")).encode("utf-8")
        phrase = HTTPStatus(code).phrase
        start_response(
            f"{code} {phrase}",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [payload]

    @staticmethod
    def _json_error(start_response, code: int, message: str):
        payload = json.dumps(
            {"api_version": "v1", "error": {"code": "HOST_REJECTED", "message": message}},
            separators=(",", ":"),
        ).encode("utf-8")
        start_response(
            f"{code} {HTTPStatus(code).phrase}",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [payload]


class ServiceHost:
    """Bounded single-node WSGI host with explicit drain/resource ownership."""

    def __init__(self, runtime, config):
        self.runtime = runtime
        self.config = config
        self.lifecycle = HostLifecycle()
        self.application = ServiceHostApplication(runtime, self.lifecycle, config)
        self._server: _BoundedThreadingWSGIServer | None = None
        self._thread: Thread | None = None
        try:
            self._server = _BoundedThreadingWSGIServer(
                (config.bind_host, config.port),
                _QuietRequestHandler,
                workers=config.workers,
                socket_timeout=config.socket_timeout_seconds,
            )
            self._server.set_app(self.application)
        except BaseException:
            self.lifecycle.mark_failed()
            raise

    @property
    def address(self) -> tuple[str, int]:
        server = self._require_server()
        host, port = server.server_address[:2]
        return str(host), int(port)

    @property
    def state(self) -> HostState:
        return self.lifecycle.state

    def start(self) -> None:
        server = self._require_server()
        if self._thread is not None:
            raise RuntimeError("service host is already started")
        try:
            if not self.runtime.qualifier.qualify(()).ready:
                raise RuntimeError("service deployment qualification is not ready")
            thread = Thread(
                target=server.serve_forever,
                name="k-supervisor-service",
                daemon=False,
            )
            self._thread = thread
            thread.start()
            self.lifecycle.mark_ready()
        except BaseException:
            self.lifecycle.mark_failed()
            server.server_close()
            raise
    def wait(self, timeout: float | None = None) -> bool:
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout)
        return not thread.is_alive()

    def stop(self) -> bool:
        server = self._require_server()
        state = self.lifecycle.state
        if state == HostState.STOPPED:
            return True
        if state == HostState.FAILED:
            server.server_close()
            self.runtime.close()
            return True
        if self._thread is None:
            self.lifecycle.begin_draining()
            server.server_close()
            self.runtime.close()
            self.lifecycle.mark_stopped()
            return True

        self.lifecycle.begin_draining()
        server.shutdown()
        self.wait(self.config.drain_timeout_seconds)
        drained = self.lifecycle.wait_for_drain(self.config.drain_timeout_seconds)
        server.server_close()
        if drained:
            self.runtime.close()
            self.lifecycle.mark_stopped()
            return True

        finalizer = Thread(
            target=self._finish_after_drain,
            name="k-supervisor-drain-finalizer",
            daemon=True,
        )
        finalizer.start()
        return False

    def _finish_after_drain(self) -> None:
        self.lifecycle.wait_for_drain(None)
        self.runtime.close()
        self.lifecycle.mark_stopped()

    def _require_server(self) -> _BoundedThreadingWSGIServer:
        if self._server is None:
            raise RuntimeError("service host is unavailable")
        return self._server


def create_service_host(runtime) -> ServiceHost:
    config = runtime.config.service_host
    if config is None:
        raise ValueError("service_host configuration is required")
    return ServiceHost(runtime, config)
