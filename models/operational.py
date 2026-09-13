from datetime import datetime

from pydantic import field_validator, model_validator

from .base import ContractModel, ensure_tz
from .enums import ProjectOperationalState


ALLOWED = {
    "ACTIVE": {"PAUSED", "WAITING_FOR_OWNER", "WAITING_FOR_EXTERNAL", "BLOCKED", "DEGRADED", "FAILED"},
    "PAUSED": {"ACTIVE", "FAILED"},
    "WAITING_FOR_OWNER": {"ACTIVE", "FAILED"},
    "WAITING_FOR_EXTERNAL": {"ACTIVE", "FAILED"},
    "BLOCKED": {"ACTIVE", "FAILED"},
    "DEGRADED": {"ACTIVE", "FAILED"},
    "FAILED": {"ACTIVE", "PAUSED"},
}


class ProjectOperationalTransition(ContractModel):
    project_id: str
    from_state: ProjectOperationalState
    to_state: ProjectOperationalState
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        return ensure_tz(value)

    @model_validator(mode="after")
    def validate_transition(self):
        if self.to_state.value not in ALLOWED[self.from_state.value]:
            raise ValueError("invalid operational transition")
        return self
