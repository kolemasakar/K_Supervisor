import io
import json
from datetime import datetime, timezone
from io import BytesIO

from integrations.gateway import SideEffectGateway
from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from observability import (
    ProductionMetricRegistry,
    ProductionObservability,
    StructuredLogger,
    TelemetryRecorder,
)
from persistence import SQLitePersistenceStore
from providers import ProviderDescriptor, ProviderResponse
from registry import ProjectRegistry, ProviderRegistry
from service_api import (
    LIFECYCLE_WRITE_SCOPE,
    READ_SCOPE,
    ServiceApiV1,
    ServicePrincipal,
    StaticBearerAuthenticator,
    WsgiServiceAppV1,
)
from tests.phase10_support import FakeProvider
from tests.test_v03_phase3_side_effect_gateway import allowed_stack, request

NOW = datetime(2026, 9, 22, 21, 30, tzinfo=timezone.utc)


def _project(project_id="P6I"):
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.IDEA,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def test_service_boundary_records_normalized_safe_telemetry_and_metrics(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        projects = ProjectRegistry(store)
        projects.register(_project())
        sink = io.StringIO()
        metrics = ProductionMetricRegistry()
        observer = ProductionObservability(
            telemetry=TelemetryRecorder(store),
            logger=StructuredLogger(sink),
            metrics=metrics,
        )
        api = ServiceApiV1(projects, store, observability=observer)
        principal = ServicePrincipal(
            principal_id="private-owner-id",
            scopes=frozenset({LIFECYCLE_WRITE_SCOPE}),
        )
        response = api.dispatch(
            "POST",
            "/api/v1/projects/P6I/lifecycle-transitions",
            principal=principal,
            idempotency_key="phase6-instrumentation",
            body={"to_state": "ONBOARDING", "reason": "test", "trigger": "owner"},
        )
        assert response.status_code == 200
        record = store.list_telemetry_records("P6I")[-1]
        assert record.event_name == "service.request.completed"
        assert record.service_operation == "POST /api/v1/projects/{project_id}/lifecycle-transitions"
        assert "private-owner-id" not in json.dumps(record.model_dump(mode="json"))
        assert record.attributes == {
            "method": "POST",
            "route": "/api/v1/projects/{project_id}/lifecycle-transitions",
            "status_class": "2xx",
        }
        rendered = metrics.render_prometheus()
        assert "P6I" not in rendered
        assert 'route="/api/v1/projects/{project_id}/lifecycle-transitions"' in rendered
        log = sink.getvalue()
        assert "private-owner-id" not in log
        assert '"project_id":null' in log


def test_wsgi_auth_instrumentation_never_serializes_authorization_header(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        projects = ProjectRegistry(store)
        projects.register(_project())
        sink = io.StringIO()
        metrics = ProductionMetricRegistry()
        observer = ProductionObservability(
            telemetry=TelemetryRecorder(store),
            logger=StructuredLogger(sink),
            metrics=metrics,
        )
        api = ServiceApiV1(projects, store, observability=observer)
        principal = ServicePrincipal(principal_id="owner", scopes=frozenset({READ_SCOPE}))
        app = WsgiServiceAppV1(
            api,
            StaticBearerAuthenticator({"super-secret-token": principal}),
            observer,
        )
        status_line = {}

        def start_response(status, headers):
            status_line["status"] = status

        body = app(
            {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/api/v1/projects/P6I",
                "HTTP_AUTHORIZATION": "Bearer super-secret-token",
                "CONTENT_LENGTH": "0",
                "wsgi.input": BytesIO(),
            },
            start_response,
        )
        assert status_line["status"].startswith("200 ")
        assert body
        raw = sink.getvalue()
        assert "super-secret-token" not in raw
        assert "Bearer" not in raw
        assert '"event_name":"auth.accepted"' in raw
        rendered = metrics.render_prometheus()
        assert 'ksupervisor_auth_attempts_total{result="accepted"} 1' in rendered


def test_side_effect_gateway_emits_policy_provider_and_repository_events_without_payload(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    providers = ProviderRegistry()
    providers.register(
        FakeProvider(
            ProviderDescriptor(
                provider_id="github.repository",
                version="1.0",
                provider_type="REPOSITORY",
                operations=("read_file",),
            ),
            response=ProviderResponse(payload={"found": True, "content": "PRIVATE_FILE_CONTENT"}),
        )
    )
    sink = io.StringIO()
    observer = ProductionObservability(
        telemetry=TelemetryRecorder(store),
        logger=StructuredLogger(sink),
        metrics=ProductionMetricRegistry(),
    )
    gateway = SideEffectGateway(store, engine, providers=providers, observability=observer)
    result = gateway.execute_provider(
        request(request_id="REQ_PHASE6_BOUNDARY", idempotency_key="phase6-boundary"),
        "github.repository",
        "read_file",
        {"path": "PRIVATE.md", "content": "SHOULD_NOT_BE_TELEMETRY"},
    )
    assert result.status.value == "SUCCEEDED"
    events = [item.event_name for item in store.list_telemetry_records("P11")]
    assert "policy.decision" in events
    assert "provider.call.started" in events
    assert "provider.call.completed" in events
    assert "repository.operation.started" in events
    assert "repository.operation.completed" in events
    serialized = json.dumps(
        [item.model_dump(mode="json") for item in store.list_telemetry_records("P11")],
        sort_keys=True,
    )
    assert "SHOULD_NOT_BE_TELEMETRY" not in serialized
    assert "PRIVATE_FILE_CONTENT" not in serialized
    assert "SHOULD_NOT_BE_TELEMETRY" not in sink.getvalue()
    store.close()
