from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from models.agent import AgentError, AgentRunRequest, AgentRunResult
from models.capability import CapabilityRequirement
from models.enums import ExecutionStatus, ProjectOperationalState
from models.task import Task, WorkflowRun
from persistence.base import PersistenceStore
from registry.agent_registry import AgentRegistry
from registry.project_registry import ProjectRegistry

from .dispatch import AgentDispatcher
from .ids import IdFactory
from .result_validation import AgentResultContractError, validate_result_matches_request
from .routing import NoProviderError, ProviderRouter
from .task_state import TaskStatus, transition_task


class ProjectNotRunnableError(RuntimeError):
    pass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")


EscalationHook = Callable[[Task, AgentRunResult, int], None]


class SupervisorKernel:
    def __init__(
        self,
        projects: ProjectRegistry,
        agents: AgentRegistry,
        store: PersistenceStore,
        dispatcher: AgentDispatcher,
        *,
        router: ProviderRouter | None = None,
        ids: IdFactory | None = None,
        retry_policy: RetryPolicy | None = None,
        escalation_hook: EscalationHook | None = None,
    ):
        self.projects = projects
        self.agents = agents
        self.store = store
        self.dispatcher = dispatcher
        self.router = router or ProviderRouter()
        self.ids = ids or IdFactory()
        self.retry_policy = retry_policy or RetryPolicy()
        self.escalation_hook = escalation_hook

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _save_task_state(self, task: Task, status: TaskStatus) -> Task:
        updated = transition_task(task, status, self._now())
        self.store.save_task(updated)
        return updated

    def run_task(
        self,
        project_id: str,
        title: str,
        requirement: CapabilityRequirement,
        input_data: dict,
        *,
        context: dict | None = None,
        policy: dict | None = None,
        limits: dict | None = None,
        metadata: dict | None = None,
        task_id: str | None = None,
        workflow_run_id: str | None = None,
    ) -> AgentRunResult:
        project = self.projects.get(project_id)
        if project is None:
            raise KeyError(project_id)
        if project.operational_state != ProjectOperationalState.ACTIVE:
            raise ProjectNotRunnableError(
                f"project is not ACTIVE: {project_id} ({project.operational_state})"
            )

        if task_id is not None and self.store.get_task(task_id) is not None:
            raise ValueError(f"task already exists: {task_id}")
        if workflow_run_id is not None and any(
            item.workflow_run_id == workflow_run_id
            for item in self.store.list_workflow_runs(project_id)
        ):
            raise ValueError(f"workflow run already exists: {workflow_run_id}")

        now = self._now()
        task = Task(
            task_id=task_id or self.ids.new("TASK"),
            project_id=project_id,
            title=title,
            status=TaskStatus.NEW.value,
            created_at=now,
            updated_at=now,
            metadata={
                "capability_id": requirement.capability_id,
                "version_constraint": requirement.version_constraint,
                "operation": requirement.operation,
                **(metadata or {}),
            },
        )
        self.store.save_task(task)
        task = self._save_task_state(task, TaskStatus.ROUTING)

        workflow = WorkflowRun(
            workflow_run_id=workflow_run_id or self.ids.new("WF"),
            project_id=project_id,
            task_id=task.task_id,
            workflow_id="supervisor.single_capability",
            status="RUNNING",
            created_at=now,
            updated_at=now,
        )
        self.store.save_workflow_run(workflow)

        providers = self.agents.find_providers(requirement)
        try:
            provider = self.router.select(requirement, providers)
        except NoProviderError:
            task = self._save_task_state(task, TaskStatus.BLOCKED)
            self.store.save_workflow_run(
                workflow.model_copy(update={"status": "BLOCKED", "updated_at": self._now()})
            )
            raise

        task = self._save_task_state(task, TaskStatus.RUNNING)
        last_result: AgentRunResult | None = None

        for attempt in range(1, self.retry_policy.max_attempts + 1):
            request = AgentRunRequest(
                request_id=self.ids.new("REQ"),
                project_id=project_id,
                task_id=task.task_id,
                workflow_run_id=workflow.workflow_run_id,
                run_id=self.ids.new("RUN"),
                agent_id=provider.agent.agent_id,
                capability_id=provider.capability.capability_id,
                capability_version=provider.capability.capability_version,
                operation=requirement.operation,
                input=input_data,
                context=context or {},
                policy=policy or {},
                limits=limits or {},
                metadata={"attempt": attempt},
            )
            task = task.model_copy(
                update={
                    "updated_at": self._now(),
                    "metadata": {
                        **task.metadata,
                        "current_run_id": request.run_id,
                        "last_run_id": request.run_id,
                    },
                }
            )
            self.store.save_task(task)

            try:
                result = self.dispatcher.dispatch(request)
                validate_result_matches_request(request, result)
            except AgentResultContractError as exc:
                result = self._failure(request, "INTERNAL_ERROR", str(exc), False)
            except Exception as exc:
                result = self._failure(request, "EXECUTION_ERROR", str(exc), False)

            self.store.save_agent_run(result)
            last_result = result

            if result.status == ExecutionStatus.SUCCEEDED:
                task = self._save_task_state(task, TaskStatus.SUCCEEDED)
                self.store.save_workflow_run(
                    workflow.model_copy(update={"status": "SUCCEEDED", "updated_at": self._now()})
                )
                return result

            retryable = (
                (result.error is not None and result.error.retryable)
                or result.status == ExecutionStatus.TIMED_OUT
            )
            if retryable and attempt < self.retry_policy.max_attempts:
                task = self._save_task_state(task, TaskStatus.RETRYING)
                task = self._save_task_state(task, TaskStatus.RUNNING)
                continue
            break

        assert last_result is not None
        if last_result.status == ExecutionStatus.BLOCKED:
            self._save_task_state(task, TaskStatus.BLOCKED)
            self.store.save_workflow_run(
                workflow.model_copy(update={"status": "BLOCKED", "updated_at": self._now()})
            )
            return last_result

        if last_result.status == ExecutionStatus.CANCELLED:
            current = self.store.get_task(task.task_id) or task
            if current.status != TaskStatus.CANCELLED.value:
                current = self._save_task_state(current, TaskStatus.CANCELLED)
            self.store.save_workflow_run(
                workflow.model_copy(update={"status": "CANCELLED", "updated_at": self._now()})
            )
            return last_result

        task = self._save_task_state(task, TaskStatus.FAILED)
        self.store.save_workflow_run(
            workflow.model_copy(update={"status": "FAILED", "updated_at": self._now()})
        )
        if self.escalation_hook is not None:
            self.escalation_hook(task, last_result, self.retry_policy.max_attempts)
        return last_result

    def cancel_task(self, project_id: str, task_id: str) -> Task:
        task = self.store.get_task(task_id)
        if task is None or task.project_id != project_id:
            raise KeyError(task_id)
        status = TaskStatus(task.status)
        if status == TaskStatus.CANCELLED:
            return task
        if status in {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.BLOCKED}:
            raise ValueError(f"task is not cancellable: {status.value}")

        run_id = task.metadata.get("current_run_id")
        cancel = getattr(self.dispatcher, "cancel", None)
        if isinstance(run_id, str) and callable(cancel):
            cancel(run_id)

        cancelled = transition_task(task, TaskStatus.CANCELLED, self._now())
        self.store.save_task(cancelled)
        for run in self.store.list_workflow_runs(project_id):
            if run.task_id != task_id:
                continue
            if run.status in {"SUCCEEDED", "FAILED", "BLOCKED", "CANCELLED"}:
                continue
            self.store.save_workflow_run(
                run.model_copy(update={"status": "CANCELLED", "updated_at": self._now()})
            )
        return cancelled

    @staticmethod
    def _failure(
        request: AgentRunRequest,
        category: str,
        message: str,
        retryable: bool,
    ) -> AgentRunResult:
        return AgentRunResult(
            request_id=request.request_id,
            project_id=request.project_id,
            task_id=request.task_id,
            workflow_run_id=request.workflow_run_id,
            run_id=request.run_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            status=ExecutionStatus.FAILED,
            error=AgentError(
                code="SUPERVISOR_DISPATCH_FAILURE",
                category=category,
                message=message,
                retryable=retryable,
            ),
        )
