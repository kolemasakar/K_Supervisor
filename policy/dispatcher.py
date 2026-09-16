from __future__ import annotations

from models.agent import AgentError, AgentRunRequest, AgentRunResult
from models.enums import ExecutionStatus
from supervisor.dispatch import AgentDispatcher

from .approval import PolicyApprovalBroker
from .contracts import PolicyEffect
from .engine import PolicyEngine


class PolicyEnforcedDispatcher:
    def __init__(
        self,
        engine: PolicyEngine,
        delegate: AgentDispatcher,
        approval_broker: PolicyApprovalBroker | None = None,
    ):
        self.engine = engine
        self.delegate = delegate
        self.approval_broker = approval_broker

    def dispatch(self, request: AgentRunRequest) -> AgentRunResult:
        decision = self.engine.evaluate(request)
        if decision.effect == PolicyEffect.REQUIRE_APPROVAL and self.approval_broker is not None:
            approval = self.approval_broker.request(request, decision.evaluated_at)
            request = request.model_copy(
                update={"policy": {**request.policy, "approval_id": approval.approval_id}}
            )
            decision = self.engine.evaluate(request)

        if decision.effect != PolicyEffect.ALLOW:
            return AgentRunResult(
                request_id=request.request_id,
                project_id=request.project_id,
                task_id=request.task_id,
                workflow_run_id=request.workflow_run_id,
                run_id=request.run_id,
                agent_id=request.agent_id,
                capability_id=request.capability_id,
                capability_version=request.capability_version,
                status=ExecutionStatus.BLOCKED,
                error=AgentError(
                    code=decision.reason_code,
                    category="POLICY_BLOCKED",
                    message=decision.reason,
                    retryable=False,
                    details={
                        "decision_id": decision.decision_id,
                        "effect": decision.effect.value,
                        "approval_id": decision.approval_id,
                        **decision.metadata,
                    },
                ),
            )

        assert decision.execution_context is not None
        authorized = request.model_copy(
            update={
                "policy": {
                    **request.policy,
                    "decision_id": decision.decision_id,
                    "effect": PolicyEffect.ALLOW.value,
                    "execution_context": decision.execution_context.model_dump(mode="json"),
                }
            }
        )
        return self.delegate.dispatch(authorized)
