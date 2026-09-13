from datetime import datetime, timezone

from models.enums import DeliveryStatus, ProjectLifecycleState, ProjectOperationalState
from models.intervention import HumanActionRequest, NotificationEvent
from models.project import Project
from persistence.sqlite_store import SQLitePersistenceStore
from providers.email import OutboundEmail
from providers.smtp_relay import SMTPRelayEmailProvider, SMTPRelaySettings
from registry.project_registry import ProjectRegistry
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.notification import NotificationBroker

NOW = datetime(2026, 9, 13, 14, 0, tzinfo=timezone.utc)


class FakeEmailProvider:
    def __init__(self):
        self.messages = []

    def send(self, message: OutboundEmail, idempotency_key: str) -> str:
        self.messages.append((message, idempotency_key))
        return f"message-{len(self.messages)}"


def make_project(project_id: str) -> Project:
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.BUILDING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def open_store(tmp_path):
    store = SQLitePersistenceStore(tmp_path / "state.sqlite3")
    store.initialize()
    return store


def test_blocking_human_action_waits_and_resumes_without_affecting_other_project(tmp_path):
    store = open_store(tmp_path)
    registry = ProjectRegistry(store)
    registry.register(make_project("project-a"))
    registry.register(make_project("project-b"))
    broker = HumanInterventionBroker(store, registry)
    action = HumanActionRequest(
        human_action_id="action-1",
        project_id="project-a",
        action_type="OWNER_CONFIGURATION",
        title="Owner action required",
        summary="A dependency requires owner input.",
        required_action="Complete the requested configuration.",
        blocking=True,
        created_at=NOW,
    )

    broker.open(action)
    assert registry.get("project-a").operational_state == ProjectOperationalState.WAITING_FOR_OWNER
    assert registry.get("project-b").operational_state == ProjectOperationalState.ACTIVE

    broker.verify("action-1", True, NOW)
    assert registry.get("project-a").operational_state == ProjectOperationalState.ACTIVE
    assert registry.get("project-b").operational_state == ProjectOperationalState.ACTIVE
    store.close()


def test_notification_duplicate_suppression_and_policy(tmp_path):
    store = open_store(tmp_path)
    provider = FakeEmailProvider()
    broker = NotificationBroker(store, provider)
    event = NotificationEvent(
        notification_id="notification-1",
        project_id="project-a",
        event_type="ACTION_REQUIRED",
        severity="HIGH",
        title="Action required",
        summary="Owner input is required.",
        action_required=True,
        required_action="Complete configuration.",
        human_action_id="action-1",
        blocking=True,
        created_at=NOW,
    )

    first = broker.deliver(event, "owner@example.com", idempotency_key="stable-key", now=NOW)
    second = broker.deliver(event, "owner@example.com", idempotency_key="stable-key", now=NOW)
    assert first is not None and first.status == DeliveryStatus.SENT
    assert second == first
    assert len(provider.messages) == 1

    info = NotificationEvent(
        notification_id="notification-info",
        project_id="project-a",
        event_type="TECHNICAL_PROGRESS",
        title="Progress",
        summary="Routine progress event.",
        created_at=NOW,
    )
    assert broker.deliver(info, "owner@example.com", now=NOW) is None
    assert len(provider.messages) == 1
    store.close()


def test_smtp_relay_provider(monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self, context):
            self.context = context

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr("providers.smtp_relay.smtplib.SMTP", FakeSMTP)
    provider = SMTPRelayEmailProvider(
        SMTPRelaySettings(
            host="smtp.example.com",
            sender_email="supervisor@example.com",
            use_starttls=True,
        )
    )
    message_id = provider.send(
        OutboundEmail("owner@example.com", "Subject", "Body"),
        "idempotency-1",
    )
    assert message_id
    assert len(sent) == 1
    assert sent[0]["X-K-Supervisor-Idempotency-Key"] == "idempotency-1"
