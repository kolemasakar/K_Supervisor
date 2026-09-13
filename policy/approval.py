from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.agent import AgentRunRequest
from models.intervention import HumanActionRequest
from persistence.base import PersistenceStore
from registry.agent_registry import AgentRegistry
from supervisor.human_intervention import HumanInterventionBroker

from .contracts import ApprovalRecord, ApprovalStatus, RiskClass
from .resolution import permission_scope_hash, requested_permissions


class PolicyApprovalBroker:
    def __init__(
        self,
        store: PersistenceStore,
        agents: AgentRegistry,
        human: HumanInterventionBroker,
    ):
        self.store = store
        self.agents = agents
        self.human = human

    def request(self, request: AgentRunRequest, at: datetime) -> ApprovalRecord:
        capability = self.agents.capabilities.get(
            request.capability_id,
            request.capability_version,
        )
        if capability is None:
            raise KeyError(f"capability not registered: {request.capability_id}")
        risk = RiskClass(capability.risk_class)
        grant = requested_permissions(request, capability.side_effects)
        scope_hash = permission_scope_hash(request, grant, risk)

        for current in self.store.list_approvals(request.project_id):
            if current.scope_hash == scope_hash and current.status in {
                ApprovalStatus.PENDING,
                ApprovalStatus.APPROVED,
            }:
                return current

        approval_id = f"APPROVAL_{uuid4().hex}"
        record = ApprovalRecord(
            approval_id=approval_id,
            project_id=request.project_id,
            scope_hash=scope_hash,
            requested_permissions=grant,
            created_at=at,
            metadata={
                "agent_id": request.agent_id,
                "capability_id": request.capability_id,
                "operation": request.operation,
                "risk_class": risk.value,
            },
        )
        self.store.save_approval(record)

        action = HumanActionRequest(
            human_action_id=f"HUMAN_{uuid4().hex}",
            project_id=request.project_id,
            action_type="POLICY_PERMISSION_EXPANSION",
            title="Permission expansion approval required",
            summary=(
                f"Agent {request.agent_id} requests a permission scope requiring explicit approval "
                f"for capability {request.capability_id}."
            ),
            required_action=f"Approve or reject policy approval {approval_id}.",
            blocking=True,
            created_at=at,
            resume_condition=f"approval:{approval_id}",
            verification_method="POLICY_APPROVAL_RECORD",
        )
        opened = self.human.open(action)
        record = record.model_copy(update={"human_action_id": opened.human_action_id})
        self.store.save_approval(record)
        return record

    def approve(self, approval_id: str, at: datetime) -> ApprovalRecord:
        record = self._get(approval_id)
        if record.status == ApprovalStatus.APPROVED:
            return record
        if record.status == ApprovalStatus.REJECTED:
            raise ValueError("rejected approval cannot be approved")
        if record.human_action_id is not None:
            self.human.verify(record.human_action_id, True, at)
        approved = record.model_copy(
            update={"status": ApprovalStatus.APPROVED, "decided_at": at}
        )
        self.store.save_approval(approved)
        return approved

    def reject(self, approval_id: str, at: datetime) -> ApprovalRecord:
        record = self._get(approval_id)
        if record.status == ApprovalStatus.REJECTED:
            return record
        if record.status == ApprovalStatus.APPROVED:
            raise ValueError("approved permission cannot be rejected retroactively")
        if record.human_action_id is not None:
            self.human.cancel(record.human_action_id, at)
        rejected = record.model_copy(
            update={"status": ApprovalStatus.REJECTED, "decided_at": at}
        )
        self.store.save_approval(rejected)
        return rejected

    def get_approval(self, approval_id: str) -> ApprovalRecord | None:
        return self.store.get_approval(approval_id)

    def _get(self, approval_id: str) -> ApprovalRecord:
        record = self.store.get_approval(approval_id)
        if record is None:
            raise KeyError(approval_id)
        return record
