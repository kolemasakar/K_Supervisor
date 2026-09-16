from datetime import datetime
from pydantic import field_validator
from .base import ContractModel, JsonObject, ensure_tz


class TelemetryRecord(ContractModel):
    telemetry_id: str
    project_id: str
    event_name: str
    event_kind: str = "EVENT"
    occurred_at: datetime
    correlation_id: str | None = None
    request_id: str | None = None
    task_id: str | None = None
    workflow_run_id: str | None = None
    run_id: str | None = None
    agent_id: str | None = None
    capability_id: str | None = None
    service_operation: str | None = None
    status: str | None = None
    duration_ms: float | None = None
    attributes: JsonObject = {}

    @field_validator("occurred_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)
