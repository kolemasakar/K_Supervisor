from __future__ import annotations

from datetime import datetime, timezone
from threading import Event, Thread

from models.agent import AgentRunResult
from models.control import ServiceCommandRecord, ServiceCommandStatus
from models.enums import ExecutionStatus
from models.task import Task, WorkflowRun
from service_api import EXECUTIONS_CANCEL_SCOPE, EXECUTIONS_START_SCOPE
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


def test_concurrent_replay_is_in_progress_and_cancel_wins_over_late_success(tmp_path):
    store, _, _, kernel, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    started = Event()
    release = Event()

    def slow_success(request):
        started.set()
        assert release.wait(timeout=5)
        return AgentRunResult(
            request_id=request.request_id,
            project_id=request.project_id,
            task_id=request.task_id,
            workflow_run_id=request.workflow_run_id,
            run_id=request.run_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            status=ExecutionStatus.SUCCEEDED,
            output={"late": True},
        )

    kernel.dispatcher.register("agent.phase2", slow_success)
    responses = []

    def invoke_start():
        responses.append(
            api.dispatch(
                "POST",
                "/api/v1/projects/P2/tasks",
                principal=principal(EXECUTIONS_START_SCOPE),
                body=task_body(),
                idempotency_key="slow-start",
            )
        )

    thread = Thread(target=invoke_start, daemon=True)
    thread.start()
    assert started.wait(timeout=5)

    concurrent = api.dispatch(
        "POST",
        "/api/v1/projects/P2/tasks",
        principal=principal(EXECUTIONS_START_SCOPE),
        body=task_body(),
        idempotency_key="slow-start",
    )
    assert concurrent.status_code == 409
    assert concurrent.body["error"]["code"] == "COMMAND_IN_PROGRESS"

    tasks = store.list_tasks("P2")
    assert len(tasks) == 1
    task_id = tasks[0].task_id

    cancelled = api.dispatch(
        "POST",
        f"/api/v1/projects/P2/tasks/{task_id}/cancel",
        principal=principal(EXECUTIONS_CANCEL_SCOPE),
        idempotency_key="cancel-slow",
    )
    assert cancelled.status_code == 200
    assert cancelled.body["data"]["task"]["status"] == "CANCELLED"

    release.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert len(responses) == 1
    assert responses[0].status_code == 200
    assert responses[0].body["data"]["task"]["status"] == "CANCELLED"
    assert store.get_task(task_id).status == "CANCELLED"
    agent_runs = store.list_agent_runs("P2")
    assert len(agent_runs) == 1
    assert agent_runs[0].status == ExecutionStatus.CANCELLED
    store.close()


def test_stale_pending_running_task_is_reconciled_after_restart_without_reexecution(tmp_path):
    store, _, _, _, _, _, _, api = build_operator_stack(tmp_path / "state.db")
    body = task_body()
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
            signature=api.operator._signature(body),
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
