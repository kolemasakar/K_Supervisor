from __future__ import annotations

from multiprocessing import get_all_start_methods, get_context
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from threading import RLock
from time import monotonic
from typing import Any

from models.agent import AgentRunRequest, AgentRunResult
from models.enums import ExecutionStatus

from .contracts import ExecutionControl, RuntimeLimits
from .errors import (
    AgentRuntimeError,
    RuntimeCancelled,
    RuntimeDependencyUnavailable,
    RuntimeTimeout,
    RuntimeValidationError,
    RuntimeWorkerCrashed,
    RuntimeWorkerReportedError,
    RuntimeWorkerTerminationError,
)
from .in_process import AgentRuntimeHandler


def _worker_entry(handler: AgentRuntimeHandler, request: AgentRunRequest, limits: RuntimeLimits, cancelled: Any, connection: Connection) -> None:
    control = ExecutionControl(limits=limits, cancelled=cancelled)
    try:
        result = handler(request, control)
        if not isinstance(result, AgentRunResult):
            raise RuntimeValidationError("runtime handler must return AgentRunResult")
        envelope = {"kind": "result", "result": result.model_dump(mode="json"), "usage": dict(control.usage)}
    except BaseException as exc:
        if isinstance(exc, AgentRuntimeError):
            error = {"code": exc.code, "category": exc.category, "retryable": exc.retryable, "status": exc.status.value, "message": str(exc)}
        else:
            error = {"code": "RUNTIME_EXECUTION_ERROR", "category": "EXECUTION_ERROR", "retryable": False, "status": ExecutionStatus.FAILED.value, "message": str(exc)}
        envelope = {"kind": "error", "error": error, "usage": dict(control.usage)}
    try:
        connection.send(envelope)
    finally:
        connection.close()


class ProcessRuntimeAdapter:
    """One-process-per-invocation runtime with parent-enforced termination."""

    def __init__(self, *, start_method: str | None = None, poll_interval_seconds: float = 0.005, cancellation_grace_seconds: float = 0.05, termination_grace_seconds: float = 0.10, kill_grace_seconds: float = 0.10):
        available = get_all_start_methods()
        selected = start_method or "spawn"
        if selected not in available:
            raise ValueError(f"unsupported multiprocessing start method: {selected}")
        for name, value in (("poll_interval_seconds", poll_interval_seconds), ("cancellation_grace_seconds", cancellation_grace_seconds), ("termination_grace_seconds", termination_grace_seconds), ("kill_grace_seconds", kill_grace_seconds)):
            if value <= 0:
                raise ValueError(f"{name} must be > 0")
        self._context = get_context(selected)
        self.start_method = selected
        self.poll_interval_seconds = poll_interval_seconds
        self.cancellation_grace_seconds = cancellation_grace_seconds
        self.termination_grace_seconds = termination_grace_seconds
        self.kill_grace_seconds = kill_grace_seconds
        self._handlers: dict[str, AgentRuntimeHandler] = {}
        self._workers: set[BaseProcess] = set()
        self._lock = RLock()

    def register(self, agent_id: str, handler: AgentRuntimeHandler) -> None:
        with self._lock:
            self._handlers[agent_id] = handler

    def unregister(self, agent_id: str) -> None:
        with self._lock:
            self._handlers.pop(agent_id, None)

    @property
    def active_worker_count(self) -> int:
        with self._lock:
            return sum(1 for process in self._workers if process.is_alive())

    def execute(self, request: AgentRunRequest, control: ExecutionControl) -> AgentRunResult:
        control.check_cancelled()
        with self._lock:
            handler = self._handlers.get(request.agent_id)
        if handler is None:
            raise RuntimeDependencyUnavailable(f"no process runtime handler for agent: {request.agent_id}")
        parent_connection, child_connection = self._context.Pipe(duplex=False)
        child_cancelled = self._context.Event()
        process = self._context.Process(target=_worker_entry, args=(handler, request, control.limits, child_cancelled, child_connection), name=f"k-supervisor-agent-{request.run_id}")
        try:
            try:
                process.start()
            except Exception as exc:
                raise RuntimeDependencyUnavailable(f"unable to start isolated runtime worker: {exc}") from exc
            finally:
                child_connection.close()
            with self._lock:
                self._workers.add(process)
            timeout = control.limits.timeout_seconds
            deadline = None if timeout is None else monotonic() + timeout
            while True:
                if control.cancelled.is_set():
                    self._stop_worker(process, child_cancelled)
                    raise RuntimeCancelled("execution cancelled")
                if deadline is not None and monotonic() >= deadline:
                    self._stop_worker(process, child_cancelled)
                    raise RuntimeTimeout("agent execution timed out")
                if parent_connection.poll(self.poll_interval_seconds):
                    try:
                        envelope = parent_connection.recv()
                    except EOFError:
                        envelope = None
                    if envelope is not None:
                        return self._decode_envelope(envelope, control)
                if not process.is_alive():
                    if parent_connection.poll(self.poll_interval_seconds):
                        try:
                            envelope = parent_connection.recv()
                        except EOFError:
                            envelope = None
                        if envelope is not None:
                            return self._decode_envelope(envelope, control)
                    raise RuntimeWorkerCrashed(f"isolated runtime worker exited without result; exitcode={process.exitcode}")
        finally:
            parent_connection.close()
            if process.pid is not None:
                self._cleanup_worker(process, child_cancelled)
            with self._lock:
                self._workers.discard(process)

    def _decode_envelope(self, envelope: dict[str, Any], control: ExecutionControl) -> AgentRunResult:
        usage = envelope.get("usage", {})
        if isinstance(usage, dict):
            control.usage.update({key: float(value) for key, value in usage.items()})
        kind = envelope.get("kind")
        if kind == "result":
            return AgentRunResult.model_validate(envelope.get("result"))
        if kind == "error":
            error = envelope.get("error") or {}
            raise RuntimeWorkerReportedError(str(error.get("message", "isolated runtime worker failed")), code=str(error.get("code", "RUNTIME_EXECUTION_ERROR")), category=str(error.get("category", "EXECUTION_ERROR")), retryable=bool(error.get("retryable", False)), status=ExecutionStatus(error.get("status", ExecutionStatus.FAILED.value)))
        raise RuntimeValidationError("isolated runtime worker returned an invalid envelope")

    def _stop_worker(self, process: BaseProcess, cancelled: Any) -> None:
        cancelled.set()
        process.join(self.cancellation_grace_seconds)
        if not process.is_alive():
            return
        process.terminate()
        process.join(self.termination_grace_seconds)
        if not process.is_alive():
            return
        kill = getattr(process, "kill", None)
        if kill is not None:
            kill()
            process.join(self.kill_grace_seconds)
        if process.is_alive():
            raise RuntimeWorkerTerminationError(f"isolated runtime worker did not terminate; pid={process.pid}")

    def _cleanup_worker(self, process: BaseProcess, cancelled: Any) -> None:
        if process.is_alive():
            self._stop_worker(process, cancelled)
        process.join(timeout=0)
        close = getattr(process, "close", None)
        if close is not None and not process.is_alive():
            close()
