from __future__ import annotations

from datetime import datetime

from pydantic import field_validator, model_validator

from .agent import AgentRunResult
from .base import ContractModel, ensure_tz
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
    """Durable completed Service/API mutation for restart-safe replay."""

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
