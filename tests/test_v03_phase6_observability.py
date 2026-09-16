from datetime import datetime, timezone

from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from observability import (
    OpenTelemetryProjectionExporter,
    PrometheusProjectionExporter,
    REDACTED,
    ServiceHealthEvaluator,
    TelemetryRecorder,
    TelemetryTimeline,
)
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry
from runtime import AgentRuntimeDispatcher
from service_api import LIFECYCLE_WRITE_SCOPE, ServiceApiV1, ServicePrincipal
from tests.phase12_support import build_reference_stack

NOW = datetime(2026, 9, 16, 14, 0, tzinfo=timezone.utc)


def project(project_id="P6"):
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.IDEA,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def test_telemetry_persists_redacted_attributes_and_survives_restart(tmp_path):
    path = tmp_path / "state.db"
    with SQLitePersistenceStore(path) as store:
        ProjectRegistry(store).register(project())
        recorder = TelemetryRecorder(store)
        original = {"token": "abc", "nested": {"secret_ref": "secret://project/P6/api"}, "safe": "ok"}
        recorder.record(project_id="P6", event_name="service.request", occurred_at=NOW, attributes=original)
        assert original["token"] == "abc"
        saved = store.list_telemetry_records("P6")[0]
        assert saved.attributes["token"] == REDACTED
        assert saved.attributes["nested"]["secret_ref"] == REDACTED
        assert saved.attributes["safe"] == "ok"
    with SQLitePersistenceStore(path) as recovered:
        records = recovered.list_telemetry_records("P6")
        assert len(records) == 1
        assert records[0].event_name == "service.request"
        assert ProjectRegistry(recovered).recover("P6").telemetry_records == records


def test_telemetry_timeline_is_deterministic(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        ProjectRegistry(store).register(project())
        recorder = TelemetryRecorder(store)
        recorder.record(project_id="P6", event_name="second", occurred_at=NOW.replace(second=2))
        recorder.record(project_id="P6", event_name="first", occurred_at=NOW.replace(second=1))
        assert [item.event_name for item in TelemetryTimeline(store).events("P6")] == ["first", "second"]


def test_exporter_projections_are_deterministic_and_redacted(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        ProjectRegistry(store).register(project())
        recorder = TelemetryRecorder(store)
        recorder.record(project_id="P6", event_name="runtime.dispatch.completed", occurred_at=NOW, correlation_id="REQ-1", attributes={"authorization": "Bearer bad", "safe": 1})
        records = store.list_telemetry_records("P6")
        assert PrometheusProjectionExporter().export(records) == (("ksupervisor_runtime_dispatch_completed_total", 1),)
        otel = OpenTelemetryProjectionExporter().export(records)[0]
        assert otel["trace_id"] == "REQ-1"
        assert otel["attributes"]["authorization"] == REDACTED
        assert otel["attributes"]["safe"] == 1


def test_health_and_readiness_are_component_based_not_project_state(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        registry = ProjectRegistry(store)
        registry.register(project())
        evaluator = ServiceHealthEvaluator({
            "persistence": (lambda: store.is_initialized, True),
            "optional-exporter": (lambda: False, False),
        })
        assert evaluator.health().live is True
        readiness = evaluator.readiness()
        assert readiness.ready is True
        registry.transition_operational("P6", ProjectOperationalState.PAUSED, NOW.replace(minute=1))
        assert evaluator.readiness().ready is True
        failed = ServiceHealthEvaluator({"persistence": (lambda: False, True)})
        assert failed.readiness().ready is False


def test_service_api_emits_scoped_telemetry_without_changing_api_contract(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        projects = ProjectRegistry(store)
        projects.register(project())
        recorder = TelemetryRecorder(store)
        api = ServiceApiV1(projects, store, telemetry=recorder)
        principal = ServicePrincipal(principal_id="owner", scopes=frozenset({LIFECYCLE_WRITE_SCOPE}))
        response = api.dispatch(
            "POST",
            "/api/v1/projects/P6/lifecycle-transitions",
            principal=principal,
            idempotency_key="p6-1",
            body={"to_state": "ONBOARDING", "reason": "phase6", "trigger": "owner"},
        )
        assert response.status_code == 200
        records = store.list_telemetry_records("P6")
        assert len(records) == 1
        assert records[0].event_name == "service.request.completed"
        assert records[0].service_operation.startswith("POST /api/v1/projects/P6")
        assert records[0].status == "200"


def test_runtime_emits_full_correlation_and_telemetry_failure_is_nonfatal(tmp_path):
    store, _, agents, adapter, _, _, kernel = build_reference_stack(tmp_path)
    recorder = TelemetryRecorder(store)
    kernel.dispatcher = AgentRuntimeDispatcher(agents, adapter, telemetry=recorder)
    from models.capability import CapabilityRequirement
    result = kernel.run_task(
        "P12",
        "phase6 telemetry",
        CapabilityRequirement(capability_id="research.reference", version_constraint="1.0.0", operation="run"),
        {"query": "phase6", "sources": ["A"]},
    )
    records = store.list_telemetry_records("P12")
    assert [item.event_name for item in records] == ["runtime.dispatch.started", "runtime.dispatch.completed"]
    completed = records[-1]
    assert completed.request_id == result.request_id
    assert completed.task_id == result.task_id
    assert completed.workflow_run_id == result.workflow_run_id
    assert completed.run_id == result.run_id
    assert completed.agent_id == result.agent_id
    assert completed.capability_id == result.capability_id

    class BrokenTelemetry:
        def record(self, **kwargs):
            raise RuntimeError("telemetry unavailable")

    kernel.dispatcher = AgentRuntimeDispatcher(agents, adapter, telemetry=BrokenTelemetry())
    result2 = kernel.run_task(
        "P12",
        "nonfatal telemetry",
        CapabilityRequirement(capability_id="research.reference", version_constraint="1.0.0", operation="run"),
        {"query": "still works", "sources": ["A"]},
    )
    assert result2.status.value == "SUCCEEDED"
    store.close()
