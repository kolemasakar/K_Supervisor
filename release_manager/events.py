from __future__ import annotations

from models.intervention import NotificationEvent
from persistence.base import PersistenceStore
from supervisor.notification import NotificationBroker


class ReleaseEventEmitter:
    def __init__(
        self,
        store: PersistenceStore,
        notification_broker: NotificationBroker | None = None,
    ):
        self.store = store
        self.notification_broker = notification_broker

    def first_working(self, release, spec) -> NotificationEvent:
        event = NotificationEvent(
            notification_id=f"NOTIFY_{release.release_id}_FIRST_WORKING",
            project_id=release.project_id,
            event_type="FIRST_WORKING_REACHED",
            severity="INFO",
            title="First working milestone reached",
            summary=f"Project reached FIRST_WORKING; release {release.version} preparation can begin.",
            created_at=release.created_at,
            metadata={"release_id": release.release_id},
        )
        self._emit(event, spec)
        return event

    def release_ready(self, release, spec, human_action_id: str | None) -> NotificationEvent:
        action_required = release.owner_publication_required
        event = NotificationEvent(
            notification_id=f"NOTIFY_{release.release_id}_RELEASE_READY",
            project_id=release.project_id,
            event_type="RELEASE_READY",
            severity="INFO",
            title="Release is ready for publication",
            summary=f"Release {release.version} passed automated preparation and readiness checks.",
            action_required=action_required,
            required_action=(
                "Review prepared release assets, publish using the owner account, and confirm publication."
                if action_required else None
            ),
            human_action_id=human_action_id,
            blocking=action_required,
            created_at=release.updated_at,
            metadata={"release_id": release.release_id, "targets": list(release.targets)},
        )
        self._emit(event, spec)
        return event

    def _emit(self, event: NotificationEvent, spec) -> None:
        recipient = spec.notifications.get("owner_email")
        if self.notification_broker is not None and recipient:
            self.notification_broker.deliver(event, str(recipient), now=event.created_at)
        else:
            self.store.save_notification(event)
