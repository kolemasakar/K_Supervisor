from __future__ import annotations

from datetime import datetime, timezone

from models.capability import CapabilityRequirement
from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType
from persistence.base import PersistenceStore

from .contracts import WorkflowExecutionResult
from .engine import WorkflowEngine, WorkflowRuntimeError
from .structured_approval import StructuredApprovalCoordinator

REFERENCE_WORKFLOW_ID = "reference.research_review"
PROFILE_CONTEXT_KEY = "profile_proposal"
PROFILE_APPROVAL_KEY = "review_profile"


def _requirement(capability_id: str) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=capability_id,
        version_constraint="1.0.0",
        operation="run",
    )


def reference_research_definition(max_iterations: int = 3) -> WorkflowDefinition:
    if max_iterations < 2:
        raise ValueError("max_iterations must be >= 2")
    nodes = (
        WorkflowNode(
            node_id="profile",
            node_type=WorkflowNodeType.CAPABILITY,
            requirement=_requirement("profile.reference_review"),
            input_key="__input__",
            output_key=PROFILE_CONTEXT_KEY,
            next_node_id="profile_approval",
        ),
        WorkflowNode(
            node_id="profile_approval",
            node_type=WorkflowNodeType.APPROVAL,
            approval_key=PROFILE_APPROVAL_KEY,
            approval_prompt="Approve or edit the task-specific review profile before research starts.",
            approved_node_id="research_initial",
            rejected_node_id="rejected",
        ),
        WorkflowNode(
            node_id="research_initial",
            node_type=WorkflowNodeType.CAPABILITY,
            requirement=_requirement("research.reference_review"),
            input_key=PROFILE_CONTEXT_KEY,
            output_key="research",
            next_node_id="review",
        ),
        WorkflowNode(
            node_id="review",
            node_type=WorkflowNodeType.CAPABILITY,
            requirement=_requirement("review.reference_review"),
            input_key="research",
            output_key="review",
            next_node_id="decision",
            max_visits=max_iterations,
        ),
        WorkflowNode(
            node_id="decision",
            node_type=WorkflowNodeType.CONDITION,
            condition_key="review.accepted",
            true_node_id="report",
            false_node_id="research_revision",
            max_visits=max_iterations,
        ),
        WorkflowNode(
            node_id="research_revision",
            node_type=WorkflowNodeType.CAPABILITY,
            requirement=_requirement("research.reference_review"),
            input_key="review",
            output_key="research",
            next_node_id="review",
            max_visits=max_iterations - 1,
        ),
        WorkflowNode(
            node_id="report",
            node_type=WorkflowNodeType.CAPABILITY,
            requirement=_requirement("report.reference_review"),
            input_key="review",
            output_key="final",
            next_node_id="completed",
        ),
        WorkflowNode(node_id="completed", node_type=WorkflowNodeType.END),
        WorkflowNode(node_id="rejected", node_type=WorkflowNodeType.END),
    )
    return WorkflowDefinition(
        workflow_id=REFERENCE_WORKFLOW_ID,
        workflow_version="1.0.0",
        start_node_id="profile",
        nodes=nodes,
        max_steps=6 + (max_iterations * 3),
    )


class ReferenceResearchReviewWorkflow:
    """Reference re-composition of the v1.0 research/review behavior."""

    def __init__(
        self,
        engine: WorkflowEngine,
        store: PersistenceStore,
        *,
        max_iterations: int = 3,
    ):
        self.engine = engine
        self.store = store
        self.definition = reference_research_definition(max_iterations)
        self.approvals = StructuredApprovalCoordinator(engine, store)

    def start(self, project_id: str, title: str, input_data: dict) -> WorkflowExecutionResult:
        return self.engine.start(project_id, title, self.definition, input_data)

    def approve_profile(
        self,
        project_id: str,
        workflow_run_id: str,
        *,
        approved_by: str,
        edits: dict | None = None,
        at: datetime | None = None,
    ) -> WorkflowExecutionResult:
        run = self._find(project_id, workflow_run_id)
        context = dict(run.metadata.get("context", {}))
        proposal = context.get(PROFILE_CONTEXT_KEY)
        if not isinstance(proposal, dict) or not isinstance(proposal.get("profile"), dict):
            raise WorkflowRuntimeError("workflow has no reviewable profile proposal")
        profile = dict(proposal["profile"])
        if profile.get("status") != "REVIEW_REQUIRED":
            raise WorkflowRuntimeError("profile is not awaiting review")
        protected = {"profile_id", "profile_version", "status", "approved_by", "approved_at"}
        changes = dict(edits or {})
        if protected.intersection(changes):
            raise WorkflowRuntimeError("profile identity and approval fields cannot be edited")
        profile.update(changes)
        threshold = float(profile.get("confidence_threshold", 0.8))
        if not 0.0 <= threshold <= 1.0:
            raise WorkflowRuntimeError("confidence_threshold must be between 0 and 1")
        approved_at = at or datetime.now(timezone.utc)
        profile.update(
            {
                "status": "APPROVED",
                "approved_by": approved_by,
                "approved_at": approved_at.isoformat(),
            }
        )
        approved_value = dict(proposal)
        approved_value["profile"] = profile
        return self.approvals.approve(
            project_id,
            workflow_run_id,
            self.definition,
            approval_key=PROFILE_APPROVAL_KEY,
            context_key=PROFILE_CONTEXT_KEY,
            approved_value=approved_value,
            approved_by=approved_by,
            approved_at=approved_at,
            edited=bool(changes),
        )

    def reject_profile(self, project_id: str, workflow_run_id: str) -> WorkflowExecutionResult:
        return self.approvals.reject(
            project_id,
            workflow_run_id,
            self.definition,
            approval_key=PROFILE_APPROVAL_KEY,
        )

    def _find(self, project_id: str, workflow_run_id: str):
        for run in self.store.list_workflow_runs(project_id):
            if run.workflow_run_id == workflow_run_id:
                return run
        raise KeyError(workflow_run_id)
