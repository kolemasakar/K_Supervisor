from datetime import datetime

from pydantic import field_validator

from .base import ContractModel, JsonObject, ensure_tz


class Task(ContractModel):
    task_id: str
    project_id: str
    title: str
    status: str = "NEW"
    created_at: datetime
    updated_at: datetime
    metadata: JsonObject = {}

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)


class WorkflowRun(ContractModel):
    workflow_run_id: str
    project_id: str
    task_id: str
    workflow_id: str
    status: str = "PENDING"
    created_at: datetime
    updated_at: datetime
    metadata: JsonObject = {}

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)
