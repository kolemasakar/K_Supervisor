from datetime import datetime
from pydantic import field_validator
from .base import ContractModel, ensure_tz


class RoutingRecord(ContractModel):
    routing_record_id: str
    project_id: str
    task_id: str
    workflow_run_id: str
    capability_id: str
    version_constraint: str
    operation: str
    candidate_agent_ids: tuple[str, ...] = ()
    selected_agent_id: str | None = None
    selected_capability_version: str | None = None
    outcome: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)


class ReleaseValidationRecord(ContractModel):
    validation_record_id: str
    project_id: str
    release_id: str
    release_target_id: str
    target_type: str
    ready: bool
    passed_check_ids: tuple[str, ...] = ()
    failed_check_ids: tuple[str, ...] = ()
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)
