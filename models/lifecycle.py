from datetime import datetime

from pydantic import field_validator, model_validator

from .base import ContractModel, ensure_tz
from .enums import ProjectLifecycleState


ALLOWED = {
    "IDEA": {"ONBOARDING", "TERMINATED"},
    "ONBOARDING": {"SPEC_REVIEW", "TERMINATED"},
    "SPEC_REVIEW": {"ONBOARDING", "APPROVED", "TERMINATED"},
    "APPROVED": {"PROVISIONING", "TERMINATED"},
    "PROVISIONING": {"BOOTSTRAPPED", "TERMINATED"},
    "BOOTSTRAPPED": {"BUILDING", "TERMINATED"},
    "BUILDING": {"VALIDATING", "MAINTENANCE", "TERMINATED"},
    "VALIDATING": {"BUILDING", "FIRST_WORKING", "TERMINATED"},
    "FIRST_WORKING": {"BUILDING", "RELEASE_PREPARATION", "MAINTENANCE", "TERMINATED"},
    "RELEASE_PREPARATION": {"BUILDING", "RELEASE_READY", "TERMINATED"},
    "RELEASE_READY": {"BUILDING", "MAINTENANCE", "TERMINATED"},
    "MAINTENANCE": {"BUILDING", "ARCHIVED", "TERMINATED"},
    "ARCHIVED": {"MAINTENANCE", "TERMINATED"},
    "TERMINATED": set(),
}


class ProjectLifecycleTransition(ContractModel):
    project_id: str
    from_state: ProjectLifecycleState
    to_state: ProjectLifecycleState
    reason: str
    trigger: str
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        return ensure_tz(value)

    @model_validator(mode="after")
    def validate_transition(self):
        if self.to_state.value not in ALLOWED[self.from_state.value]:
            raise ValueError("invalid lifecycle transition")
        return self
