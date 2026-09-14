from models.capability import CapabilityRequirement
from observability import AuditTimeline, MetricsCollector, ObservableSupervisorKernel, ReliabilityValidator
from tests.phase12_support import build_reference_stack
from tests.phase15_support import NOW


def test_routing_metrics_and_audit_timeline(tmp_path):
    store, _, _, _, _, _, kernel = build_reference_stack(tmp_path)
    observed = ObservableSupervisorKernel(kernel)
    requirement = CapabilityRequirement(
        capability_id="research.reference",
        version_constraint="1.0.0",
        operation="run",
    )
    result = observed.run_task(
        "P12",
        "observed research",
        requirement,
        {"query": "phase 15", "sources": ["source A", "source B"]},
    )
    assert result.status.value == "SUCCEEDED"

    routes = store.list_routing_records("P12")
    assert len(routes) == 1
    assert routes[0].selected_agent_id == result.agent_id
    assert len(routes[0].candidate_agent_ids) == 2

    metrics = MetricsCollector(store).snapshot("P12", NOW)
    assert metrics.routing_records == 1
    assert metrics.agent_runs_total == 1
    assert metrics.agents[0].success_rate == 1.0

    event_types = {item.event_type for item in AuditTimeline(store).events("P12")}
    assert "ROUTING_SELECTED" in event_types
    assert ReliabilityValidator(store).check("P12").passed
