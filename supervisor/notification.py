from datetime import datetime, timezone

from models.enums import DeliveryStatus, NotificationChannel
from models.intervention import NotificationDeliveryAttempt, NotificationEvent
from persistence.base import PersistenceStore
from providers.email import EmailProvider, OutboundEmail


IMMEDIATE_EVENT_TYPES = {
    "ACTION_REQUIRED",
    "FIRST_WORKING_REACHED",
    "RELEASE_READY",
    "CRITICAL_FAILURE",
}


class NotificationDeliveryError(RuntimeError):
    pass


class NotificationBroker:
    def __init__(self, store: PersistenceStore, email_provider: EmailProvider):
        self.store = store
        self.email_provider = email_provider

    def should_deliver(self, event: NotificationEvent) -> bool:
        return event.action_required or event.event_type in IMMEDIATE_EVENT_TYPES or event.severity.upper() == "CRITICAL"

    def deliver(
        self,
        event: NotificationEvent,
        recipient: str,
        *,
        idempotency_key: str | None = None,
        now: datetime | None = None,
    ) -> NotificationDeliveryAttempt | None:
        if event.channel != NotificationChannel.EMAIL:
            raise ValueError("Phase 3 supports EMAIL notifications only")
        self.store.save_notification(event)
        if not self.should_deliver(event):
            return None

        key = idempotency_key or f"{event.notification_id}:EMAIL:{recipient}"
        prior = [
            item
            for item in self.store.list_notification_delivery_attempts(event.project_id)
            if item.idempotency_key == key
        ]
        sent = [item for item in prior if item.status == DeliveryStatus.SENT]
        if sent:
            return sent[-1]

        attempt_number = max((item.attempt_number for item in prior), default=0) + 1
        created_at = now or datetime.now(timezone.utc)
        attempt_id = f"{event.notification_id}:attempt:{attempt_number}"
        pending = NotificationDeliveryAttempt(
            delivery_attempt_id=attempt_id,
            notification_id=event.notification_id,
            project_id=event.project_id,
            idempotency_key=key,
            attempt_number=attempt_number,
            recipient=recipient,
            status=DeliveryStatus.PENDING,
            created_at=created_at,
        )
        self.store.append_notification_delivery_attempt(pending)

        message = OutboundEmail(recipient=recipient, subject=self._subject(event), body=self._body(event))
        try:
            provider_message_id = self.email_provider.send(message, key)
        except Exception as exc:
            failed = pending.model_copy(
                update={
                    "status": DeliveryStatus.FAILED,
                    "completed_at": datetime.now(timezone.utc),
                    "error_message": str(exc),
                }
            )
            self.store.append_notification_delivery_attempt(failed)
            raise NotificationDeliveryError(str(exc)) from exc

        completed = pending.model_copy(
            update={
                "status": DeliveryStatus.SENT,
                "completed_at": datetime.now(timezone.utc),
                "provider_message_id": provider_message_id,
            }
        )
        self.store.append_notification_delivery_attempt(completed)
        return completed

    @staticmethod
    def _subject(event: NotificationEvent) -> str:
        return f"[K_Supervisor][{event.severity}] {event.title}"

    @staticmethod
    def _body(event: NotificationEvent) -> str:
        lines = [
            f"Project: {event.project_id}",
            f"Event: {event.event_type}",
            f"Severity: {event.severity}",
            "",
            event.summary,
        ]
        if event.required_action:
            lines.extend(["", "Required action:", event.required_action])
        if event.human_action_id:
            lines.extend(["", f"Human action ID: {event.human_action_id}"])
        lines.extend(["", f"Blocking: {'YES' if event.blocking else 'NO'}"])
        return "\n".join(lines)
