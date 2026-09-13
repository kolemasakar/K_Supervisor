from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.agent import AgentRunRequest
from models.capability import CapabilityDescriptor
from models.enums import ProjectLifecycleState, ProjectOperationalState, ProjectSpecStatus, ReleaseStatus
from models.intervention import NotificationEvent
from models.lifecycle import ProjectLifecycleTransition
from models.operational import ProjectOperationalTransition
from models.project import ProjectSpec
from models.release import Release


NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def make_spec(status=ProjectSpecStatus.DRAFT, approved_at=None):
    return ProjectSpec(
        project_spec_id="PS_1",
        project_id="PRJ_1",
        spec_version="1.0",
        status=status,
        created_at=NOW,
        updated_at=NOW,
        approved_at=approved_at,
        name="Example",
        short_name="example",
        purpose="Validate contracts",
        problem_statement="Need a durable project spec",
        project_type="AI_PROJECT",
        success_criteria=("valid",),
        first_working_criteria=("smoke test",),
        documentation={},
        repository={},
        architecture={},
        notifications={"owner_email": "owner@example.com"},
    )


def test_approved_project_spec_requires_timestamp():
    with pytest.raises(ValidationError):
        make_spec(ProjectSpecStatus.APPROVED)


def test_project_spec_roundtrip():
    spec = make_spec(ProjectSpecStatus.APPROVED, NOW)
    assert ProjectSpec.model_validate_json(spec.model_dump_json()) == spec


def test_invalid_lifecycle_transition_fails():
    with pytest.raises(ValidationError):
        ProjectLifecycleTransition(project_id="PRJ_1", from_state=ProjectLifecycleState.IDEA, to_state=ProjectLifecycleState.RELEASE_READY, reason="skip", trigger="test", timestamp=NOW)


def test_waiting_owner_is_operational_state():
    transition = ProjectOperationalTransition(project_id="PRJ_1", from_state=ProjectOperationalState.ACTIVE, to_state=ProjectOperationalState.WAITING_FOR_OWNER, timestamp=NOW)
    assert transition.to_state == ProjectOperationalState.WAITING_FOR_OWNER


def test_none_side_effect_is_exclusive():
    with pytest.raises(ValidationError):
        CapabilityDescriptor(capability_id="notify.email", capability_version="1.0", description="Notify", operations=("send",), input_schema="in", output_schema="out", side_effects=("NONE", "SEND_MESSAGE"))


def test_agent_request_has_project_and_capability_version():
    request = AgentRunRequest(request_id="REQ_1", project_id="PRJ_1", task_id="TASK_1", workflow_run_id="WF_1", run_id="RUN_1", agent_id="agent.default", capability_id="research.web", capability_version="1.0", operation="research", input={})
    assert request.project_id == "PRJ_1" and request.capability_version == "1.0"


def test_notification_defaults_to_email():
    event = NotificationEvent(notification_id="N_1", project_id="PRJ_1", event_type="INFO", title="Status", summary="Ready", created_at=NOW)
    assert event.channel.value == "EMAIL"


def test_published_release_requires_timestamp():
    with pytest.raises(ValidationError):
        Release(release_id="REL_1", project_id="PRJ_1", version="0.1.0", targets=("GPT_STORE",), status=ReleaseStatus.PUBLISHED, created_at=NOW, updated_at=NOW)
