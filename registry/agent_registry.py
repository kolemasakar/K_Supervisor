from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from models.agent import AgentDescriptor
from models.capability import CapabilityDescriptor, CapabilityRequirement

from .capability_registry import CapabilityRegistry
from .errors import CapabilityResolutionError, DuplicateRegistrationError
from .versioning import matches_version, parse_version


class AgentAvailability(StrEnum):
    REGISTERED = "REGISTERED"
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class CapabilityProvider:
    agent: AgentDescriptor
    capability: CapabilityDescriptor
    availability: AgentAvailability


class AgentRegistry:
    def __init__(self, capabilities: CapabilityRegistry):
        self.capabilities = capabilities
        self._agents: dict[str, AgentDescriptor] = {}
        self._availability: dict[str, AgentAvailability] = {}

    def register(self, descriptor: AgentDescriptor) -> AgentDescriptor:
        current = self._agents.get(descriptor.agent_id)
        if current is not None:
            if current == descriptor:
                return current
            raise DuplicateRegistrationError(
                f"agent_id already registered: {descriptor.agent_id}"
            )

        for reference in descriptor.capabilities:
            if self.capabilities.get(reference.capability_id, reference.capability_version) is None:
                raise CapabilityResolutionError(
                    f"agent references unregistered capability: "
                    f"{reference.capability_id}@{reference.capability_version}"
                )

        try:
            availability = AgentAvailability(descriptor.status)
        except ValueError:
            availability = AgentAvailability.REGISTERED

        self._agents[descriptor.agent_id] = descriptor
        self._availability[descriptor.agent_id] = availability
        return descriptor

    def unregister(self, agent_id: str) -> AgentDescriptor:
        try:
            descriptor = self._agents.pop(agent_id)
        except KeyError as exc:
            raise KeyError(agent_id) from exc
        self._availability.pop(agent_id, None)
        return descriptor

    def get(self, agent_id: str) -> AgentDescriptor | None:
        return self._agents.get(agent_id)

    def list(self) -> tuple[AgentDescriptor, ...]:
        return tuple(self._agents[key] for key in sorted(self._agents))

    def set_availability(self, agent_id: str, availability: AgentAvailability | str) -> None:
        if agent_id not in self._agents:
            raise KeyError(agent_id)
        self._availability[agent_id] = AgentAvailability(availability)

    def availability(self, agent_id: str) -> AgentAvailability:
        if agent_id not in self._agents:
            raise KeyError(agent_id)
        return self._availability[agent_id]

    def find_providers(
        self,
        requirement: CapabilityRequirement,
        include_degraded: bool = False,
    ) -> tuple[CapabilityProvider, ...]:
        permitted = {AgentAvailability.AVAILABLE}
        if include_degraded:
            permitted.add(AgentAvailability.DEGRADED)

        candidates: list[CapabilityProvider] = []
        for agent in self._agents.values():
            availability = self._availability[agent.agent_id]
            if availability not in permitted:
                continue
            for reference in agent.capabilities:
                if reference.capability_id != requirement.capability_id:
                    continue
                if not matches_version(reference.capability_version, requirement.version_constraint):
                    continue
                capability = self.capabilities.get(
                    reference.capability_id, reference.capability_version
                )
                if capability is None or requirement.operation not in capability.operations:
                    continue
                candidates.append(
                    CapabilityProvider(
                        agent=agent,
                        capability=capability,
                        availability=availability,
                    )
                )

        candidates.sort(key=lambda item: item.agent.agent_id)
        candidates.sort(
            key=lambda item: parse_version(item.capability.capability_version),
            reverse=True,
        )
        return tuple(candidates)
