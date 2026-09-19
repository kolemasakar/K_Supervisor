from __future__ import annotations

from datetime import datetime, timezone
from models.agent import AgentRunResult
from models.control import ServiceCommandRecord, ServiceCommandStatus
from models.enums import ExecutionStatus
from models.task import Task, WorkflowRun
from service_api import EXECUTIONS_START_SCOPE, TaskStartRequest
from supervisor.task_state import TaskStatus
from tests.v04_phase2_support import build_operator_stack, principal


def task_body():
    return {
        "title": "slow operator task",
        "requirement": {
            "capability_id": "analysis.test",
            "version_constraint": "^1.0.0",
            "operation": "run",
        },
        "input": {"value": 42},
    }


def test_active_replay_is_in_progress_and_cancel_wins_over_late_success(tmp_path):
    store, _, _, kernel, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    body = task_body()
    canonical = TaskStartRequest.model_validate(body).model_dump(mode="json")

    active_command_id = api.operator._command_id("P2", "task-start", "active-start")
    now = datetime.now(timezone.utc)
    store.claim_service_command(
        ServiceCommandRecord(
            command_id=active_command_id,
            project_id="P2",
            api_version="v1",
            operation="task-start",
            idempotency_key="active-start",
            signature=api.operator._signature(canonical),
            result_refs={
                "task_id": api.operator._derived_id("TASK_SERVICE", active_command_id),
                "workflow_run_id": api.operator._derived_id("WF_SERVICE", active_command_id),
            },
            created_at=now,
            updated_at=now,
        )
    )
    api.operator._mark_active(active_command_id)
    try:
        concurrent = api.dispatch(
            "POST",
            "/api/v1/projects/P2/tasks",
            principal=principal(EXECUTIONS_START_SCOPE),
            body=body,
            idempotency_key="active-start",
        )
    finally:
        api.operator._clear_active(active_command_id)
    assert concurrent.status_code == 409
    assert concurrent.body["error"]["code"] == "COMMAND_IN_PROGRESS"

    original_handler = kernel.dispatcher._handlers["agent.phase2"]

    def cancel_then_report_success(request):
        kernel.cancel_task(request.project_id, request.task_id)
        return original_handler(request)

    kernel.dispatcher.register("agent.phase2", cancel_then_report_success)
    response = api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=body,
        idempotency_key="cancel-during-dispatch",
    )
    assert response.status_code == 200
    task_id = response.body["data"]["task"]["task_id"]
    assert response.body["data"]["task"]["status"] == "CANCELLED"
    assert store.get_task(task_id).status == "CANCELLED"
    agent_runs = store.list_agent_runs("P2")
    assert len(agent_runs) == 1
    assert agent_runs[0].status == ExecutionStatus.CANCELLED
    store.close()


def test_recovered_pending_without_task_reacquires_single_process_execution_lease(tmp_path):
    store, _, _, kernel, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    body = task_body()
    canonical = TaskStartRequest.model_validate(body).model_dump(mode="json")
    command_id = api.operator._command_id("P2", "task-start", "restart-lease")
    task_id = api.operator._derived_id("TASK_SERVICE", command_id)
    workflow_run_id = api.operator._derived_id("WF_SERVICE", command_id)
    now = datetime.now(timezone.utc)

    store.claim_service_command(
        ServiceCommandRecord(
            command_id=command_id,
            project_id="P2",
            api_version="v1",
            operation="task-start",
            idempotency_key="restart-lease",
            signature=api.operator._signature(canonical),
            result_refs={"task_id": task_id, "workflow_run_id": workflow_run_id},
            created_at=now,
            updated_at=now,
        )
    )

    original_handler = kernel.dispatcher._handlers["agent.phase2"]
    nested = []

    def nested_replay(request):
        replay = api.dispatch(
            "POST",
            "/api/v1/projects/P2/tasks",
            principal=principal(EXECUTIONS_START_SCOPE),
            body=body,
            idempotency_key="restart-lease",
        )
        nested.append((replay.status_code, replay.body["error"]["code"]))
        return original_handler(request)

    kernel.dispatcher.register("agent.phase2", nested_replay)
    response = api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=body,
        idempotency_key="restart-lease",
    )

    assert response.status_code == 200
    assert response.body["data"]["task"]["status"] == "SUCCEEDED"
    assert nested == [(409, "COMMAND_IN_PROGRESS")]
    assert len(store.list_tasks("P2")) == 1
    assert store.get_service_command(command_id).status == ServiceCommandStatus.SUCCEEDED
    store.close()


def test_stale_pending_running_task_is_reconciled_after_restart_without_reexecution(tmp_path):
    store, _, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    body = task_body()
    canonical = TaskStartRequest.model_validate(body).model_dump(mode="json")
    command_id = api.operator._command_id("P2", "task-start", "stale-running")
    task_id = api.operator._derived_id("TASK_SERVICE", command_id)
    workflow_run_id = api.operator._derived_id("WF_SERVICE", command_id)
    now = datetime.now(timezone.utc)

    store.claim_service_command(
        ServiceCommandRecord(
            command_id=command_id,
            project_id="P2",
            api_version="v1",
            operation="task-start",
            idempotency_key="stale-running",
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
            title="interrupted",
            status=TaskStatus.RUNNING.value,
            created_at=now,
            updated_at=now,
            metadata={"service_command_id": command_id},
        )
    )
    store.save_workflow_run(
        WorkflowRun(
            workflow_run_id=workflow_run_id,
            project_id="P2",
            task_id=task_id,
            workflow_id="supervisor.single_capability",
            status="RUNNING",
            created_at=now,
            updated_at=now,
        )
    )
    store.close()

    recovered, _, _, _, _, _, _, recovered_api = build_operator_stack(tmp_path / "state.db")
    response = recovered_api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=body,
        idempotency_key="stale-running",
    )

    assert response.status_code == 409
    assert response.body["error"]["code"] == "EXECUTION_INTERRUPTED"
    assert recovered.get_task(task_id).status == "CANCELLED"
    runs = [
        item for item in recovered.list_workflow_runs("P2")
        if item.workflow_run_id == workflow_run_id
    ]
    assert runs[0].status == "CANCELLED"
    command = recovered.get_service_command(command_id)
    assert command.status == ServiceCommandStatus.FAILED
    assert command.error_code == "EXECUTION_INTERRUPTED"
    assert recovered.list_agent_runs("P2") == ()
    recovered.close()
