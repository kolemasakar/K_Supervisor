import io
import json
from datetime import datetime, timezone

import pytest

from observability import (
    BoundedExporterSupervisor,
    ExporterHealth,
    OTLPHTTPExporter,
    ProductionMetricRegistry,
    REDACTED,
    StructuredLogger,
    UnsafeTelemetryAttributeError,
    normalize_service_route,
    safe_production_attributes,
)

NOW = datetime(2026, 9, 22, 21, 0, tzinfo=timezone.utc)


def test_production_event_schema_rejects_unknown_fields_and_redacts_secret_markers():
    with pytest.raises(UnsafeTelemetryAttributeError):
        safe_production_attributes("unknown.event", {})
    with pytest.raises(UnsafeTelemetryAttributeError):
        safe_production_attributes(
            "service.request.completed",
            {"method": "GET", "request_body": {"secret": "bad"}},
        )
    safe = safe_production_attributes(
        "provider.call.failed",
        {
            "provider_type": "MODEL",
            "operation": "invoke",
            "result": "failed",
            "error_code": "Bearer canary-token",
        },
    )
    assert safe["error_code"] == REDACTED


def test_production_attributes_reject_nested_or_unbounded_content():
    with pytest.raises(UnsafeTelemetryAttributeError):
        safe_production_attributes(
            "policy.decision",
            {"decision": {"unsafe": "content"}, "operation": "execute"},
        )
    value = "x" * 500
    safe = safe_production_attributes(
        "policy.decision",
        {"decision": value, "operation": "execute"},
    )
    assert len(safe["decision"]) == 160


def test_structured_logger_is_deterministic_machine_readable_and_project_id_is_policy_controlled():
    sink = io.StringIO()
    logger = StructuredLogger(sink)
    assert logger.emit(
        event_name="service.request.completed",
        component="service_api",
        timestamp=NOW,
        status="200",
        duration_ms=12.5,
        correlation_id="REQ-1",
        request_id="REQ-1",
        project_id="P-PRIVATE",
        operation="GET /api/v1/projects/{project_id}",
        attributes={"method": "GET", "route": "/api/v1/projects/{project_id}", "status_class": "2xx"},
    )
    raw = sink.getvalue()
    payload = json.loads(raw)
    assert raw.endswith("\n")
    assert payload["timestamp"] == "2026-09-22T21:00:00Z"
    assert payload["event_name"] == "service.request.completed"
    assert payload["project_id"] is None
    assert "P-PRIVATE" not in raw


def test_structured_logger_redacts_secret_canaries_and_sink_failure_is_nonfatal():
    sink = io.StringIO()
    logger = StructuredLogger(sink)
    assert logger.emit(
        event_name="repository.operation.failed",
        component="repository",
        timestamp=NOW,
        error_code="authorization: Bearer forbidden",
        attributes={
            "provider": "GITHUB",
            "operation": "read_file",
            "result": "failed",
            "error_code": "secret://repo/token",
        },
    )
    assert "forbidden" not in sink.getvalue()
    assert "secret://repo/token" not in sink.getvalue()
    assert REDACTED in sink.getvalue()

    class BrokenSink:
        def write(self, _value):
            raise OSError("disk unavailable")

    assert StructuredLogger(BrokenSink()).emit(
        event_name="telemetry.export.failed",
        component="telemetry",
        timestamp=NOW,
        attributes={"exporter": "otlp_http", "result": "failed", "error_code": "IO"},
    ) is False


def test_service_route_normalization_removes_project_identifier():
    assert normalize_service_route("/api/v1/projects/P-SECRET/lifecycle-transitions?x=1") == (
        "/api/v1/projects/{project_id}/lifecycle-transitions"
    )


def test_production_metrics_use_only_frozen_families_and_bounded_labels():
    metrics = ProductionMetricRegistry()
    metrics.record_service_request(
        "GET",
        "/api/v1/projects/P-SECRET",
        200,
        250,
    )
    metrics.record_auth("accepted")
    metrics.record_repository("GITHUB", "read_file", "success")
    metrics.record_export("otlp_http", "success")
    metrics.record_export_drop("otlp_http", "queue_full")
    metrics.set_queue_depth("otlp_http", 2)
    rendered = metrics.render_prometheus()
    assert "P-SECRET" not in rendered
    assert 'route="/api/v1/projects/{project_id}"' in rendered
    assert "ksupervisor_service_request_duration_seconds_sum" in rendered
    assert "ksupervisor_repository_operations_total" in rendered
    assert "ksupervisor_telemetry_queue_depth" in rendered
    with pytest.raises(ValueError):
        metrics.record_repository("repo-user-controlled", "read_file", "success")


class _FailingExporter:
    def __init__(self):
        self.calls = 0

    def export(self, records, *, timeout_seconds):
        self.calls += 1
        assert timeout_seconds == 0.5
        raise TimeoutError("collector unavailable")


class _CollectingExporter:
    def __init__(self):
        self.batches = []

    def export(self, records, *, timeout_seconds):
        self.batches.append((tuple(records), timeout_seconds))


def test_bounded_exporter_queue_drop_and_retry_are_bounded_and_observable():
    metrics = ProductionMetricRegistry()
    exporter = _FailingExporter()
    supervisor = BoundedExporterSupervisor(
        "otlp_http",
        exporter,
        queue_size=2,
        batch_size=2,
        timeout_seconds=0.5,
        max_retries=1,
        metrics=metrics,
    )
    assert supervisor.enqueue("A") is True
    assert supervisor.enqueue("B") is True
    assert supervisor.enqueue("C") is False
    before = supervisor.snapshot()
    assert before.queued == 2
    assert before.dropped == 1
    assert before.health == ExporterHealth.DEGRADED

    after = supervisor.flush()
    assert exporter.calls == 2
    assert after.queued == 0
    assert after.exported == 0
    assert after.dropped == 3
    assert after.failures == 2
    assert after.health == ExporterHealth.UNAVAILABLE

    rendered = metrics.render_prometheus()
    assert 'reason="queue_full"' in rendered
    assert 'reason="export_failed"' in rendered
    assert 'result="failed"' in rendered


def test_bounded_exporter_success_and_nonflushing_shutdown():
    exporter = _CollectingExporter()
    supervisor = BoundedExporterSupervisor(
        "otlp_http",
        exporter,
        queue_size=3,
        batch_size=2,
        timeout_seconds=1.0,
        max_retries=0,
    )
    supervisor.enqueue("A")
    supervisor.enqueue("B")
    assert supervisor.flush().exported == 2
    assert exporter.batches == [(("A", "B"), 1.0)]
    supervisor.enqueue("C")
    snapshot = supervisor.shutdown(flush=False)
    assert snapshot.queued == 0
    assert snapshot.dropped == 1
    assert snapshot.health == ExporterHealth.DEGRADED


def test_otlp_http_adapter_uses_safe_projection_and_explicit_timeout():
    class Transport:
        def __init__(self):
            self.calls = []

        def send(self, projected_records, *, timeout_seconds):
            self.calls.append((projected_records, timeout_seconds))

    class Record:
        event_name = "provider.call.completed"
        occurred_at = NOW
        correlation_id = "REQ-1"
        project_id = "P1"
        request_id = "REQ-1"
        task_id = None
        workflow_run_id = None
        run_id = None
        agent_id = None
        capability_id = None
        service_operation = None
        status = "SUCCEEDED"
        attributes = {"authorization": "Bearer bad", "safe": "ok"}

    transport = Transport()
    OTLPHTTPExporter(transport).export((Record(),), timeout_seconds=0.75)
    projected, timeout = transport.calls[0]
    assert timeout == 0.75
    assert projected[0]["attributes"]["authorization"] == REDACTED
