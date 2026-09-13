from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from threading import RLock

from models.agent import AgentRunRequest, AgentRunResult

from .contracts import ExecutionControl
from .errors import RuntimeDependencyUnavailable, RuntimeTimeout, RuntimeValidationError


AgentRuntimeHandler = Callable[[AgentRunRequest, ExecutionControl], AgentRunResult]


class InProcessRuntimeAdapter:
    def __init__(self):
        self._handlers: dict[str, AgentRuntimeHandler] = {}
        self._lock = RLock()

    def register(self, agent_id: str, handler: AgentRuntimeHandler) -> None:
        with self._lock:
            self._handlers[agent_id] = handler

    def unregister(self, agent_id: str) -> None:
        with self._lock:
            self._handlers.pop(agent_id, None)

    def execute(
        self,
        request: AgentRunRequest,
        control: ExecutionControl,
    ) -> AgentRunResult:
        control.check_cancelled()
        with self._lock:
            handler = self._handlers.get(request.agent_id)
        if handler is None:
            raise RuntimeDependencyUnavailable(
                f"no in-process runtime handler for agent: {request.agent_id}"
            )

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="k-supervisor-agent")
        future = executor.submit(handler, request, control)
        try:
            result = future.result(timeout=control.limits.timeout_seconds)
        except FutureTimeout as exc:
            control.cancel()
            future.cancel()
            raise RuntimeTimeout("agent execution timed out") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        if not isinstance(result, AgentRunResult):
            raise RuntimeValidationError("runtime handler must return AgentRunResult")
        return result
