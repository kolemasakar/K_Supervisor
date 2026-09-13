from __future__ import annotations

from datetime import datetime, timezone

from models.enums import ExecutionStatus, ProjectOperationalState
from models.task import Task, WorkflowRun
from models.workflow import WorkflowDefinition, WorkflowNodeType
from persistence.base import PersistenceStore
from supervisor.kernel import ProjectNotRunnableError, SupervisorKernel
from supervisor.task_state import TaskStatus, transition_task

from .approval import ApprovalRequester
from .contracts import WorkflowExecutionResult, WorkflowExecutionStatus


class WorkflowRuntimeError(RuntimeError):
    pass


class WorkflowEngine:
    def __init__(
        self,
        kernel: SupervisorKernel,
        store: PersistenceStore,
        approval_requester: ApprovalRequester | None = None,
    ):
        self.kernel = kernel
        self.store = store
        self.approval_requester = approval_requester

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _require_active_project(self, project_id: str) -> None:
        project = self.kernel.projects.get(project_id)
        if project is None:
            raise KeyError(project_id)
        if project.operational_state != ProjectOperationalState.ACTIVE:
            raise ProjectNotRunnableError(
                f"project is not ACTIVE: {project_id} ({project.operational_state})"
            )

    def start(
        self,
        project_id: str,
        title: str,
        definition: WorkflowDefinition,
        input_data: dict,
        *,
        approvals: dict[str, bool] | None = None,
    ) -> WorkflowExecutionResult:
        self._require_active_project(project_id)
        now = self._now()
        task = Task(
            task_id=self.kernel.ids.new("TASK"),
            project_id=project_id,
            title=title,
            status=TaskStatus.NEW.value,
            created_at=now,
            updated_at=now,
            metadata={"workflow_id": definition.workflow_id},
        )
        self.store.save_task(task)
        task = transition_task(task, TaskStatus.ROUTING, self._now())
        self.store.save_task(task)
        task = transition_task(task, TaskStatus.RUNNING, self._now())
        self.store.save_task(task)

        context = {"__input__": input_data}
        run = WorkflowRun(
            workflow_run_id=self.kernel.ids.new("WF"),
            project_id=project_id,
            task_id=task.task_id,
            workflow_id=definition.workflow_id,
            status=WorkflowExecutionStatus.RUNNING.value,
            created_at=now,
            updated_at=now,
            metadata=self._metadata(
                definition,
                definition.start_node_id,
                context,
                {},
                0,
            ),
        )
        self.store.save_workflow_run(run)
        return self._drive(task, run, definition, approvals or {})

    def resume(
        self,
        project_id: str,
        workflow_run_id: str,
        definition: WorkflowDefinition,
        *,
        approvals: dict[str, bool] | None = None,
    ) -> WorkflowExecutionResult:
        self._require_active_project(project_id)
        run = self._find_run(project_id, workflow_run_id)
        if run.workflow_id != definition.workflow_id:
            raise WorkflowRuntimeError("workflow definition does not match persisted run")
        if run.metadata.get("workflow_version") != definition.workflow_version:
            raise WorkflowRuntimeError("workflow version does not match persisted run")
        task = self.store.get_task(run.task_id)
        if task is None:
            raise WorkflowRuntimeError("workflow parent task is missing")
        if run.status in {
            WorkflowExecutionStatus.SUCCEEDED.value,
            WorkflowExecutionStatus.FAILED.value,
        }:
            return self._result_from_run(run)
        return self._drive(task, run, definition, approvals or {})

    def _drive(
        self,
        task: Task,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        approvals: dict[str, bool],
    ) -> WorkflowExecutionResult:
        context = dict(run.metadata.get("context", {}))
        visits = {str(k): int(v) for k, v in dict(run.metadata.get("visits", {})).items()}
        steps = int(run.metadata.get("steps", 0))
        current = str(run.metadata.get("current_node_id", definition.start_node_id))

        while True:
            node = definition.node(current)
            resuming_gate = (
                run.status == WorkflowExecutionStatus.WAITING_FOR_APPROVAL.value
                and node.node_type == WorkflowNodeType.APPROVAL
            )
            if not resuming_gate:
                if steps >= definition.max_steps:
                    return self._fail(
                        task,
                        run,
                        definition,
                        current,
                        context,
                        visits,
                        steps,
                        "workflow max_steps exceeded",
                    )
                visits[current] = visits.get(current, 0) + 1
                if visits[current] > node.max_visits:
                    return self._fail(
                        task,
                        run,
                        definition,
                        current,
                        context,
                        visits,
                        steps,
                        f"node max_visits exceeded: {current}",
                    )
                steps += 1

            if node.node_type == WorkflowNodeType.END:
                completed = run.model_copy(
                    update={
                        "status": WorkflowExecutionStatus.SUCCEEDED.value,
                        "updated_at": self._now(),
                        "metadata": self._metadata(definition, current, context, visits, steps),
                    }
                )
                self.store.save_workflow_run(completed)
                if task.status == TaskStatus.RUNNING.value:
                    task = transition_task(task, TaskStatus.SUCCEEDED, self._now())
                    self.store.save_task(task)
                return WorkflowExecutionResult(
                    workflow_run_id=completed.workflow_run_id,
                    task_id=task.task_id,
                    status=WorkflowExecutionStatus.SUCCEEDED,
                    current_node_id=current,
                    context=context,
                )

            if node.node_type == WorkflowNodeType.CAPABILITY:
                value = self._resolve_path(context, node.input_key)
                if not isinstance(value, dict):
                    return self._fail(
                        task,
                        run,
                        definition,
                        current,
                        context,
                        visits,
                        steps,
                        f"capability input is not an object: {node.input_key}",
                    )
                try:
                    result = self.kernel.run_task(
                        task.project_id,
                        f"{definition.workflow_id}:{node.node_id}",
                        node.requirement,
                        value,
                        metadata={
                            "parent_task_id": task.task_id,
                            "parent_workflow_run_id": run.workflow_run_id,
                            "workflow_node_id": node.node_id,
                        },
                    )
                except Exception as exc:
                    return self._fail(
                        task,
                        run,
                        definition,
                        current,
                        context,
                        visits,
                        steps,
                        str(exc),
                    )
                if result.status != ExecutionStatus.SUCCEEDED:
                    message = result.error.message if result.error else "capability execution failed"
                    return self._fail(
                        task,
                        run,
                        definition,
                        current,
                        context,
                        visits,
                        steps,
                        message,
                    )
                context[node.output_key or node.node_id] = result.output
                current = node.next_node_id or ""

            elif node.node_type == WorkflowNodeType.CONDITION:
                value = self._resolve_path(context, node.condition_key or "")
                if not isinstance(value, bool):
                    return self._fail(
                        task,
                        run,
                        definition,
                        current,
                        context,
                        visits,
                        steps,
                        f"condition value must be boolean: {node.condition_key}",
                    )
                current = node.true_node_id if value else node.false_node_id
                current = current or ""

            elif node.node_type == WorkflowNodeType.APPROVAL:
                key = node.approval_key or ""
                if key not in approvals:
                    human_action_id = run.metadata.get("human_action_id")
                    if not resuming_gate and self.approval_requester is not None:
                        human_action_id = self.approval_requester.request(
                            task.project_id,
                            task.task_id,
                            run.workflow_run_id,
                            node,
                            self._now(),
                        )
                    metadata = self._metadata(definition, current, context, visits, steps)
                    if human_action_id:
                        metadata["human_action_id"] = human_action_id
                    waiting = run.model_copy(
                        update={
                            "status": WorkflowExecutionStatus.WAITING_FOR_APPROVAL.value,
                            "updated_at": self._now(),
                            "metadata": metadata,
                        }
                    )
                    self.store.save_workflow_run(waiting)
                    return WorkflowExecutionResult(
                        workflow_run_id=waiting.workflow_run_id,
                        task_id=task.task_id,
                        status=WorkflowExecutionStatus.WAITING_FOR_APPROVAL,
                        current_node_id=current,
                        context=context,
                    )
                decision = approvals[key]
                if not isinstance(decision, bool):
                    return self._fail(
                        task,
                        run,
                        definition,
                        current,
                        context,
                        visits,
                        steps,
                        f"approval decision must be boolean: {key}",
                    )
                current = node.approved_node_id if decision else node.rejected_node_id
                current = current or ""

            run = run.model_copy(
                update={
                    "status": WorkflowExecutionStatus.RUNNING.value,
                    "updated_at": self._now(),
                    "metadata": self._metadata(definition, current, context, visits, steps),
                }
            )
            self.store.save_workflow_run(run)

    def _fail(
        self,
        task: Task,
        run: WorkflowRun,
        definition: WorkflowDefinition,
        current: str,
        context: dict,
        visits: dict[str, int],
        steps: int,
        error: str,
    ) -> WorkflowExecutionResult:
        metadata = self._metadata(definition, current, context, visits, steps)
        metadata["error"] = error
        failed = run.model_copy(
            update={
                "status": WorkflowExecutionStatus.FAILED.value,
                "updated_at": self._now(),
                "metadata": metadata,
            }
        )
        self.store.save_workflow_run(failed)
        if task.status == TaskStatus.RUNNING.value:
            task = transition_task(task, TaskStatus.FAILED, self._now())
            self.store.save_task(task)
        return WorkflowExecutionResult(
            workflow_run_id=failed.workflow_run_id,
            task_id=task.task_id,
            status=WorkflowExecutionStatus.FAILED,
            current_node_id=current,
            context=context,
            error=error,
        )

    def _find_run(self, project_id: str, workflow_run_id: str) -> WorkflowRun:
        for run in self.store.list_workflow_runs(project_id):
            if run.workflow_run_id == workflow_run_id:
                return run
        raise KeyError(workflow_run_id)

    @staticmethod
    def _resolve_path(context: dict, path: str):
        value = context
        for part in path.split("."):
            if not part or not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value

    @staticmethod
    def _metadata(
        definition: WorkflowDefinition,
        current: str,
        context: dict,
        visits: dict[str, int],
        steps: int,
    ) -> dict:
        return {
            "workflow_version": definition.workflow_version,
            "current_node_id": current,
            "context": context,
            "visits": visits,
            "steps": steps,
        }

    @staticmethod
    def _result_from_run(run: WorkflowRun) -> WorkflowExecutionResult:
        context = dict(run.metadata.get("context", {}))
        return WorkflowExecutionResult(
            workflow_run_id=run.workflow_run_id,
            task_id=run.task_id,
            status=WorkflowExecutionStatus(run.status),
            current_node_id=run.metadata.get("current_node_id"),
            context=context,
            error=run.metadata.get("error"),
        )
