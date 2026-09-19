from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from models.control import ServiceCommandRecord, ServiceCommandStatus
from models.enums import (
    HumanActionStatus,
    ProjectLifecycleState,
    ProjectOperationalState,
    ProjectSpecStatus,
    ReleaseStatus,
)
from models.intervention import HumanActionRequest
from models.project import Project
from models.task import Task, WorkflowRun
from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType
from policy.contracts import ApprovalRecord, ApprovalStatus, PermissionGrant
from release_manager import ReleaseManager
from service_api import (
    APPROVALS_DECIDE_SCOPE,
    EXECUTIONS_CANCEL_SCOPE,
    EXECUTIONS_READ_SCOPE,
    EXECUTIONS_START_SCOPE,
    HUMAN_ACTIONS_VERIFY_SCOPE,
    PROJECT_REGISTER_SCOPE,
    PROJECT_SPECS_ACTIVATE_SCOPE,
    PROJECT_SPECS_APPROVE_SCOPE,
    PROJECT_SPECS_READ_SCOPE,
    PROJECT_SPECS_SUBMIT_SCOPE,
    RECOVERY_READ_SCOPE,
    RELEASES_CONFIRM_SCOPE,
    RELEASES_READ_SCOPE,
    ServiceApiV1,
    TaskStartRequest,
)
from supervisor.task_state import TaskStatus
from tests.phase13_support import NOW as RELEASE_NOW, build_release_stack
from tests.v04_phase2_support import NOW, build_operator_stack, onboarding, principal


def registration_body(project_id="PNEW", *, secret_ref=None):
    return {
        "project_id": project_id,
        "spec_version": "0.1",
        "onboarding": onboarding(name=project_id, secret_ref=secret_ref),
    }


def task_body(value=7):
    return {
        "title": "operator task",
        "requirement": {
            "capability_id": "analysis.test",
            "version_constraint": "^1.0.0",
            "operation": "run",
        },
        "input": {"value": value},
    }


def approval_workflow_body():
    definition = WorkflowDefinition(
        workflow_id="operator.approval",
        workflow_version="1.0.0",
        start_node_id="gate",
        nodes=(
            WorkflowNode(
                node_id="gate",
                node_type=WorkflowNodeType.APPROVAL,
                approval_key="owner",
                approval_prompt="Approve continuation",
                approved_node_id="approved",
                rejected_node_id="rejected",
            ),
            WorkflowNode(node_id="approved", node_type=WorkflowNodeType.END),
            WorkflowNode(node_id="rejected", node_type=WorkflowNodeType.END),
        ),
    )
    return {
        "title": "operator workflow",
        "definition": definition.model_dump(mode="json"),
        "input": {"private_note": "not-for-status-projection"},
    }


def test_project_registration_is_fixed_state_and_restart_safe_idempotent(tmp_path):
    path = tmp_path / "state.db"
    store, projects, _, _, _, _, _, api = build_operator_stack(
        path,
        register_project=False,
    )
    body = registration_body()

    first = api.dispatch(
        "POST",
        "/api/v1/projects",
        principal=principal(PROJECT_REGISTER_SCOPE),
        body=body,
        idempotency_key="register-1",
    )
    assert first.status_code == 200
    assert first.body["data"]["project"]["lifecycle_state"] == "IDEA"
    assert first.body["data"]["project"]["operational_state"] == "ACTIVE"
    assert first.body["data"]["project_spec"]["status"] == "DRAFT"
    assert first.body["meta"]["idempotent_replay"] is False
    assert len(store.list_service_commands("PNEW")) == 1
    store.close()

    recovered, recovered_projects, _, _, _, _, _, recovered_api = build_operator_stack(
        path,
        register_project=False,
    )
    replay = recovered_api.dispatch(
        "POST",
        "/api/v1/projects",
        principal=principal(PROJECT_REGISTER_SCOPE),
        body=body,
        idempotency_key="register-1",
    )
    assert replay.status_code == 200
    assert replay.body["meta"]["idempotent_replay"] is True
    assert len(recovered_projects.list()) == 1
    assert len(recovered.list_project_specs("PNEW")) == 1
    assert len(recovered.list_service_commands("PNEW")) == 1
    recovered.close()


def test_registration_rejects_plaintext_secret_and_persists_safe_failed_command(tmp_path):
    store, projects, _, _, _, _, _, api = build_operator_stack(
        tmp_path / "state.db",
        register_project=False,
    )
    response = api.dispatch(
        "POST",
        "/api/v1/projects",
        principal=principal(PROJECT_REGISTER_SCOPE),
        body=registration_body("PRAW", secret_ref="plaintext-secret"),
        idempotency_key="raw-secret",
    )
    assert response.status_code == 400
    assert response.body["error"]["code"] == "INVALID_REQUEST"
    assert projects.get("PRAW") is None
    commands = store.list_service_commands("PRAW")
    assert len(commands) == 1
    assert commands[0].status == ServiceCommandStatus.FAILED
    serialized = commands[0].model_dump_json()
    assert "plaintext-secret" not in serialized
    assert "onboarding" not in serialized
    store.close()


def test_project_spec_submit_approve_activate_and_scope_denial(tmp_path):
    store, projects, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")

    denied = api.dispatch(
        "POST",
        "/api/v1/projects/P2/specs",
        principal=principal(PROJECT_SPECS_READ_SCOPE),
        body={"spec_version": "1.0", "onboarding": onboarding()},
        idempotency_key="denied-spec",
    )
    assert denied.status_code == 403
    assert store.list_project_specs("P2") == ()

    submitted = api.dispatch(
        "POST",
        "/api/v1/projects/P2/specs",
        principal=principal(PROJECT_SPECS_SUBMIT_SCOPE),
        body={"spec_version": "1.0", "onboarding": onboarding(secret_ref="secret://project/P2/repo")},
        idempotency_key="spec-1",
    )
    assert submitted.status_code == 200
    spec_id = submitted.body["data"]["project_spec"]["project_spec_id"]
    assert submitted.body["data"]["project_spec"]["status"] == "DRAFT"

    approved = api.dispatch(
        "POST",
        f"/api/v1/projects/P2/specs/{spec_id}/approve",
        principal=principal(PROJECT_SPECS_APPROVE_SCOPE),
        idempotency_key="approve-1",
    )
    assert approved.status_code == 200
    assert approved.body["data"]["project_spec"]["status"] == "APPROVED"
    persisted = store.get_project_spec(spec_id)
    assert persisted.status == ProjectSpecStatus.APPROVED
    assert persisted.repository["token"] == "secret://project/P2/repo"

    activated = api.dispatch(
        "POST",
        f"/api/v1/projects/P2/specs/{spec_id}/activate",
        principal=principal(PROJECT_SPECS_ACTIVATE_SCOPE),
        idempotency_key="activate-1",
    )
    assert activated.status_code == 200
    assert projects.get("P2").active_project_spec_id == spec_id
    events = [item.event_type for item in store.list_audit_events("P2")]
    assert "PROJECT_SPEC_APPROVED" in events
    assert "PROJECT_SPEC_ACTIVATED" in events
    store.close()


def test_project_spec_supersession_preserves_immutable_content_and_approval_evidence(tmp_path):
    store, projects, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    submitted = api.dispatch(
        "POST",
        "/api/v1/projects/P2/specs",
        principal=principal(PROJECT_SPECS_SUBMIT_SCOPE),
        body={"spec_version": "1.0", "onboarding": onboarding()},
        idempotency_key="supersede-spec",
    )
    spec_id = submitted.body["data"]["project_spec"]["project_spec_id"]
    api.dispatch(
        "POST",
        f"/api/v1/projects/P2/specs/{spec_id}/approve",
        principal=principal(PROJECT_SPECS_APPROVE_SCOPE),
        idempotency_key="supersede-approve",
    )
    approved = store.get_project_spec(spec_id)
    approved_at = approved.approved_at
    repository = dict(approved.repository)

    superseded = projects.transition_spec_status(
        "P2",
        spec_id,
        ProjectSpecStatus.SUPERSEDED,
        datetime.now(timezone.utc) + timedelta(seconds=1),
    )
    assert superseded.status == ProjectSpecStatus.SUPERSEDED
    assert superseded.approved_at == approved_at
    assert superseded.repository == repository
    store.close()


def test_project_spec_cross_project_identifier_fails_closed(tmp_path):
    store, projects, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    projects.register(
        Project(
            project_id="POTHER",
            name="other",
            lifecycle_state=ProjectLifecycleState.BUILDING,
            operational_state=ProjectOperationalState.ACTIVE,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    created = api.dispatch(
        "POST",
        "/api/v1/projects/POTHER/specs",
        principal=principal(PROJECT_SPECS_SUBMIT_SCOPE),
        body={"spec_version": "1.0", "onboarding": onboarding(name="other")},
        idempotency_key="other-spec",
    )
    spec_id = created.body["data"]["project_spec"]["project_spec_id"]

    wrong_project = api.dispatch(
        "POST",
        f"/api/v1/projects/P2/specs/{spec_id}/approve",
        principal=principal(PROJECT_SPECS_APPROVE_SCOPE),
        idempotency_key="cross-project",
    )
    assert wrong_project.status_code == 404
    assert store.get_project_spec(spec_id).status == ProjectSpecStatus.DRAFT
    store.close()


def test_human_action_and_policy_approval_use_authoritative_brokers(tmp_path):
    store, projects, _, _, _, human, approvals, api = build_operator_stack(tmp_path / "state.db")
    action = human.open(
        HumanActionRequest(
            human_action_id="H_PHASE2",
            project_id="P2",
            action_type="OWNER_CONFIRMATION",
            title="Confirm",
            summary="Confirm owner action",
            required_action="Confirm",
            blocking=True,
            created_at=NOW,
        )
    )
    assert action.status == HumanActionStatus.WAITING_FOR_OWNER
    assert projects.get("P2").operational_state == ProjectOperationalState.WAITING_FOR_OWNER

    verified = api.dispatch(
        "POST",
        "/api/v1/projects/P2/human-actions/H_PHASE2/verify",
        principal=principal(HUMAN_ACTIONS_VERIFY_SCOPE),
        idempotency_key="human-verify",
    )
    assert verified.status_code == 200
    assert verified.body["data"]["human_action"]["status"] == "VERIFIED"
    assert projects.get("P2").operational_state == ProjectOperationalState.ACTIVE

    pending = ApprovalRecord(
        approval_id="APP_PHASE2",
        project_id="P2",
        scope_hash="scope-phase2",
        requested_permissions=PermissionGrant(),
        created_at=NOW,
    )
    store.save_approval(pending)
    approved = api.dispatch(
        "POST",
        "/api/v1/projects/P2/approvals/APP_PHASE2/approve",
        principal=principal(APPROVALS_DECIDE_SCOPE),
        idempotency_key="approval-approve",
    )
    assert approved.status_code == 200
    assert store.get_approval("APP_PHASE2").status == ApprovalStatus.APPROVED

    revoked = api.dispatch(
        "POST",
        "/api/v1/projects/P2/approvals/APP_PHASE2/revoke",
        principal=principal(APPROVALS_DECIDE_SCOPE),
        body={"reason": "owner withdrew grant"},
        idempotency_key="approval-revoke",
    )
    assert revoked.status_code == 200
    assert store.get_approval("APP_PHASE2").status == ApprovalStatus.REVOKED
    store.close()


def test_task_start_replay_survives_restart_without_duplicate_task(tmp_path):
    path = tmp_path / "state.db"
    store, _, _, _, _, _, _, api = build_operator_stack(path)
    body = task_body()

    first = api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=body,
        idempotency_key="task-start-1",
    )
    assert first.status_code == 200
    assert first.body["data"]["task"]["status"] == "SUCCEEDED"
    task_id = first.body["data"]["task"]["task_id"]
    assert len(store.list_tasks("P2")) == 1
    assert len(store.list_service_commands("P2")) == 1
    store.close()

    recovered, _, _, _, _, _, _, recovered_api = build_operator_stack(path)
    replay = recovered_api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=body,
        idempotency_key="task-start-1",
    )
    assert replay.status_code == 200
    assert replay.body["meta"]["idempotent_replay"] is True
    assert replay.body["data"]["task"]["task_id"] == task_id
    assert len(recovered.list_tasks("P2")) == 1
    recovered.close()


def test_orphaned_pending_task_command_reconciles_without_duplicate_execution(tmp_path):
    store, _, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    body = task_body(9)
    canonical = TaskStartRequest.model_validate(body).model_dump(mode="json")
    command_id = api.operator._command_id("P2", "task-start", "orphan-task")
    task_id = api.operator._derived_id("TASK_SERVICE", command_id)
    workflow_run_id = api.operator._derived_id("WF_SERVICE", command_id)
    now = datetime.now(timezone.utc)
    store.claim_service_command(
        ServiceCommandRecord(
            command_id=command_id,
            project_id="P2",
            api_version="v1",
            operation="task-start",
            idempotency_key="orphan-task",
            signature=api.operator._signature(canonical),
            result_refs={"task_id": task_id, "workflow_run_id": workflow_run_id},
            created_at=now,
            updated_at=now,
        )
    )
    store.save_task(
        Task(
            task_id=task_id,
            project_id="P2",
            title="already durable",
            status=TaskStatus.SUCCEEDED.value,
            created_at=now,
            updated_at=now,
            metadata={"service_command_id": command_id},
        )
    )
    response = api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=body,
        idempotency_key="orphan-task",
    )
    assert response.status_code == 200
    assert response.body["meta"]["idempotent_replay"] is True
    assert len(store.list_tasks("P2")) == 1
    command = store.get_service_command(command_id)
    assert command.status == ServiceCommandStatus.SUCCEEDED
    store.close()


def test_task_cancel_uses_kernel_authority_and_updates_linked_workflow(tmp_path):
    store, _, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    task = Task(
        task_id="TASK_CANCEL",
        project_id="P2",
        title="cancel me",
        status=TaskStatus.RUNNING.value,
        created_at=NOW,
        updated_at=NOW,
        metadata={},
    )
    store.save_task(task)
    store.save_workflow_run(
        WorkflowRun(
            workflow_run_id="WF_CANCEL",
            project_id="P2",
            task_id=task.task_id,
            workflow_id="supervisor.single_capability",
            status="RUNNING",
            created_at=NOW,
            updated_at=NOW,
        )
    )

    response = api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks/TASK_CANCEL/cancel",
        principal=principal(EXECUTIONS_CANCEL_SCOPE),
        idempotency_key="task-cancel-1",
    )
    assert response.status_code == 200
    assert store.get_task("TASK_CANCEL").status == "CANCELLED"
    runs = [item for item in store.list_workflow_runs("P2") if item.workflow_run_id == "WF_CANCEL"]
    assert runs[0].status == "CANCELLED"
    store.close()


def test_workflow_waiting_for_owner_can_be_cancelled_without_exposing_context(tmp_path):
    store, projects, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    started = api.dispatch(
        "POST",
        "/api/v1/projects/P2/workflows",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=approval_workflow_body(),
        idempotency_key="workflow-start-1",
    )
    assert started.status_code == 200
    workflow = started.body["data"]["workflow"]
    assert workflow["status"] == "WAITING_FOR_APPROVAL"
    assert "context" not in workflow["metadata"]
    assert "not-for-status-projection" not in json.dumps(workflow)
    assert projects.get("P2").operational_state == ProjectOperationalState.WAITING_FOR_OWNER

    workflow_run_id = workflow["workflow_run_id"]
    cancelled = api.dispatch(
        "POST",
        f"/api/v1/projects/P2/workflows/{workflow_run_id}/cancel",
        principal=principal(EXECUTIONS_CANCEL_SCOPE),
        idempotency_key="workflow-cancel-1",
    )
    assert cancelled.status_code == 200
    assert cancelled.body["data"]["workflow"]["status"] == "CANCELLED"
    assert projects.get("P2").operational_state == ProjectOperationalState.ACTIVE
    actions = store.list_human_actions("P2")
    assert len(actions) == 1
    assert actions[0].status == HumanActionStatus.CANCELLED
    assert store.get_task(workflow["task_id"]).status == "CANCELLED"
    store.close()


def test_execution_read_scope_is_independent(tmp_path):
    store, _, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    denied = api.dispatch(
        "GET",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
    )
    assert denied.status_code == 403
    allowed = api.dispatch(
        "GET",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_READ_SCOPE),
    )
    assert allowed.status_code == 200
    store.close()


def test_recovery_status_is_explicit_redacted_projection(tmp_path):
    store, _, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    submitted = api.dispatch(
        "POST",
        "/api/v1/projects/P2/specs",
        principal=principal(PROJECT_SPECS_SUBMIT_SCOPE),
        body={
            "spec_version": "1.0",
            "onboarding": onboarding(secret_ref="secret://project/P2/repository"),
        },
        idempotency_key="recovery-spec",
    )
    assert submitted.status_code == 200

    response = api.dispatch(
        "GET",
        "/api/v1/projects/P2/recovery-status",
        principal=principal(RECOVERY_READ_SCOPE),
    )
    assert response.status_code == 200
    serialized = json.dumps(response.body, sort_keys=True)
    assert "secret://project/P2/repository" not in serialized
    assert "repository" not in response.body["data"]["recovery_status"]
    assert response.body["data"]["recovery_status"]["counts"]["project_specs"] == 1
    store.close()


def test_release_status_and_owner_publication_confirmation(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    manager = ReleaseManager(store, registry, repos, human)
    prepared = manager.handle_first_working(
        "P13",
        "0.2.0",
        repository,
        RELEASE_NOW,
        satisfied_criteria=("release tests pass",),
    )
    assert prepared.release.status == ReleaseStatus.PUBLICATION_REQUIRED

    api = ServiceApiV1(registry, store, human=human, releases=manager)
    read = api.dispatch(
        "GET",
        f"/api/v1/projects/P13/releases/{prepared.release.release_id}",
        principal=principal(RELEASES_READ_SCOPE),
    )
    assert read.status_code == 200
    assert read.body["data"]["release"]["release_targets"][0]["status"] == "PUBLICATION_REQUIRED"

    confirmed = api.dispatch(
        "POST",
        f"/api/v1/projects/P13/releases/{prepared.release.release_id}/targets/GPT_STORE/confirm-publication",
        principal=principal(RELEASES_CONFIRM_SCOPE),
        idempotency_key="publish-confirm-1",
    )
    assert confirmed.status_code == 200
    assert confirmed.body["data"]["release"]["status"] == "PUBLISHED"

    replay = api.dispatch(
        "POST",
        f"/api/v1/projects/P13/releases/{prepared.release.release_id}/targets/GPT_STORE/confirm-publication",
        principal=principal(RELEASES_CONFIRM_SCOPE),
        idempotency_key="publish-confirm-1",
    )
    assert replay.status_code == 200
    assert replay.body["meta"]["idempotent_replay"] is True
    store.close()


def test_direct_provider_and_secret_routes_are_not_exposed(tmp_path):
    store, _, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    for route in (
        "/api/v1/projects/P2/providers",
        "/api/v1/projects/P2/tools",
        "/api/v1/projects/P2/secrets",
    ):
        response = api.dispatch(
            "POST",
            route,
            principal=principal(EXECUTIONS_START_SCOPE),
            idempotency_key="no-direct-surface",
        )
        assert response.status_code == 404
        assert response.body["error"]["code"] == "NOT_FOUND"
    store.close()
