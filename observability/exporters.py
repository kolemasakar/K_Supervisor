from __future__ import annotations

from typing import Protocol

from .telemetry import redact


class TelemetryExporter(Protocol):
    def export(self, records): ...


class PrometheusProjectionExporter:
    def export(self, records):
        counters: dict[str, int] = {}
        for record in records:
            key = f"ksupervisor_{record.event_name.lower().replace('.', '_').replace('-', '_')}_total"
            counters[key] = counters.get(key, 0) + 1
        return tuple(sorted(counters.items()))


class OpenTelemetryProjectionExporter:
    def export(self, records):
        return tuple({
            "name": item.event_name,
            "timestamp": item.occurred_at.isoformat(),
            "trace_id": item.correlation_id,
            "attributes": redact({
                "project_id": item.project_id, "request_id": item.request_id,
                "task_id": item.task_id, "workflow_run_id": item.workflow_run_id,
                "run_id": item.run_id, "agent_id": item.agent_id,
                "capability_id": item.capability_id, "service_operation": item.service_operation,
                "status": item.status, **item.attributes,
            }),
        } for item in records)
