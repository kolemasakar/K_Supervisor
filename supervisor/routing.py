from __future__ import annotations

from models.capability import CapabilityRequirement
from registry.agent_registry import CapabilityProvider
from registry.versioning import parse_version


class NoProviderError(RuntimeError):
    pass


class ProviderRouter:
    def select(
        self,
        requirement: CapabilityRequirement,
        providers: tuple[CapabilityProvider, ...],
    ) -> CapabilityProvider:
        if not providers:
            raise NoProviderError(
                f"no provider for {requirement.capability_id} {requirement.version_constraint}"
            )

        preferred = requirement.preferences.get("preferred_agents", [])
        preference_order = {agent_id: index for index, agent_id in enumerate(preferred)}

        def rank(item: CapabilityProvider):
            preferred_rank = preference_order.get(item.agent.agent_id, len(preference_order) + 1)
            version = parse_version(item.capability.capability_version)
            return (preferred_rank, tuple(-part for part in version), item.agent.agent_id)

        return min(providers, key=rank)
