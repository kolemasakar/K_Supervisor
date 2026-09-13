import pytest

from models.agent import AgentDescriptor, CapabilityRef
from models.capability import CapabilityDescriptor, CapabilityRequirement
from registry import (
    AgentAvailability,
    AgentRegistry,
    CapabilityRegistry,
    CapabilityResolutionError,
    DuplicateRegistrationError,
    RegistryConflictError,
)
from registry.versioning import matches_version


def capability(version="1.0.0", operations=("run",), description="Test"):
    return CapabilityDescriptor(
        capability_id="analysis.test",
        capability_version=version,
        description=description,
        operations=operations,
        input_schema="schema://input",
        output_schema="schema://output",
    )


def agent(agent_id, version="1.0.0", status="AVAILABLE"):
    return AgentDescriptor(
        agent_id=agent_id,
        agent_type="TEST",
        agent_version="1.0.0",
        display_name=agent_id,
        capabilities=(
            CapabilityRef(
                capability_id="analysis.test",
                capability_version=version,
            ),
        ),
        status=status,
    )


def requirement(constraint="^1.0.0", operation="run"):
    return CapabilityRequirement(
        capability_id="analysis.test",
        version_constraint=constraint,
        operation=operation,
    )


def test_version_constraints():
    assert matches_version("1.4.0", "^1.2.0")
    assert not matches_version("2.0.0", "^1.2.0")
    assert matches_version("1.2.7", "~1.2.0")
    assert not matches_version("1.3.0", "~1.2.0")
    assert matches_version("1.5.0", ">=1.2,<2")


def test_capability_registry_resolves_highest_compatible_version():
    registry = CapabilityRegistry()
    for version in ("1.0.0", "1.4.0", "2.0.0"):
        registry.register(capability(version))
    assert registry.resolve("analysis.test", "^1.0.0", "run").capability_version == "1.4.0"


def test_capability_registry_conflict_is_rejected():
    registry = CapabilityRegistry()
    registry.register(capability())
    assert registry.register(capability()) == capability()
    with pytest.raises(RegistryConflictError):
        registry.register(capability(description="Different"))


def test_agent_registration_requires_registered_capability():
    capabilities = CapabilityRegistry()
    agents = AgentRegistry(capabilities)
    with pytest.raises(CapabilityResolutionError):
        agents.register(agent("agent.one"))
    capabilities.register(capability())
    assert agents.register(agent("agent.one")).agent_id == "agent.one"


def test_duplicate_agent_id_conflict_is_rejected():
    capabilities = CapabilityRegistry()
    capabilities.register(capability())
    agents = AgentRegistry(capabilities)
    agents.register(agent("agent.one"))
    with pytest.raises(DuplicateRegistrationError):
        agents.register(
            AgentDescriptor(
                agent_id="agent.one",
                agent_type="OTHER",
                agent_version="1.0.0",
                display_name="Changed",
                capabilities=(
                    CapabilityRef(
                        capability_id="analysis.test",
                        capability_version="1.0.0",
                    ),
                ),
                status="AVAILABLE",
            )
        )


def test_provider_resolution_honors_availability_version_and_operation():
    capabilities = CapabilityRegistry()
    capabilities.register(capability("1.0.0"))
    capabilities.register(capability("1.5.0"))
    capabilities.register(capability("2.0.0"))
    agents = AgentRegistry(capabilities)
    agents.register(agent("agent.old", "1.0.0"))
    agents.register(agent("agent.best", "1.5.0"))
    agents.register(agent("agent.v2", "2.0.0"))
    agents.register(agent("agent.busy", "1.5.0", "BUSY"))

    providers = agents.find_providers(requirement("^1.0.0"))
    assert [item.agent.agent_id for item in providers] == ["agent.best", "agent.old"]

    agents.set_availability("agent.best", AgentAvailability.UNAVAILABLE)
    assert [item.agent.agent_id for item in agents.find_providers(requirement("^1.0.0"))] == ["agent.old"]


def test_degraded_provider_is_opt_in():
    capabilities = CapabilityRegistry()
    capabilities.register(capability())
    agents = AgentRegistry(capabilities)
    agents.register(agent("agent.degraded", status="DEGRADED"))
    assert agents.find_providers(requirement()) == ()
    assert agents.find_providers(requirement(), include_degraded=True)[0].agent.agent_id == "agent.degraded"


def test_unregister_removes_provider_without_registry_redesign():
    capabilities = CapabilityRegistry()
    capabilities.register(capability())
    agents = AgentRegistry(capabilities)
    agents.register(agent("agent.one"))
    assert len(agents.find_providers(requirement())) == 1
    agents.unregister("agent.one")
    assert agents.find_providers(requirement()) == ()
