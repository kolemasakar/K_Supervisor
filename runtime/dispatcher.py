from __future__ import annotations

from threading import RLock

from models.agent import AgentError, AgentRunRequest, AgentRunResult
from models.enums import ExecutionStatus
from registry.agent_registry import AgentAvailability, AgentRegistry

from .contracts import ExecutionControl, RuntimeAdapter, RuntimeLimits
from .errors import AgentRuntimeError, RuntimeValidationError
from .health import RuntimeHealthTracker
from .idempotency import MemoryIdempotencyStore


class AgentRuntimeDispatcher:
    def __init__(self, registry: AgentRegistry, adapter: RuntimeAdapter, *, unavailable_after: int = 3):
        self.registry = registry
        self.adapter = adapter
        self.idempotency = MemoryIdempotencyStore()
        self.health = RuntimeHealthTracker(registry, unavailable_after)
        self._controls: dict[str, ExecutionControl] = {}
        self._lock = RLock()

    def cancel(self, run_id: str) -> bool:
        with self._lock:
            control = self._controls.get(run_id)
        if control is None:
            return False
        control.cancel()
        return True

    def dispatch(self, request: AgentRunRequest) -> AgentRunResult:
        if self.registry.get(request.agent_id) is None:
            return self._error(request, RuntimeValidationError("agent is not registered"))
        availability = self.registry.availability(request.agent_id)
        if availability not in {AgentAvailability.AVAILABLE, AgentAvailability.DEGRADED}:
            return self._blocked(request, f"agent is not runnable: {availability}")

        try:
            limits = RuntimeLimits.from_request(request.limits)
            replay = self.idempotency.replay(request)
            if replay is not None:
                return replay
        except Exception as exc:
            return self._error(request, exc)

        control = ExecutionControl(limits)
        with self._lock:
            self._controls[request.run_id] = control
        self.registry.set_availability(request.agent_id, AgentAvailability.BUSY)

        try:
            result = self.adapter.execute(request, control)
        except Exception as exc:
            result = self._error(request, exc)
        finally:
            with self._lock:
                self._controls.pop(request.run_id, None)

        if control.usage:
            result = result.model_copy(
                update={"metrics": {**result.metrics, "runtime_usage": dict(control.usage)}}
            )
        if result.status == ExecutionStatus.SUCCEEDED:
            try:
                self.idempotency.remember(request, result)
            except Exception as exc:
                result = self._error(request, exc)
        self.health.record(result)
        return result

    @staticmethod
    def _blocked(request: AgentRunRequest, message: str) -> AgentRunResult:
        return AgentRuntimeDispatcher._make_error(
            request,
            ExecutionStatus.BLOCKED,
            "RUNTIME_AGENT_UNAVAILABLE",
            "DEPENDENCY_UNAVAILABLE",
            message,
            True,
        )

    @staticmethod
    def _error(request: AgentRunRequest, exc: Exception) -> AgentRunResult:
        if isinstance(exc, AgentRuntimeError):
            return AgentRuntimeDispatcher._make_error(
                request, exc.status, exc.code, exc.category, str(exc), exc.retryable
            )
        return AgentRuntimeDispatcher._make_error(
            request,
            ExecutionStatus.FAILED,
            "RUNTIME_EXECUTION_ERROR",
            "EXECUTION_ERROR",
            str(exc),
            False,
        )

    @staticmethod
    def _make_error(
        request: AgentRunRequest,
        status: ExecutionStatus,
        code: str,
        category: str,
        message: str,
        retryable: bool,
    ) -> AgentRunResult:
        return AgentRunResult(
            request_id=request.request_id,
            project_id=request.project_id,
            task_id=request.task_id,
            workflow_run_id=request.workflow_run_id,
            run_id=request.run_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            status=status,
            error=AgentError(
                code=code,
                category=category,
                message=message,
                retryable=retryable,
            ),
        )
