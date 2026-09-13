from __future__ import annotations

from dataclasses import dataclass

from models.agent import AgentRunResult
from models.enums import ExecutionStatus
from registry.agent_registry import AgentAvailability, AgentRegistry


@dataclass
class AgentHealth:
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0


class RuntimeHealthTracker:
    def __init__(self, registry: AgentRegistry, unavailable_after: int = 3):
        if unavailable_after < 1:
            raise ValueError("unavailable_after must be >= 1")
        self.registry = registry
        self.unavailable_after = unavailable_after
        self._health: dict[str, AgentHealth] = {}

    def state(self, agent_id: str) -> AgentHealth:
        return self._health.setdefault(agent_id, AgentHealth())

    def record(self, result: AgentRunResult) -> None:
        health = self.state(result.agent_id)
        if result.status == ExecutionStatus.SUCCEEDED:
            health.successes += 1
            health.consecutive_failures = 0
            self.registry.set_availability(result.agent_id, AgentAvailability.AVAILABLE)
            return

        if result.status == ExecutionStatus.CANCELLED:
            self.registry.set_availability(result.agent_id, AgentAvailability.AVAILABLE)
            return

        if result.status == ExecutionStatus.BLOCKED:
            self.registry.set_availability(result.agent_id, AgentAvailability.AVAILABLE)
            return

        health.failures += 1
        health.consecutive_failures += 1
        if health.consecutive_failures >= self.unavailable_after:
            self.registry.set_availability(result.agent_id, AgentAvailability.UNAVAILABLE)
        else:
            self.registry.set_availability(result.agent_id, AgentAvailability.DEGRADED)
