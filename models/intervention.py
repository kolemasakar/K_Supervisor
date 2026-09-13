from datetime import datetime

from pydantic import Field, field_validator, model_validator

from .base import ContractModel, JsonObject, ensure_tz
from .enums import DeliveryStatus, HumanActionStatus, NotificationChannel


class HumanActionRequest(ContractModel):
    human_action_id: str
    project_id: str
    status: HumanActionStatus = HumanActionStatus.OPEN
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
    last_verification_error: str | None = None

    @field_validator("created_at", "due_at", "resolved_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)

    @model_validator(mode="after")
    def validate_state(self):
        if self.due_at is not None and self.due_at < self.created_at:
            raise ValueError("due_at must not precede created_at")
        terminal = {
            HumanActionStatus.VERIFIED,
            HumanActionStatus.CANCELLED,
            HumanActionStatus.FAILED,
        }
        if self.status == HumanActionStatus.VERIFIED and self.resolved_at is None:
            raise ValueError("verified human action requires resolved_at")
        if self.resolved_at is not None and self.status not in terminal:
            raise ValueError("resolved_at requires a terminal human action status")
        return self


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
    metadata: JsonObject = {}

    @field_validator("created_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)

    @model_validator(mode="after")
    def validate_action(self):
        if self.action_required and not self.required_action:
            raise ValueError("action_required notification requires required_action")
        return self


class NotificationDeliveryAttempt(ContractModel):
    delivery_attempt_id: str
    notification_id: str
    project_id: str
    idempotency_key: str
    attempt_number: int = Field(ge=1)
    channel: NotificationChannel = NotificationChannel.EMAIL
    recipient: str
    status: DeliveryStatus
    created_at: datetime
    completed_at: datetime | None = None
    provider_message_id: str | None = None
    error_message: str | None = None

    @field_validator("created_at", "completed_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)

    @model_validator(mode="after")
    def validate_delivery(self):
        if self.status == DeliveryStatus.PENDING and self.completed_at is not None:
            raise ValueError("pending delivery must not have completed_at")
        if self.status in {DeliveryStatus.SENT, DeliveryStatus.FAILED} and self.completed_at is None:
            raise ValueError("completed delivery attempt requires completed_at")
        if self.status == DeliveryStatus.FAILED and not self.error_message:
            raise ValueError("failed delivery attempt requires error_message")
        return self
