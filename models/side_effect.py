from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import field_validator, model_validator

from .base import ContractModel, JsonObject, ensure_tz


class SideEffectExecutionStatus(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class SideEffectResult(ContractModel):
    execution_id: str
    project_id: str
    request_id: str
    status: SideEffectExecutionStatus
    component_kind: str
    component_id: str
    component_version: str | None = None
    operation: str
    output: JsonObject = {}
    metadata: JsonObject = {}
    error_code: str | None = None
    error_message: str | None = None
    policy_decision_id: str | None = None
    idempotent_replay: bool = False

    @model_validator(mode="after")
    def validate_error(self):
        if self.status in {SideEffectExecutionStatus.FAILED, SideEffectExecutionStatus.BLOCKED}:
            if not self.error_code or not self.error_message:
                raise ValueError("failed or blocked side-effect result requires normalized error")
        return self


class SideEffectExecutionRecord(ContractModel):
    execution_id: str
    project_id: str
    request_id: str
    agent_id: str
    capability_id: str
    capability_version: str
    component_kind: str
    component_id: str
    component_version: str | None = None
    operation: str
    idempotency_key: str | None = None
    signature: str
    status: SideEffectExecutionStatus
    output: JsonObject = {}
    metadata: JsonObject = {}
    error_code: str | None = None
    error_message: str | None = None
    policy_decision_id: str
    created_at: datetime
    completed_at: datetime | None = None

    @field_validator("created_at", "completed_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)

    @model_validator(mode="after")
    def validate_state(self):
        if self.status == SideEffectExecutionStatus.PENDING:
            if self.completed_at is not None:
                raise ValueError("pending side-effect execution cannot be completed")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("pending side-effect execution cannot contain an error")
        else:
            if self.completed_at is None:
                raise ValueError("completed side-effect execution requires completed_at")
        if self.status == SideEffectExecutionStatus.FAILED:
            if not self.error_code or not self.error_message:
                raise ValueError("failed side-effect execution requires normalized error")
        return self
