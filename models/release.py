from datetime import datetime

from pydantic import field_validator, model_validator

from .base import ContractModel, ensure_tz
from .enums import ReleaseStatus


class Release(ContractModel):
    release_id: str
    project_id: str
    version: str
    targets: tuple[str, ...]
    status: ReleaseStatus = ReleaseStatus.DRAFT
    readiness_criteria: tuple[str, ...] = ()
    owner_publication_required: bool = True
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    @field_validator("created_at", "updated_at", "published_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)

    @model_validator(mode="after")
    def validate_release(self):
        if self.status == ReleaseStatus.PUBLISHED and self.published_at is None:
            raise ValueError("published release requires published_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        return self


class ReleaseTarget(ContractModel):
    release_target_id: str
    release_id: str
    project_id: str
    target_type: str
    status: ReleaseStatus = ReleaseStatus.DRAFT
    readiness_criteria: tuple[str, ...] = ()
    checklist: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    owner_publication_required: bool = True
    human_action_id: str | None = None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    @field_validator("created_at", "updated_at", "published_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)

    @model_validator(mode="after")
    def validate_target(self):
        if self.status == ReleaseStatus.PUBLISHED and self.published_at is None:
            raise ValueError("published release target requires published_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        if not self.target_type.strip():
            raise ValueError("target_type must not be empty")
        return self
