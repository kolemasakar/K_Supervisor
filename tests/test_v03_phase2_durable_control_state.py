from datetime import timedelta

import pytest

from models.agent import AgentRunRequest
from models.enums import (
    DeliveryStatus,
    ExecutionStatus,
    HumanActionStatus,
    ProjectLifecycleState,
    ProjectOperationalState,
)
from models.intervention import HumanActionRequest, NotificationEvent
from models.observability_records import RoutingRecord, ReleaseValidationRecord
from models.project import Project
from persistence import SQLitePersistenceStore
from policy.contracts import (
    ApprovalRecord,
    ApprovalStatus,
    PermissionGrant,
    PolicyDecision,
    PolicyEffect,
    RiskClass,
)
from registry import ProjectRegistry
from runtime import AgentRuntimeDispatcher
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.notification import NotificationBroker
from tests.phase8_support import build_runtime, make_request, success
from tests.phase11_support import LATER, NOW, build_policy_stack


class CountingEmailProvider:
    def __init__(self):
        self.calls = []

    def send(self, message, idempotency_key):
        self.calls.append((message, idempotency_key))
        return f"MSG-{len(self.calls)}"


class FailingAuditStore(SQLitePersistenceStore):
    def _audit(self, value):
        raise RuntimeError("forced audit failure")


def make_project(project_id="PCTRL"):
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.IDEA,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def make_policy_request(*, request_id="REQ-P2", run_id="RUN-P2", policy=None):
    return AgentRunRequest(
        request_id=request_id,
        project_id="P11",
        task_id="T-P2",
        workflow_run_id="WF-P2",
        run_id=run_id,
        agent_id="agent.policy",
        capability_id="policy.test",
        capability_version="1.0.0",
        operation="run",
        input={"value": 1},
        policy=policy or {},
    )


def durable_runtime(store, calls):
    agents, adapter, _ = build_runtime()

    def handler(request, control):
        calls.append(request.project_id)
        return success(request, {"call": len(calls)})

    adapter.register("A1", handler)
    return AgentRuntimeDispatcher(agents, adapter, persistence_store=store)


def test_runtime_idempotency_replays_after_store_restart(tmp_path):
    path = tmp_path / "state.db"
    calls = []

    store = SQLitePersistenceStore(path)
    store.initialize()
    runtime = durable_runtime(store, calls)
    first = runtime.dispatch(make_request(key="DURABLE", request_id="REQ1", run_id="RUN1"))
    assert first.status == ExecutionStatus.SUCCEEDED
    assert calls == ["P1"]
    assert len(store.list_runtime_idempotency("P1")) == 1
    store.close()

    recovered = SQLitePersistenceStore(path)
    recovered.initialize()
    runtime = durable_runtime(recovered, calls)
    replay = runtime.dispatch(make_request(key="DURABLE", request_id="REQ2", run_id="RUN2"))

    assert replay.status == ExecutionStatus.SUCCEEDED
    assert replay.request_id == "REQ2"
    assert replay.run_id == "RUN2"
    assert replay.output == {"call": 1}
    assert replay.metadata["idempotent_replay"] is True
    assert calls == ["P1"]
    recovered.close()


def test_runtime_idempotency_scope_isolated_by_project(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        calls = []
        runtime = durable_runtime(store, calls)
        first = make_request(key="SAME", request_id="REQ1", run_id="RUN1")
        second = first.model_copy(
            update={"project_id": "P2", "request_id": "REQ2", "run_id": "RUN2"}
        )

        assert runtime.dispatch(first).status == ExecutionStatus.SUCCEEDED
        assert runtime.dispatch(second).status == ExecutionStatus.SUCCEEDED
        assert calls == ["P1", "P2"]
        assert len(store.list_runtime_idempotency("P1")) == 1
        assert len(store.list_runtime_idempotency("P2")) == 1


def test_pending_approval_expires_and_same_scope_can_be_requested_again(tmp_path):
    store, projects, _, _, approval, _, _, _ = build_policy_stack(
        tmp_path,
        side_effects=("CREATE_RESOURCE",),
        risk_class="HIGH",
    )
    request = make_policy_request()
    original = approval.request(request, NOW, expires_at=LATER)

    expired = approval.expire(original.approval_id, LATER)
    assert expired.status == ApprovalStatus.EXPIRED
    assert expired.expired_at == LATER
    assert store.get_human_action(original.human_action_id).status == HumanActionStatus.CANCELLED
    assert projects.get("P11").operational_state == ProjectOperationalState.ACTIVE

    renewed = approval.request(request, LATER + timedelta(minutes=1))
    assert renewed.approval_id != original.approval_id
    assert renewed.status == ApprovalStatus.PENDING
    store.close()


def test_revoked_approval_no_longer_authorizes_policy(tmp_path):
    store, _, _, _, approval, engine, _, _ = build_policy_stack(
        tmp_path,
        side_effects=("CREATE_RESOURCE",),
        risk_class="HIGH",
    )
    request = make_policy_request()
    pending = approval.request(request, NOW)
    approved = approval.approve(pending.approval_id, LATER)
    assert approved.status == ApprovalStatus.APPROVED

    revoked_at = LATER + timedelta(minutes=1)
    revoked = approval.revoke(
        approved.approval_id,
        revoked_at,
        reason="owner withdrew permission",
    )
    assert revoked.status == ApprovalStatus.REVOKED
    assert revoked.revoked_at == revoked_at

    decision = engine.evaluate(
        make_policy_request(
            request_id="REQ-REVOKED",
            run_id="RUN-REVOKED",
            policy={"approval_id": approved.approval_id},
        )
    )
    assert decision.effect == PolicyEffect.REQUIRE_APPROVAL
    assert decision.reason_code == "APPROVAL_REVOKED"
    store.close()


def test_recovery_aggregate_and_notification_dedup_survive_restart(tmp_path):
    path = tmp_path / "state.db"
    store = SQLitePersistenceStore(path)
    store.initialize()
    projects = ProjectRegistry(store)
    projects.register(make_project())

    human = HumanInterventionBroker(store, projects)
    action = human.open(
        HumanActionRequest(
            human_action_id="H-P2",
            project_id="PCTRL",
            action_type="CHECK",
            title="Check",
            summary="Check durable state",
            required_action="Review",
            blocking=False,
            created_at=NOW,
        )
    )

    provider = CountingEmailProvider()
    broker = NotificationBroker(store, provider)
    event = NotificationEvent(
        notification_id="N-P2",
        project_id="PCTRL",
        event_type="ACTION_REQUIRED",
        severity="WARNING",
        title="Owner action",
        summary="Review control state",
        action_required=True,
        required_action="Review",
        human_action_id=action.human_action_id,
        created_at=NOW,
    )
    sent = broker.deliver(event, "owner@example.test", idempotency_key="CONTROL-NOTIFY", now=NOW)
    assert sent.status == DeliveryStatus.SENT
    assert len(provider.calls) == 1

    approval = ApprovalRecord(
        approval_id="APP-P2",
        project_id="PCTRL",
        scope_hash="scope-p2",
        requested_permissions=PermissionGrant(),
        created_at=NOW,
    )
    store.save_approval(approval)

    calls = []
    runtime = durable_runtime(store, calls)
    runtime_request = make_request(key="CTRL", request_id="REQ-C1", run_id="RUN-C1").model_copy(
        update={"project_id": "PCTRL"}
    )
    assert runtime.dispatch(runtime_request).status == ExecutionStatus.SUCCEEDED

    store.append_policy_decision(
        PolicyDecision(
            decision_id="POL-P2",
            project_id="PCTRL",
            request_id="REQ-C1",
            effect=PolicyEffect.ALLOW,
            reason_code="TEST",
            reason="durable control state",
            risk_class=RiskClass.LOW,
            evaluated_at=NOW,
        )
    )
    store.append_routing_record(
        RoutingRecord(
            routing_record_id="ROUTE-P2",
            project_id="PCTRL",
            task_id="T-P2",
            workflow_run_id="WF-P2",
            capability_id="analysis.test",
            version_constraint="1.0.0",
            operation="run",
            candidate_agent_ids=("A1",),
            selected_agent_id="A1",
            selected_capability_version="1.0.0",
            outcome="SELECTED",
            created_at=NOW,
        )
    )
    store.append_release_validation_record(
        ReleaseValidationRecord(
            validation_record_id="VALID-P2",
            project_id="PCTRL",
            release_id="REL-P2",
            release_target_id="TARGET-P2",
            target_type="TEST",
            ready=True,
            passed_check_ids=("control-state",),
            created_at=NOW,
        )
    )
    store.close()

    recovered = SQLitePersistenceStore(path)
    recovered.initialize()
    snapshot = ProjectRegistry(recovered).recover("PCTRL")
    assert [item.human_action_id for item in snapshot.human_actions] == ["H-P2"]
    assert [item.notification_id for item in snapshot.notifications] == ["N-P2"]
    assert len(snapshot.notification_delivery_attempts) == 2
    assert [item.approval_id for item in snapshot.approvals] == ["APP-P2"]
    assert len(snapshot.runtime_idempotency) == 1
    assert [item.decision_id for item in snapshot.policy_decisions] == ["POL-P2"]
    assert snapshot.audit_events
    assert [item.routing_record_id for item in snapshot.routing_records] == ["ROUTE-P2"]
    assert [item.validation_record_id for item in snapshot.release_validation_records] == ["VALID-P2"]

    provider_after_restart = CountingEmailProvider()
    replay_broker = NotificationBroker(recovered, provider_after_restart)
    duplicate = replay_broker.deliver(
        event,
        "owner@example.test",
        idempotency_key="CONTROL-NOTIFY",
        now=LATER,
    )
    assert duplicate.status == DeliveryStatus.SENT
    assert provider_after_restart.calls == []
    recovered.close()


def test_authoritative_project_transition_and_audit_roll_back_together(tmp_path):
    store = FailingAuditStore(tmp_path / "state.db")
    store.initialize()
    registry = ProjectRegistry(store)
    registry.register(make_project("PATOMIC"))

    with pytest.raises(RuntimeError, match="forced audit failure"):
        registry.transition_lifecycle(
            "PATOMIC",
            ProjectLifecycleState.ONBOARDING,
            "begin",
            "test",
            LATER,
        )

    assert registry.get("PATOMIC").lifecycle_state == ProjectLifecycleState.IDEA
    assert store.list_lifecycle_transitions("PATOMIC") == ()
    assert store.list_audit_events("PATOMIC") == ()
    store.close()
