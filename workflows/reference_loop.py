from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json

from models.capability import CapabilityRequirement
from models.enums import ExecutionStatus, ProjectOperationalState
from models.task import Task, WorkflowRun
from persistence.base import PersistenceStore
from supervisor.kernel import ProjectNotRunnableError, SupervisorKernel
from supervisor.task_state import TaskStatus, transition_task

from .contracts import WorkflowExecutionResult, WorkflowExecutionStatus
from .engine import WorkflowRuntimeError
from .structured_approval import StructuredApprovalRecord

REFERENCE_WORKFLOW_ID = "reference.research_critic"
PROFILE_APPROVAL_KEY = "critic_profile"
REFERENCE_CAPABILITIES = (
    "research.reference",
    "factcheck.reference",
    "critique.reference",
    "report.reference",
)


def _requirement(capability_id: str) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=capability_id,
        version_constraint="1.0.0",
        operation="run",
    )


def _profile_fingerprint(profile: dict) -> str:
    payload = json.dumps(profile, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


class ReferenceResearchReviewWorkflow:
    """Capability-based re-composition of the reference Research-Critic behavior."""

    def __init__(self, kernel: SupervisorKernel, store: PersistenceStore, *, max_iterations: int = 3):
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        self.kernel = kernel
        self.store = store
        self.max_iterations = max_iterations

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def start(self, project_id: str, title: str, input_data: dict) -> WorkflowExecutionResult:
        project = self.kernel.projects.get(project_id)
        if project is None:
            raise KeyError(project_id)
        if project.operational_state != ProjectOperationalState.ACTIVE:
            raise ProjectNotRunnableError(f"project is not ACTIVE: {project_id} ({project.operational_state})")

        now = self._now()
        task = Task(
            task_id=self.kernel.ids.new("TASK"),
            project_id=project_id,
            title=title,
            status=TaskStatus.NEW.value,
            created_at=now,
            updated_at=now,
            metadata={"workflow_id": REFERENCE_WORKFLOW_ID},
        )
        self.store.save_task(task)
        task = transition_task(task, TaskStatus.ROUTING, self._now())
        self.store.save_task(task)
        task = transition_task(task, TaskStatus.RUNNING, self._now())
        self.store.save_task(task)

        criteria = input_data.get("evaluation_criteria", ["evidence", "completeness", "uncertainty"])
        if not isinstance(criteria, list) or not criteria:
            raise ValueError("evaluation_criteria must be a non-empty list")
        threshold = float(input_data.get("confidence_threshold", 0.8))
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1")
        profile = {
            "profile_id": f"PROFILE:{task.task_id}",
            "profile_version": 1,
            "domain": str(input_data.get("domain", "general")),
            "evaluation_criteria": [str(item) for item in criteria],
            "confidence_threshold": threshold,
            "status": "REVIEW_REQUIRED",
            "approved_by": None,
            "approved_at": None,
        }
        context = {
            "__input__": dict(input_data),
            "profile": profile,
            "iteration": 0,
            "review_history": [],
        }
        run = WorkflowRun(
            workflow_run_id=self.kernel.ids.new("WF"),
            project_id=project_id,
            task_id=task.task_id,
            workflow_id=REFERENCE_WORKFLOW_ID,
            status=WorkflowExecutionStatus.WAITING_FOR_APPROVAL.value,
            created_at=now,
            updated_at=now,
            metadata={
                "current_node_id": "profile_approval",
                "context": context,
                "max_iterations": self.max_iterations,
            },
        )
        self.store.save_workflow_run(run)
        return WorkflowExecutionResult(
            workflow_run_id=run.workflow_run_id,
            task_id=task.task_id,
            status=WorkflowExecutionStatus.WAITING_FOR_APPROVAL,
            current_node_id="profile_approval",
            context=context,
        )

    def approve_profile(
        self,
        project_id: str,
        workflow_run_id: str,
        *,
        approved_by: str,
        edits: dict | None = None,
        at: datetime | None = None,
    ) -> WorkflowExecutionResult:
        run = self._find_run(project_id, workflow_run_id)
        if run.status != WorkflowExecutionStatus.WAITING_FOR_APPROVAL.value:
            raise WorkflowRuntimeError("workflow is not waiting for profile approval")
        task = self.store.get_task(run.task_id)
        if task is None:
            raise WorkflowRuntimeError("workflow parent task is missing")
        context = dict(run.metadata.get("context", {}))
        profile = dict(context.get("profile", {}))
        if profile.get("status") != "REVIEW_REQUIRED":
            raise WorkflowRuntimeError("profile is not awaiting review")

        changes = dict(edits or {})
        protected = {"profile_id", "profile_version", "status", "approved_by", "approved_at"}
        if protected.intersection(changes):
            raise WorkflowRuntimeError("profile identity and approval fields cannot be edited")
        profile.update(changes)
        criteria = profile.get("evaluation_criteria", [])
        if not isinstance(criteria, list) or not criteria:
            raise WorkflowRuntimeError("approved profile requires evaluation criteria")
        threshold = float(profile.get("confidence_threshold", 0.8))
        if not 0.0 <= threshold <= 1.0:
            raise WorkflowRuntimeError("confidence_threshold must be between 0 and 1")

        approved_at = at or self._now()
        profile.update(
            {
                "status": "APPROVED",
                "approved_by": approved_by,
                "approved_at": approved_at.isoformat(),
            }
        )
        approval = StructuredApprovalRecord.create(
            approval_key=PROFILE_APPROVAL_KEY,
            context_key="profile",
            approved_by=approved_by,
            approved_at=approved_at,
            edited=bool(changes),
        )
        context["profile"] = profile
        context["profile_fingerprint"] = _profile_fingerprint(profile)
        context["__structured_approvals__"] = {
            PROFILE_APPROVAL_KEY: approval.model_dump(mode="json")
        }
        run = run.model_copy(
            update={
                "status": WorkflowExecutionStatus.RUNNING.value,
                "updated_at": approved_at,
                "metadata": {**run.metadata, "current_node_id": "research", "context": context},
            }
        )
        self.store.save_workflow_run(run)
        return self._drive(task, run, context)

    def _drive(self, task: Task, run: WorkflowRun, context: dict) -> WorkflowExecutionResult:
        request_data = dict(context.get("__input__", {}))
        query = str(request_data.get("query", "")).strip()
        initial_sources = request_data.get("sources", [])
        revision_sources = request_data.get("revision_sources", initial_sources)
        if not isinstance(initial_sources, list) or not isinstance(revision_sources, list):
            return self._fail(task, run, context, "sources and revision_sources must be lists")

        profile = dict(context["profile"])
        frozen = str(context["profile_fingerprint"])
        threshold = float(profile.get("confidence_threshold", 0.8))
        review_history = list(context.get("review_history", []))

        for iteration in range(1, self.max_iterations + 1):
            sources = initial_sources if iteration == 1 else revision_sources
            research = self.kernel.run_task(
                task.project_id,
                f"{REFERENCE_WORKFLOW_ID}:research:{iteration}",
                _requirement("research.reference"),
                {"query": query, "sources": sources},
                metadata={"parent_task_id": task.task_id, "parent_workflow_run_id": run.workflow_run_id, "iteration": iteration},
            )
            if research.status != ExecutionStatus.SUCCEEDED:
                return self._fail(task, run, context, "research capability failed")
            summary = str(research.output.get("summary", ""))

            factcheck = self.kernel.run_task(
                task.project_id,
                f"{REFERENCE_WORKFLOW_ID}:factcheck:{iteration}",
                _requirement("factcheck.reference"),
                {"claim": str(sources[0]) if sources else query, "evidence": sources},
                metadata={"parent_task_id": task.task_id, "parent_workflow_run_id": run.workflow_run_id, "iteration": iteration},
            )
            if factcheck.status != ExecutionStatus.SUCCEEDED:
                return self._fail(task, run, context, "independent fact-check capability failed")

            critique = self.kernel.run_task(
                task.project_id,
                f"{REFERENCE_WORKFLOW_ID}:critique:{iteration}",
                _requirement("critique.reference"),
                {"content": summary},
                metadata={"parent_task_id": task.task_id, "parent_workflow_run_id": run.workflow_run_id, "iteration": iteration},
            )
            if critique.status != ExecutionStatus.SUCCEEDED:
                return self._fail(task, run, context, "critique capability failed")

            verdict = str(critique.output.get("verdict", "REVISE"))
            reliability = 0.95 if verdict == "PASS" else 0.5
            accepted = verdict == "PASS" and reliability >= threshold
            review_history.append(
                {
                    "iteration": iteration,
                    "research_run_id": research.run_id,
                    "factcheck_run_id": factcheck.run_id,
                    "critique_run_id": critique.run_id,
                    "research_agent_id": research.agent_id,
                    "critic_agent_id": critique.agent_id,
                    "verdict": verdict,
                    "reliability_score": reliability,
                    "issues": list(critique.output.get("issues", [])),
                    "factcheck_verdict": factcheck.output.get("verdict"),
                }
            )
            context.update(
                {
                    "iteration": iteration,
                    "research": research.output,
                    "review": review_history[-1],
                    "review_history": review_history,
                }
            )
            self._save_running(run, context, "review")

            if not accepted:
                continue

            final_report = self.kernel.run_task(
                task.project_id,
                f"{REFERENCE_WORKFLOW_ID}:final_report",
                _requirement("report.reference"),
                {"sections": [summary, f"Independent verification: {factcheck.output.get('verdict', '')}"]},
                metadata={"parent_task_id": task.task_id, "parent_workflow_run_id": run.workflow_run_id},
            )
            protocol = self.kernel.run_task(
                task.project_id,
                f"{REFERENCE_WORKFLOW_ID}:review_protocol",
                _requirement("report.reference"),
                {
                    "sections": [
                        f"Profile: {profile.get('profile_id', '')}",
                        f"Iterations: {iteration}",
                        f"Decision: {verdict}",
                        f"Reliability: {reliability:.2f}",
                        "Private chain-of-thought is not stored.",
                    ]
                },
                metadata={"parent_task_id": task.task_id, "parent_workflow_run_id": run.workflow_run_id},
            )
            if final_report.status != ExecutionStatus.SUCCEEDED or protocol.status != ExecutionStatus.SUCCEEDED:
                return self._fail(task, run, context, "report capability failed")
            if _profile_fingerprint(profile) != frozen:
                return self._fail(task, run, context, "approved profile changed during autonomous execution")

            context["final"] = {
                "final_report": final_report.output.get("report", ""),
                "review_protocol": protocol.output.get("report", ""),
                "iteration_count": iteration,
                "final_reliability_score": reliability,
            }
            completed = run.model_copy(
                update={
                    "status": WorkflowExecutionStatus.SUCCEEDED.value,
                    "updated_at": self._now(),
                    "metadata": {**run.metadata, "current_node_id": "completed", "context": context},
                }
            )
            self.store.save_workflow_run(completed)
            task = transition_task(task, TaskStatus.SUCCEEDED, self._now())
            self.store.save_task(task)
            return WorkflowExecutionResult(
                workflow_run_id=completed.workflow_run_id,
                task_id=task.task_id,
                status=WorkflowExecutionStatus.SUCCEEDED,
                current_node_id="completed",
                context=context,
            )

        context["reference_status"] = "MAX_ITERATIONS_REACHED"
        return self._fail(task, run, context, "acceptance criteria not met within max_iterations")

    def _save_running(self, run: WorkflowRun, context: dict, node_id: str) -> None:
        self.store.save_workflow_run(
            run.model_copy(
                update={
                    "status": WorkflowExecutionStatus.RUNNING.value,
                    "updated_at": self._now(),
                    "metadata": {**run.metadata, "current_node_id": node_id, "context": context},
                }
            )
        )

    def _fail(self, task: Task, run: WorkflowRun, context: dict, error: str) -> WorkflowExecutionResult:
        failed = run.model_copy(
            update={
                "status": WorkflowExecutionStatus.FAILED.value,
                "updated_at": self._now(),
                "metadata": {**run.metadata, "current_node_id": "failed", "context": context, "error": error},
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
            current_node_id="failed",
            context=context,
            error=error,
        )

    def _find_run(self, project_id: str, workflow_run_id: str) -> WorkflowRun:
        for run in self.store.list_workflow_runs(project_id):
            if run.workflow_run_id == workflow_run_id:
                return run
        raise KeyError(workflow_run_id)
