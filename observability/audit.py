from datetime import datetime
from uuid import uuid4
from models.audit import AuditEvent


def record_audit(store, *, project_id: str, category: str, event_type: str, occurred_at: datetime, resource_type: str, resource_id: str, severity: str = "INFO", correlation_id: str | None = None, details: dict | None = None) -> AuditEvent:
    event = AuditEvent(
        audit_event_id=f"AUDIT_{uuid4().hex}",
        project_id=project_id,
        category=category,
        event_type=event_type,
        occurred_at=occurred_at,
        resource_type=resource_type,
        resource_id=resource_id,
        severity=severity,
        correlation_id=correlation_id,
        details=details or {},
    )
    store.append_audit_event(event)
    return event
