from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import field_validator, model_validator

from .agent import AgentRunResult
from .base import ContractModel, JsonObject, ensure_tz
from .project import Project


class RuntimeIdempotencyRecord(ContractModel):
    """Durable successful runtime result keyed by a semantic command scope."""

    record_id: str
    project_id: str
    scope: str
    signature: str
    result: AgentRunResult
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        return ensure_tz(value)


class ServiceMutationRecord(ContractModel):
    """Legacy durable completed Service/API mutation for restart-safe replay."""

    record_id: str
    project_id: str
    api_version: str
    operation: str
    idempotency_key: str
    signature: str
    result: Project
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: datetime) -> datetime:
        return ensure_tz(value)

    @model_validator(mode="after")
    def validate_project(self):
        if self.result.project_id != self.project_id:
            raise ValueError("service mutation result project_id mismatch")
        return self


class ServiceCommandStatus(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ServiceCommandRecord(ContractModel):
    """Generic durable Phase-2 command claim/result without persisting request bodies."""

    command_id: str
    project_id: str
    api_version: str
    operation: str
    idempotency_key: str
    signature: str
    status: ServiceCommandStatus = ServiceCommandStatus.PENDING
    result_kind: str | None = None
    result_refs: JsonObject = {}
    error_code: str | None = None
    error_category: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    @field_validator("created_at", "updated_at", "completed_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)

    @model_validator(mode="after")
    def validate_state(self):
        if self.updated_at < self.created_at:
            raise ValueError("service command updated_at precedes created_at")
        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("service command completed_at precedes created_at")
        if self.status == ServiceCommandStatus.PENDING:
            if self.completed_at is not None or self.error_code is not None:
                raise ValueError("pending service command cannot be completed")
        elif self.status == ServiceCommandStatus.SUCCEEDED:
            if self.completed_at is None:
                raise ValueError("successful service command requires completed_at")
            if self.error_code is not None or self.error_category is not None:
                raise ValueError("successful service command cannot contain an error")
        elif self.status == ServiceCommandStatus.FAILED:
            if self.completed_at is None or not self.error_code:
                raise ValueError("failed service command requires completion and error code")
        return self
