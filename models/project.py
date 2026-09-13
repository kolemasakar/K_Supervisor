from __future__ import annotations

from datetime import datetime

from pydantic import field_validator, model_validator

from .base import ContractModel, JsonObject, ensure_tz
from .enums import ProjectLifecycleState, ProjectOperationalState, ProjectSpecStatus


class ProjectSpec(ContractModel):
    project_spec_id: str
    project_id: str
    spec_version: str
    status: ProjectSpecStatus
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None = None
    supersedes_spec_id: str | None = None
    name: str
    short_name: str
    purpose: str
    problem_statement: str
    project_type: str
    success_criteria: tuple[str, ...]
    first_working_criteria: tuple[str, ...]
    documentation: JsonObject
    repository: JsonObject
    architecture: JsonObject
    integrations: JsonObject = {}
    agents: JsonObject = {}
    autonomy: JsonObject = {}
    notifications: JsonObject
    parallel_execution: JsonObject = {}
    release: JsonObject = {}
    risk: JsonObject = {}

    @field_validator("created_at", "updated_at", "approved_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)

    @model_validator(mode="after")
    def validate_approval(self) -> "ProjectSpec":
        if self.status == ProjectSpecStatus.APPROVED and self.approved_at is None:
            raise ValueError("approved ProjectSpec requires approved_at")
        if self.status != ProjectSpecStatus.APPROVED and self.approved_at is not None:
            raise ValueError("only approved ProjectSpec may contain approved_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        return self


class Project(ContractModel):
    project_id: str
    name: str
    active_project_spec_id: str | None = None
    lifecycle_state: ProjectLifecycleState
    operational_state: ProjectOperationalState
    current_roadmap_phase: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)
