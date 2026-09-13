from datetime import datetime

from pydantic import field_validator, model_validator

from .base import ContractModel, ensure_tz
from .enums import NotificationChannel


class HumanActionRequest(ContractModel):
    human_action_id: str
    project_id: str
    status: str = "OPEN"
    action_type: str
    title: str
    summary: str
    required_action: str
    blocking: bool = True
    created_at: datetime
    due_at: datetime | None = None
    resolved_at: datetime | None = None
    resume_condition: str | None = None
    verification_method: str | None = None

    @field_validator("created_at", "due_at", "resolved_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)


class NotificationEvent(ContractModel):
    notification_id: str
    project_id: str
    channel: NotificationChannel = NotificationChannel.EMAIL
    event_type: str
    severity: str = "INFO"
    title: str
    summary: str
    action_required: bool = False
    required_action: str | None = None
    human_action_id: str | None = None
    blocking: bool = False
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)

    @model_validator(mode="after")
    def validate_action(self):
        if self.action_required and not self.required_action:
            raise ValueError("action_required notification requires required_action")
        return self
