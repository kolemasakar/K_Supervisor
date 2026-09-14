from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from models.agent import AgentRunRequest
from registry.agent_registry import AgentRegistry
from registry.project_registry import ProjectRegistry

from .audit import NullPolicyAuditSink, PolicyAuditSink
from .contracts import (
    ApprovalRecord,
    ApprovalStatus,
    LeastPrivilegeExecutionContext,
    PolicyDecision,
    PolicyEffect,
    RiskClass,
    SideEffect,
)
from .resolution import (
    apply_workflow_constraints,
    constraints_from_spec,
    permission_scope_hash,
    requested_permissions,
)


class ApprovalLookup:
    def get_approval(self, approval_id: str) -> ApprovalRecord | None:
        raise NotImplementedError


class PolicyEngine:
    def __init__(
        self,
        projects: ProjectRegistry,
        agents: AgentRegistry,
        *,
        approvals: ApprovalLookup | None = None,
        audit: PolicyAuditSink | None = None,
    ):
        self.projects = projects
        self.agents = agents
        self.approvals = approvals
        self.audit = audit or NullPolicyAuditSink()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def evaluate(self, request: AgentRunRequest) -> PolicyDecision:
        capability = self.agents.capabilities.get(
            request.capability_id,
            request.capability_version,
        )
        if capability is None:
            return self._decision(request, PolicyEffect.DENY, "CAPABILITY_UNKNOWN", "capability is not registered", RiskClass.CRITICAL)

        try:
            risk = RiskClass(capability.risk_class)
            grant = requested_permissions(request, capability.side_effects)
        except (ValueError, TypeError) as exc:
            return self._decision(request, PolicyEffect.DENY, "POLICY_INPUT_INVALID", str(exc), RiskClass.CRITICAL)

        snapshot = self.projects.recover(request.project_id)
        constraints = constraints_from_spec(snapshot.active_spec)
        workflow_patch = request.policy.get("workflow_constraints", {}) if request.policy else {}
        try:
            constraints = apply_workflow_constraints(constraints, workflow_patch)
        except (ValueError, TypeError) as exc:
            return self._decision(request, PolicyEffect.DENY, "WORKFLOW_POLICY_INVALID", str(exc), risk)

        if request.capability_id in constraints.denied_capabilities:
            return self._decision(request, PolicyEffect.DENY, "CAPABILITY_DENIED", "capability is denied by project policy", risk)
        if constraints.allowed_capabilities and request.capability_id not in constraints.allowed_capabilities:
            return self._decision(request, PolicyEffect.DENY, "CAPABILITY_NOT_ALLOWED", "capability is outside the project allowlist", risk)

        denied = set(constraints.denied_side_effects)
        allowed = set(constraints.allowed_side_effects)
        approval_side_effects = set(constraints.approval_side_effects)
        for effect in grant.side_effects:
            if effect in denied:
                return self._decision(request, PolicyEffect.DENY, "SIDE_EFFECT_DENIED", f"side effect denied: {effect.value}", risk)
            if effect not in allowed and effect not in approval_side_effects:
                return self._decision(request, PolicyEffect.DENY, "SIDE_EFFECT_NOT_ALLOWED", f"side effect is not allowed: {effect.value}", risk)

        tool_permissions = constraints.agent_tool_permissions.get(request.agent_id, {})
        for tool_id, operations in grant.tools.items():
            permitted = set(tool_permissions.get(tool_id, ()))
            if not set(operations).issubset(permitted):
                return self._decision(request, PolicyEffect.DENY, "TOOL_PERMISSION_DENIED", f"tool permission denied: {tool_id}", risk)

        permitted_refs = set(constraints.allowed_access_refs)
        for reference in grant.access_refs:
            if reference not in permitted_refs:
                return self._decision(request, PolicyEffect.DENY, "ACCESS_REFERENCE_DENIED", "access reference is outside the approved scope", risk)

        needs_approval = risk in set(constraints.approval_risk_classes) or any(
            effect in approval_side_effects for effect in grant.side_effects
        )
        approval_id = request.policy.get("approval_id") if request.policy else None
        scope_hash = permission_scope_hash(request, grant, risk)
        if needs_approval:
            approval = self.approvals.get_approval(approval_id) if self.approvals and approval_id else None
            if approval is not None and approval.status == ApprovalStatus.REJECTED:
                return self._decision(request, PolicyEffect.DENY, "APPROVAL_REJECTED", "permission expansion was rejected", risk, approval_id=approval.approval_id)
            if approval is not None and approval.status == ApprovalStatus.REVOKED:
                return self._decision(request, PolicyEffect.REQUIRE_APPROVAL, "APPROVAL_REVOKED", "permission expansion approval was revoked", risk, approval_id=approval.approval_id, metadata={"scope_hash": scope_hash})
            if approval is not None and (
                approval.status == ApprovalStatus.EXPIRED
                or approval.is_expired_at(self._now())
            ):
                return self._decision(request, PolicyEffect.REQUIRE_APPROVAL, "APPROVAL_EXPIRED", "permission expansion approval expired", risk, approval_id=approval.approval_id, metadata={"scope_hash": scope_hash})
            if approval is None or approval.status != ApprovalStatus.APPROVED or approval.scope_hash != scope_hash:
                return self._decision(request, PolicyEffect.REQUIRE_APPROVAL, "APPROVAL_REQUIRED", "material permission scope requires explicit approval", risk, approval_id=approval_id, metadata={"scope_hash": scope_hash})

        context = LeastPrivilegeExecutionContext(
            project_id=request.project_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            operation=request.operation,
            side_effects=grant.side_effects,
            tool_permissions=grant.tools,
            access_refs=grant.access_refs,
            approval_id=approval_id,
        )
        return self._decision(
            request,
            PolicyEffect.ALLOW,
            "POLICY_ALLOWED",
            "execution is allowed within the resolved least-privilege context",
            risk,
            execution_context=context,
            approval_id=approval_id,
            metadata={"scope_hash": scope_hash},
        )

    def _decision(
        self,
        request: AgentRunRequest,
        effect: PolicyEffect,
        reason_code: str,
        reason: str,
        risk: RiskClass,
        *,
        execution_context: LeastPrivilegeExecutionContext | None = None,
        approval_id: str | None = None,
        metadata: dict | None = None,
    ) -> PolicyDecision:
        decision = PolicyDecision(
            decision_id=f"POLICY_{uuid4().hex}",
            project_id=request.project_id,
            request_id=request.request_id,
            effect=effect,
            reason_code=reason_code,
            reason=reason,
            risk_class=risk,
            evaluated_at=self._now(),
            execution_context=execution_context,
            approval_id=approval_id,
            metadata=metadata or {},
        )
        self.audit.append(decision)
        return decision
