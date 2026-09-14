import pytest

from models.intervention import HumanActionRequest, NotificationEvent
from observability import AuditTimeline, DeterministicFailureInjector
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.notification import NotificationBroker, NotificationDeliveryError
from tests.phase12_support import build_reference_stack
from tests.phase15_support import LATER, NOW


class FailingEmailProvider:
    def __init__(self):
        self.injector = DeterministicFailureInjector((1,))

    def send(self, message, idempotency_key):
        self.injector.checkpoint("email failure")
        return "unused"


def test_intervention_and_notification_failure_are_auditable(tmp_path):
    store, _, _, _, _, _, kernel = build_reference_stack(tmp_path)
    human = HumanInterventionBroker(store, kernel.projects)
    action = human.open(HumanActionRequest(
        human_action_id="HA15",
        project_id="P12",
        action_type="TEST_APPROVAL",
        title="Approve test",
        summary="Phase 15 audit test",
        required_action="Approve",
        blocking=True,
        created_at=NOW,
    ))
    assert action.status.value == "WAITING_FOR_OWNER"

    broker = NotificationBroker(store, FailingEmailProvider())
    event = NotificationEvent(
        notification_id="N15",
        project_id="P12",
        event_type="ACTION_REQUIRED",
        severity="WARNING",
        title="Action required",
        summary="Owner action is required.",
        action_required=True,
        required_action="Approve",
        human_action_id=action.human_action_id,
        blocking=True,
        created_at=NOW,
    )
    with pytest.raises(NotificationDeliveryError):
        broker.deliver(event, "owner@example.test", now=NOW)

    human.verify(action.human_action_id, True, LATER)
    types = {item.event_type for item in AuditTimeline(store).events("P12")}
    assert "HUMAN_ACTION_OPENED" in types
    assert "HUMAN_ACTION_VERIFIED" in types
    assert "NOTIFICATION_DELIVERY_FAILED" in types
    assert store.list_notification_delivery_attempts("P12")[-1].status.value == "FAILED"
