from __future__ import annotations

from datetime import datetime

from models.base import ContractModel, JsonObject, ensure_tz
from persistence.base import PersistenceStore

from .contracts import WorkflowExecutionResult, WorkflowExecutionStatus
from .engine import WorkflowEngine, WorkflowRuntimeError


class StructuredApprovalRecord(ContractModel):
    approval_key: str
    context_key: str
    approved_by: str
    approved_at: datetime
    edited: bool = False

    @classmethod
    def create(
        cls,
        *,
        approval_key: str,
        context_key: str,
        approved_by: str,
        approved_at: datetime,
        edited: bool,
    ) -> "StructuredApprovalRecord":
        return cls(
            approval_key=approval_key,
            context_key=context_key,
            approved_by=approved_by,
            approved_at=ensure_tz(approved_at),
            edited=edited,
        )


class StructuredApprovalCoordinator:
    """Resumes an approval gate while durably replacing one reviewed context object."""

    def __init__(self, engine: WorkflowEngine, store: PersistenceStore):
        self.engine = engine
        self.store = store

    def approve(
        self,
        project_id: str,
        workflow_run_id: str,
        definition,
        *,
        approval_key: str,
        context_key: str,
        approved_value: JsonObject,
        approved_by: str,
        approved_at: datetime,
        edited: bool = False,
    ) -> WorkflowExecutionResult:
        run = self._find(project_id, workflow_run_id)
        if run.status != WorkflowExecutionStatus.WAITING_FOR_APPROVAL.value:
            raise WorkflowRuntimeError("workflow is not waiting for approval")
        context = dict(run.metadata.get("context", {}))
        context[context_key] = dict(approved_value)
        record = StructuredApprovalRecord.create(
            approval_key=approval_key,
            context_key=context_key,
            approved_by=approved_by,
            approved_at=approved_at,
            edited=edited,
        )
        approvals = dict(context.get("__structured_approvals__", {}))
        approvals[approval_key] = record.model_dump(mode="json")
        context["__structured_approvals__"] = approvals
        metadata = dict(run.metadata)
        metadata["context"] = context
        self.store.save_workflow_run(run.model_copy(update={"metadata": metadata, "updated_at": ensure_tz(approved_at)}))
        return self.engine.resume(
            project_id,
            workflow_run_id,
            definition,
            approvals={approval_key: True},
        )

    def reject(
        self,
        project_id: str,
        workflow_run_id: str,
        definition,
        *,
        approval_key: str,
    ) -> WorkflowExecutionResult:
        run = self._find(project_id, workflow_run_id)
        if run.status != WorkflowExecutionStatus.WAITING_FOR_APPROVAL.value:
            raise WorkflowRuntimeError("workflow is not waiting for approval")
        return self.engine.resume(
            project_id,
            workflow_run_id,
            definition,
            approvals={approval_key: False},
        )

    def _find(self, project_id: str, workflow_run_id: str):
        for run in self.store.list_workflow_runs(project_id):
            if run.workflow_run_id == workflow_run_id:
                return run
        raise KeyError(workflow_run_id)
