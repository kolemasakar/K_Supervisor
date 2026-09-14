from datetime import datetime
from pydantic import field_validator
from .base import ContractModel, JsonObject, ensure_tz


class AuditEvent(ContractModel):
    audit_event_id: str
    project_id: str
    category: str
    event_type: str
    occurred_at: datetime
    resource_type: str
    resource_id: str
    severity: str = "INFO"
    correlation_id: str | None = None
    details: JsonObject = {}

    @field_validator("occurred_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)
