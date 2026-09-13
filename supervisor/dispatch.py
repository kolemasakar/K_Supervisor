from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from models.agent import AgentRunRequest, AgentRunResult


class AgentDispatcher(Protocol):
    def dispatch(self, request: AgentRunRequest) -> AgentRunResult: ...


class DispatchUnavailableError(RuntimeError):
    pass


AgentHandler = Callable[[AgentRunRequest], AgentRunResult]


class LocalAgentDispatcher:
    def __init__(self):
        self._handlers: dict[str, AgentHandler] = {}

    def register(self, agent_id: str, handler: AgentHandler) -> None:
        self._handlers[agent_id] = handler

    def unregister(self, agent_id: str) -> None:
        self._handlers.pop(agent_id, None)

    def dispatch(self, request: AgentRunRequest) -> AgentRunResult:
        handler = self._handlers.get(request.agent_id)
        if handler is None:
            raise DispatchUnavailableError(f"no dispatcher handler for agent: {request.agent_id}")
        return handler(request)
