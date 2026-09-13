from __future__ import annotations

from enum import StrEnum

from models.base import ContractModel, JsonObject


class WorkflowExecutionStatus(StrEnum):
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class WorkflowExecutionResult(ContractModel):
    workflow_run_id: str
    task_id: str
    status: WorkflowExecutionStatus
    current_node_id: str | None = None
    context: JsonObject = {}
    error: str | None = None
