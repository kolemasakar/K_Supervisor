from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import field_validator

from models.base import ContractModel, JsonObject, ensure_tz


class IntegrationKind(StrEnum):
    TOOL = "TOOL"
    PROVIDER = "PROVIDER"


class AvailabilityState(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class DependencyRequirement(ContractModel):
    kind: IntegrationKind
    component_id: str
    version_constraint: str = "*"
    required: bool = True


class AvailabilityReport(ContractModel):
    component_id: str
    state: AvailabilityState
    checked_at: datetime
    detail: str | None = None
    metadata: JsonObject = {}

    @field_validator("checked_at")
    @classmethod
    def validate_checked_at(cls, value: datetime) -> datetime:
        return ensure_tz(value)
