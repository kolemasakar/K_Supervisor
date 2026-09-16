from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from models.telemetry import TelemetryRecord

REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "authorization", "cookie", "credentials", "credential", "password",
    "secret", "secret_ref", "token", "access_token", "refresh_token", "api_key",
}


def redact(value: Any, *, key: str | None = None) -> Any:
    if key is not None and key.lower() in _SENSITIVE_KEYS:
        return REDACTED
    if isinstance(value, str):
        return REDACTED if value.startswith("secret://") else value
    if isinstance(value, dict):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class TelemetryRecorder:
    def __init__(self, store):
        self.store = store

    def record(
        self,
        *,
        project_id: str,
        event_name: str,
        event_kind: str = "EVENT",
        occurred_at: datetime | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        task_id: str | None = None,
        workflow_run_id: str | None = None,
        run_id: str | None = None,
        agent_id: str | None = None,
        capability_id: str | None = None,
        service_operation: str | None = None,
        status: str | None = None,
        duration_ms: float | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TelemetryRecord:
        at = occurred_at or datetime.now(timezone.utc)
        safe_attributes = redact(attributes or {})
        basis = json.dumps({
            "project_id": project_id, "event_name": event_name, "event_kind": event_kind,
            "occurred_at": at.isoformat(), "correlation_id": correlation_id,
            "request_id": request_id, "task_id": task_id, "workflow_run_id": workflow_run_id,
            "run_id": run_id, "agent_id": agent_id, "capability_id": capability_id,
            "service_operation": service_operation, "status": status, "attributes": safe_attributes,
        }, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        record = TelemetryRecord(
            telemetry_id="TELEMETRY_" + hashlib.sha256(basis).hexdigest(),
            project_id=project_id, event_name=event_name, event_kind=event_kind, occurred_at=at,
            correlation_id=correlation_id, request_id=request_id, task_id=task_id,
            workflow_run_id=workflow_run_id, run_id=run_id, agent_id=agent_id,
            capability_id=capability_id, service_operation=service_operation, status=status,
            duration_ms=duration_ms, attributes=safe_attributes,
        )
        self.store.append_telemetry_record(record)
        return record


class TelemetryTimeline:
    def __init__(self, store):
        self.store = store

    def events(self, project_id: str) -> tuple[TelemetryRecord, ...]:
        return tuple(sorted(self.store.list_telemetry_records(project_id), key=lambda item: (item.occurred_at, item.telemetry_id)))
