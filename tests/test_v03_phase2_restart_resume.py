from models.enums import HumanActionStatus, ProjectOperationalState
from models.intervention import HumanActionRequest
from models.task import Task, WorkflowRun
from persistence import SQLitePersistenceStore
from policy.contracts import ApprovalStatus
from registry import ProjectRegistry
from supervisor.human_intervention import HumanInterventionBroker
from tests.phase11_support import LATER, NOW, build_policy_stack
from tests.test_v03_phase2_durable_control_state import make_policy_request, make_project


def test_interrupted_active_workflow_and_owner_wait_resume_after_restart(tmp_path):
    path = tmp_path / "state.db"
    store = SQLitePersistenceStore(path)
    store.initialize()
    projects = ProjectRegistry(store)
    projects.register(make_project("PRESUME"))
    store.save_task(
        Task(
            task_id="T-RESUME",
            project_id="PRESUME",
            title="durable task",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    store.save_workflow_run(
        WorkflowRun(
            workflow_run_id="WF-RESUME",
            project_id="PRESUME",
            task_id="T-RESUME",
            workflow_id="wf.resume",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    action = HumanInterventionBroker(store, projects).open(
        HumanActionRequest(
            human_action_id="H-RESUME",
            project_id="PRESUME",
            action_type="OWNER_CHECK",
            title="Owner check",
            summary="Waiting across restart",
            required_action="Confirm",
            blocking=True,
            created_at=NOW,
        )
    )
    assert projects.get("PRESUME").operational_state == ProjectOperationalState.WAITING_FOR_OWNER
    store.close()

    recovered = SQLitePersistenceStore(path)
    recovered.initialize()
    recovered_projects = ProjectRegistry(recovered)
    snapshot = recovered_projects.recover("PRESUME")
    assert snapshot.project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER
    assert [item.task_id for item in snapshot.tasks] == ["T-RESUME"]
    assert [item.workflow_run_id for item in snapshot.workflow_runs] == ["WF-RESUME"]
    assert snapshot.human_actions[0].status == HumanActionStatus.WAITING_FOR_OWNER

    verified = HumanInterventionBroker(recovered, recovered_projects).verify(
        action.human_action_id,
        True,
        LATER,
    )
    assert verified.status == HumanActionStatus.VERIFIED
    assert recovered_projects.get("PRESUME").operational_state == ProjectOperationalState.ACTIVE
    recovered.close()


def test_approval_expiry_and_revocation_are_durably_audited(tmp_path):
    expiry_store, _, _, _, expiry_broker, _, _, _ = build_policy_stack(
        tmp_path / "expiry",
        side_effects=("CREATE_RESOURCE",),
        risk_class="HIGH",
    )
    pending = expiry_broker.request(make_policy_request(), NOW, expires_at=LATER)
    expired = expiry_broker.expire(pending.approval_id, LATER)
    assert expired.status == ApprovalStatus.EXPIRED
    expiry_events = {item.event_type for item in expiry_store.list_audit_events("P11")}
    assert "APPROVAL_REQUESTED" in expiry_events
    assert "APPROVAL_EXPIRED" in expiry_events
    expiry_store.close()

    revoke_store, _, _, _, revoke_broker, _, _, _ = build_policy_stack(
        tmp_path / "revoke",
        side_effects=("CREATE_RESOURCE",),
        risk_class="HIGH",
    )
    pending = revoke_broker.request(make_policy_request(), NOW)
    approved = revoke_broker.approve(pending.approval_id, LATER)
    revoked = revoke_broker.revoke(
        approved.approval_id,
        LATER.replace(minute=LATER.minute + 1),
        reason="owner withdrew permission",
    )
    assert revoked.status == ApprovalStatus.REVOKED
    revoke_events = {item.event_type for item in revoke_store.list_audit_events("P11")}
    assert "APPROVAL_APPROVED" in revoke_events
    assert "APPROVAL_REVOKED" in revoke_events
    revoke_store.close()
