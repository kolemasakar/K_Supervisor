from models.capability import CapabilityRequirement
from models.enums import ExecutionStatus
from registry.agent_registry import AgentAvailability

from tests.phase12_support import build_reference_stack


def test_research_capability_has_two_interchangeable_providers(tmp_path):
    store, _, agents, _, _, _, kernel = build_reference_stack(tmp_path)

    requirement = CapabilityRequirement(
        capability_id="research.reference",
        version_constraint="^1.0.0",
        operation="run",
        preferences={"preferred_agents": ["reference.research.alpha"]},
    )
    providers = agents.find_providers(requirement)
    assert {item.agent.agent_id for item in providers} == {
        "reference.research.alpha",
        "reference.research.beta",
    }

    first = kernel.run_task(
        "P12",
        "research alpha",
        requirement,
        {"query": "test", "sources": ["source one"]},
    )
    assert first.status == ExecutionStatus.SUCCEEDED
    assert first.output["provider"] == "alpha"

    agents.set_availability("reference.research.alpha", AgentAvailability.UNAVAILABLE)
    second = kernel.run_task(
        "P12",
        "research fallback",
        CapabilityRequirement(
            capability_id="research.reference",
            version_constraint="^1.0.0",
            operation="run",
        ),
        {"query": "test", "sources": ["source one"]},
    )
    assert second.status == ExecutionStatus.SUCCEEDED
    assert second.output["provider"] == "beta"
    store.close()
