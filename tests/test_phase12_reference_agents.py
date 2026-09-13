from models.capability import CapabilityRequirement
from models.enums import ExecutionStatus

from tests.phase12_support import build_reference_stack


def _requirement(capability_id: str) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=capability_id,
        version_constraint="^1.0.0",
        operation="run",
    )


def test_at_least_three_reference_agent_types_use_common_contract(tmp_path):
    store, _, agents, _, _, builds, kernel = build_reference_stack(tmp_path)

    assert len(builds) >= 5
    assert len({build.agent.agent_type for build in builds}) >= 5
    assert {build.agent.contract_version for build in builds} == {"1.0"}

    critic = kernel.run_task(
        "P12",
        "critic",
        _requirement("critique.reference"),
        {"content": "This reference content is long enough to pass structural critique."},
    )
    report = kernel.run_task(
        "P12",
        "report",
        _requirement("report.reference"),
        {"sections": ["One", "Two"]},
    )
    analysis = kernel.run_task(
        "P12",
        "analysis",
        _requirement("analysis.reference"),
        {"values": [1, 2, 3]},
    )

    assert critic.status == ExecutionStatus.SUCCEEDED
    assert critic.output["verdict"] == "PASS"
    assert report.status == ExecutionStatus.SUCCEEDED
    assert report.output["report"] == "One\n\nTwo"
    assert analysis.status == ExecutionStatus.SUCCEEDED
    assert analysis.output["mean"] == 2.0
    store.close()
