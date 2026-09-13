from __future__ import annotations

from datetime import datetime
from typing import Protocol

from models.intervention import HumanActionRequest
from models.workflow import WorkflowNode
from supervisor.human_intervention import HumanInterventionBroker
from supervisor.ids import IdFactory


class ApprovalRequester(Protocol):
    def request(
        self,
        project_id: str,
        task_id: str,
        workflow_run_id: str,
        node: WorkflowNode,
        at: datetime,
    ) -> str | None: ...


class HumanInterventionApprovalRequester:
    def __init__(self, broker: HumanInterventionBroker, ids: IdFactory | None = None):
        self.broker = broker
        self.ids = ids or IdFactory()

    def request(
        self,
        project_id: str,
        task_id: str,
        workflow_run_id: str,
        node: WorkflowNode,
        at: datetime,
    ) -> str:
        action = HumanActionRequest(
            human_action_id=self.ids.new("HUMAN"),
            project_id=project_id,
            action_type="WORKFLOW_APPROVAL",
            title=f"Workflow approval: {node.approval_key}",
            summary=node.approval_prompt or "Workflow approval required",
            required_action=node.approval_prompt or "Approve or reject the workflow gate",
            blocking=True,
            created_at=at,
            resume_condition=f"workflow approval recorded for {node.approval_key}",
            verification_method="OWNER_CONFIRMATION",
        )
        self.broker.open(action)
        return action.human_action_id
