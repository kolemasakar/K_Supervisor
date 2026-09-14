from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.agent import AgentRunRequest
from models.base import ensure_tz
from models.intervention import HumanActionRequest
from observability.audit import build_audit_event
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

    def request(
        self,
        request: AgentRunRequest,
        at: datetime,
        *,
        expires_at: datetime | None = None,
    ) -> ApprovalRecord:
        at = ensure_tz(at)
        expires_at = None if expires_at is None else ensure_tz(expires_at)
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
            if current.scope_hash != scope_hash:
                continue
            if current.status in {ApprovalStatus.PENDING, ApprovalStatus.APPROVED}:
                if current.is_expired_at(at):
                    self.expire(current.approval_id, at)
                    continue
                return current

        approval_id = f"APPROVAL_{uuid4().hex}"
        record = ApprovalRecord(
            approval_id=approval_id,
            project_id=request.project_id,
            scope_hash=scope_hash,
            requested_permissions=grant,
            created_at=at,
            expires_at=expires_at,
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
        self._save(record, "APPROVAL_REQUESTED", at)
        return record

    def approve(self, approval_id: str, at: datetime) -> ApprovalRecord:
        at = ensure_tz(at)
        record = self._get(approval_id)
        if record.status == ApprovalStatus.APPROVED:
            if record.is_expired_at(at):
                self.expire(approval_id, at)
                raise ValueError("approval has expired")
            return record
        if record.status in {
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.REVOKED,
        }:
            raise ValueError(f"{record.status.value.lower()} approval cannot be approved")
        if record.is_expired_at(at):
            self.expire(approval_id, at)
            raise ValueError("approval has expired")
        if record.human_action_id is not None:
            self.human.verify(record.human_action_id, True, at)
        approved = record.model_copy(
            update={"status": ApprovalStatus.APPROVED, "decided_at": at}
        )
        self._save(approved, "APPROVAL_APPROVED", at)
        return approved

    def reject(self, approval_id: str, at: datetime) -> ApprovalRecord:
        at = ensure_tz(at)
        record = self._get(approval_id)
        if record.status == ApprovalStatus.REJECTED:
            return record
        if record.status != ApprovalStatus.PENDING:
            raise ValueError(f"{record.status.value.lower()} approval cannot be rejected")
        if record.is_expired_at(at):
            self.expire(approval_id, at)
            raise ValueError("approval has expired")
        if record.human_action_id is not None:
            self.human.cancel(record.human_action_id, at)
        rejected = record.model_copy(
            update={"status": ApprovalStatus.REJECTED, "decided_at": at}
        )
        self._save(rejected, "APPROVAL_REJECTED", at)
        return rejected

    def expire(self, approval_id: str, at: datetime) -> ApprovalRecord:
        at = ensure_tz(at)
        record = self._get(approval_id)
        if record.status == ApprovalStatus.EXPIRED:
            return record
        if record.status in {ApprovalStatus.REJECTED, ApprovalStatus.REVOKED}:
            raise ValueError(f"{record.status.value.lower()} approval cannot expire")
        if record.expires_at is None or at < record.expires_at:
            raise ValueError("approval has not reached expires_at")
        if record.status == ApprovalStatus.PENDING and record.human_action_id is not None:
            self.human.cancel(record.human_action_id, at)
        expired = record.model_copy(
            update={"status": ApprovalStatus.EXPIRED, "expired_at": at}
        )
        self._save(expired, "APPROVAL_EXPIRED", at)
        return expired

    def revoke(
        self,
        approval_id: str,
        at: datetime,
        *,
        reason: str,
    ) -> ApprovalRecord:
        at = ensure_tz(at)
        if not reason.strip():
            raise ValueError("revocation reason is required")
        record = self._get(approval_id)
        if record.status == ApprovalStatus.REVOKED:
            return record
        if record.status != ApprovalStatus.APPROVED:
            raise ValueError("only approved permission can be revoked")
        if record.is_expired_at(at):
            self.expire(approval_id, at)
            raise ValueError("approval has expired")
        revoked = record.model_copy(
            update={
                "status": ApprovalStatus.REVOKED,
                "revoked_at": at,
                "revocation_reason": reason.strip(),
            }
        )
        self._save(revoked, "APPROVAL_REVOKED", at)
        return revoked

    def get_approval(self, approval_id: str) -> ApprovalRecord | None:
        return self.store.get_approval(approval_id)

    def _save(
        self,
        record: ApprovalRecord,
        event_type: str,
        at: datetime,
    ) -> None:
        audit = build_audit_event(
            project_id=record.project_id,
            category="POLICY",
            event_type=event_type,
            occurred_at=at,
            resource_type="ApprovalRecord",
            resource_id=record.approval_id,
            correlation_id=record.human_action_id,
            details={
                "status": record.status.value,
                "scope_hash": record.scope_hash,
                "expires_at": (
                    record.expires_at.isoformat() if record.expires_at is not None else None
                ),
            },
        )
        self.store.save_approval(record, audit)

    def _get(self, approval_id: str) -> ApprovalRecord:
        record = self.store.get_approval(approval_id)
        if record is None:
            raise KeyError(approval_id)
        return record
