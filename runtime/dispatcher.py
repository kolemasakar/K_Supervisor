from __future__ import annotations

from threading import RLock

from models.agent import AgentError, AgentRunRequest, AgentRunResult
from models.enums import ExecutionStatus
from persistence.base import PersistenceStore
from registry.agent_registry import AgentAvailability, AgentRegistry

from .contracts import ExecutionControl, RuntimeAdapter, RuntimeLimits
from .errors import AgentRuntimeError, RuntimeValidationError
from .health import RuntimeHealthTracker
from .idempotency import MemoryIdempotencyStore, PersistenceIdempotencyStore


class AgentRuntimeDispatcher:
    def __init__(
        self,
        registry: AgentRegistry,
        adapter: RuntimeAdapter,
        *,
        unavailable_after: int = 3,
        persistence_store: PersistenceStore | None = None,
        telemetry=None,
    ):
        self.registry = registry
        self.adapter = adapter
        self.idempotency = (
            PersistenceIdempotencyStore(persistence_store)
            if persistence_store is not None
            else MemoryIdempotencyStore()
        )
        self.health = RuntimeHealthTracker(registry, unavailable_after)
        self.telemetry = telemetry
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
        self._telemetry(request, "runtime.dispatch.started", status="STARTED")
        if self.registry.get(request.agent_id) is None:
            result = self._error(request, RuntimeValidationError("agent is not registered"))
            self._telemetry(request, "runtime.dispatch.completed", status=result.status.value)
            return result
        availability = self.registry.availability(request.agent_id)
        if availability not in {AgentAvailability.AVAILABLE, AgentAvailability.DEGRADED}:
            result = self._blocked(request, f"agent is not runnable: {availability}")
            self._telemetry(request, "runtime.dispatch.completed", status=result.status.value)
            return result

        try:
            limits = RuntimeLimits.from_request(request.limits)
            replay = self.idempotency.replay(request)
            if replay is not None:
                self._telemetry(
                    request,
                    "runtime.dispatch.completed",
                    status=replay.status.value,
                    attributes={"idempotent_replay": True},
                )
                return replay
        except Exception as exc:
            result = self._error(request, exc)
            self._telemetry(request, "runtime.dispatch.completed", status=result.status.value)
            return result

        control = ExecutionControl(limits)
        with self._lock:
            self._controls[request.run_id] = control
        self.registry.set_availability(request.agent_id, AgentAvailability.BUSY)

        try:
            result = self.adapter.execute(request, control)
            self._validate_result(request, result)
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
        self._telemetry(request, "runtime.dispatch.completed", status=result.status.value, attributes={"runtime_usage": dict(control.usage)})
        return result


    def _telemetry(self, request: AgentRunRequest, event_name: str, *, status: str | None = None, attributes: dict | None = None) -> None:
        if self.telemetry is None:
            return
        try:
            self.telemetry.record(
                project_id=request.project_id,
                event_name=event_name,
                correlation_id=request.request_id,
                request_id=request.request_id,
                task_id=request.task_id,
                workflow_run_id=request.workflow_run_id,
                run_id=request.run_id,
                agent_id=request.agent_id,
                capability_id=request.capability_id,
                status=status,
                attributes=attributes,
            )
        except Exception:
            pass

    @staticmethod
    def _validate_result(request: AgentRunRequest, result: AgentRunResult) -> None:
        fields = (
            "request_id",
            "project_id",
            "task_id",
            "workflow_run_id",
            "run_id",
            "agent_id",
            "capability_id",
            "capability_version",
        )
        mismatched = [name for name in fields if getattr(request, name) != getattr(result, name)]
        if mismatched:
            raise RuntimeValidationError(
                f"runtime result correlation mismatch: {', '.join(mismatched)}"
            )

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
