from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from access import AccessReference
from models.agent import AgentRunRequest
from models.side_effect import (
    SideEffectExecutionRecord,
    SideEffectExecutionStatus,
    SideEffectResult,
)
from observability.audit import build_audit_event
from persistence.base import PersistenceConflictError, PersistenceStore
from policy.access_permissions import require_access_reference
from policy.contracts import PolicyDecision, PolicyEffect
from policy.engine import PolicyEngine
from policy.tool_permissions import require_tool_operation
from providers import ProviderRequest
from registry.provider_registry import ProviderRegistry
from registry.tool_registry import ToolRegistry
from tools import ToolRequest


class SideEffectGateway:
    """Central policy/idempotency/audit boundary for tool and provider side effects."""

    def __init__(
        self,
        store: PersistenceStore,
        policy: PolicyEngine,
        *,
        tools: ToolRegistry | None = None,
        providers: ProviderRegistry | None = None,
    ):
        self.store = store
        self.policy = policy
        self.tools = tools or ToolRegistry()
        self.providers = providers or ProviderRegistry()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def invoke_tool(
        self,
        request: AgentRunRequest,
        tool_id: str,
        operation: str,
        input_data: dict | None = None,
        *,
        access_refs: tuple[AccessReference, ...] = (),
        idempotency_key: str | None = None,
        version_constraint: str = "*",
    ) -> SideEffectResult:
        decision = self.policy.evaluate(request)
        blocked = self._authorize(
            request,
            decision,
            component_kind="TOOL",
            component_id=tool_id,
            operation=operation,
            access_refs=access_refs,
            require_tool=(tool_id, operation),
        )
        if blocked is not None:
            return blocked

        tool = self.tools.resolve(tool_id, version_constraint, operation)
        if tool is None:
            return self._unavailable(
                request,
                decision,
                "TOOL",
                tool_id,
                operation,
                "tool operation is unavailable",
            )

        return self._execute(
            request,
            decision,
            component_kind="TOOL",
            component_id=tool.descriptor.tool_id,
            component_version=tool.descriptor.version,
            operation=operation,
            payload=input_data or {},
            access_refs=access_refs,
            idempotency_key=idempotency_key or request.idempotency_key,
            invoke=lambda key: self._normalize_tool_result(
                tool.invoke(
                    ToolRequest(
                        project_id=request.project_id,
                        operation=operation,
                        input=input_data or {},
                        access_refs=access_refs,
                        request_id=request.request_id,
                        agent_id=request.agent_id,
                        capability_id=request.capability_id,
                        capability_version=request.capability_version,
                        idempotency_key=key,
                    )
                )
            ),
        )

    def execute_provider(
        self,
        request: AgentRunRequest,
        provider_id: str,
        operation: str,
        payload: dict | None = None,
        *,
        access_refs: tuple[AccessReference, ...] = (),
        idempotency_key: str | None = None,
        version_constraint: str = "*",
    ) -> SideEffectResult:
        decision = self.policy.evaluate(request)
        blocked = self._authorize(
            request,
            decision,
            component_kind="PROVIDER",
            component_id=provider_id,
            operation=operation,
            access_refs=access_refs,
        )
        if blocked is not None:
            return blocked

        provider = self.providers.resolve(provider_id, version_constraint, operation)
        if provider is None:
            return self._unavailable(
                request,
                decision,
                "PROVIDER",
                provider_id,
                operation,
                "provider operation is unavailable",
            )

        return self._execute(
            request,
            decision,
            component_kind="PROVIDER",
            component_id=provider.descriptor.provider_id,
            component_version=provider.descriptor.version,
            operation=operation,
            payload=payload or {},
            access_refs=access_refs,
            idempotency_key=idempotency_key or request.idempotency_key,
            invoke=lambda key: self._normalize_provider_result(
                provider.execute(
                    ProviderRequest(
                        project_id=request.project_id,
                        operation=operation,
                        payload=payload or {},
                        access_refs=access_refs,
                        request_id=request.request_id,
                        agent_id=request.agent_id,
                        capability_id=request.capability_id,
                        capability_version=request.capability_version,
                        idempotency_key=key,
                    )
                )
            ),
        )

    def _authorize(
        self,
        request: AgentRunRequest,
        decision: PolicyDecision,
        *,
        component_kind: str,
        component_id: str,
        operation: str,
        access_refs: tuple[AccessReference, ...],
        require_tool: tuple[str, str] | None = None,
    ) -> SideEffectResult | None:
        if decision.effect != PolicyEffect.ALLOW or decision.execution_context is None:
            return self._blocked(
                request,
                decision,
                component_kind,
                component_id,
                operation,
                decision.reason_code,
                decision.reason,
            )

        context = decision.execution_context
        if (
            context.project_id != request.project_id
            or context.agent_id != request.agent_id
            or context.capability_id != request.capability_id
            or context.operation != request.operation
        ):
            return self._blocked(
                request,
                decision,
                component_kind,
                component_id,
                operation,
                "SIDE_EFFECT_CONTEXT_MISMATCH",
                "least-privilege execution context does not match request correlation",
            )

        try:
            if require_tool is not None:
                require_tool_operation(context, *require_tool)
            for reference in access_refs:
                require_access_reference(context, reference)
        except PermissionError as exc:
            return self._blocked(
                request,
                decision,
                component_kind,
                component_id,
                operation,
                "SIDE_EFFECT_PERMISSION_DENIED",
                str(exc),
            )
        return None

    def _execute(
        self,
        request: AgentRunRequest,
        decision: PolicyDecision,
        *,
        component_kind: str,
        component_id: str,
        component_version: str,
        operation: str,
        payload: dict,
        access_refs: tuple[AccessReference, ...],
        idempotency_key: str | None,
        invoke,
    ) -> SideEffectResult:
        signature = self._signature(payload, access_refs)
        execution_id = self._execution_id(
            request,
            component_kind,
            component_id,
            operation,
            idempotency_key,
        )
        created_at = self._now()
        pending = SideEffectExecutionRecord(
            execution_id=execution_id,
            project_id=request.project_id,
            request_id=request.request_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            component_kind=component_kind,
            component_id=component_id,
            component_version=component_version,
            operation=operation,
            idempotency_key=idempotency_key,
            signature=signature,
            status=SideEffectExecutionStatus.PENDING,
            policy_decision_id=decision.decision_id,
            created_at=created_at,
        )
        attempt_audit = self._audit_event(
            pending,
            "SIDE_EFFECT_ATTEMPTED",
            created_at,
            details={"idempotency_key": idempotency_key},
        )

        try:
            self.store.claim_side_effect_execution(pending, attempt_audit)
        except PersistenceConflictError:
            existing = self.store.get_side_effect_execution(execution_id)
            if existing is None:
                return self._failure_result(
                    pending,
                    "SIDE_EFFECT_IDEMPOTENCY_CONFLICT",
                    "side-effect execution claim conflicted without an authoritative record",
                    decision.decision_id,
                )
            if existing.signature != signature:
                result = self._result_from_record(
                    existing,
                    error_code="SIDE_EFFECT_IDEMPOTENCY_CONFLICT",
                    error_message="idempotency key was reused with different side-effect input",
                    replay=True,
                    force_status=SideEffectExecutionStatus.BLOCKED,
                    request_id=request.request_id,
                    policy_decision_id=decision.decision_id,
                )
                self.store.append_audit_event(
                    self._replay_audit(
                        existing,
                        request,
                        decision,
                        "SIDE_EFFECT_IDEMPOTENCY_CONFLICT",
                        severity="WARNING",
                    )
                )
                return result
            self.store.append_audit_event(
                self._replay_audit(existing, request, decision, "SIDE_EFFECT_REPLAYED")
            )
            return self._result_from_record(
                existing,
                replay=True,
                request_id=request.request_id,
                policy_decision_id=decision.decision_id,
            )

        try:
            output, metadata = invoke(idempotency_key)
        except Exception as exc:
            completed_at = self._now()
            failed = pending.model_copy(
                update={
                    "status": SideEffectExecutionStatus.FAILED,
                    "error_code": "SIDE_EFFECT_ADAPTER_ERROR",
                    "error_message": str(exc),
                    "completed_at": completed_at,
                }
            )
            audit = self._audit_event(
                failed,
                "SIDE_EFFECT_FAILED",
                completed_at,
                severity="WARNING",
                details={"error_code": failed.error_code},
            )
            self.store.complete_side_effect_execution(failed, audit)
            return self._result_from_record(failed)

        completed_at = self._now()
        succeeded = pending.model_copy(
            update={
                "status": SideEffectExecutionStatus.SUCCEEDED,
                "output": output,
                "metadata": metadata,
                "completed_at": completed_at,
            }
        )
        audit = self._audit_event(succeeded, "SIDE_EFFECT_SUCCEEDED", completed_at)
        self.store.complete_side_effect_execution(succeeded, audit)
        return self._result_from_record(succeeded)

    def _blocked(
        self,
        request: AgentRunRequest,
        decision: PolicyDecision,
        component_kind: str,
        component_id: str,
        operation: str,
        error_code: str,
        error_message: str,
    ) -> SideEffectResult:
        execution_id = f"SIDE_EFFECT_BLOCKED_{uuid4().hex}"
        self.store.append_audit_event(
            build_audit_event(
                project_id=request.project_id,
                category="SIDE_EFFECT",
                event_type="SIDE_EFFECT_BLOCKED",
                occurred_at=self._now(),
                resource_type="SideEffectExecution",
                resource_id=execution_id,
                correlation_id=request.request_id,
                details={
                    "request_id": request.request_id,
                    "agent_id": request.agent_id,
                    "capability_id": request.capability_id,
                    "capability_version": request.capability_version,
                    "component_kind": component_kind,
                    "component_id": component_id,
                    "operation": operation,
                    "policy_decision_id": decision.decision_id,
                    "policy_effect": decision.effect.value,
                    "reason_code": error_code,
                },
            )
        )
        return SideEffectResult(
            execution_id=execution_id,
            project_id=request.project_id,
            request_id=request.request_id,
            status=SideEffectExecutionStatus.BLOCKED,
            component_kind=component_kind,
            component_id=component_id,
            operation=operation,
            error_code=error_code,
            error_message=error_message,
            policy_decision_id=decision.decision_id,
        )

    def _unavailable(
        self,
        request: AgentRunRequest,
        decision: PolicyDecision,
        component_kind: str,
        component_id: str,
        operation: str,
        message: str,
    ) -> SideEffectResult:
        execution_id = f"SIDE_EFFECT_UNAVAILABLE_{uuid4().hex}"
        self.store.append_audit_event(
            build_audit_event(
                project_id=request.project_id,
                category="SIDE_EFFECT",
                event_type="SIDE_EFFECT_FAILED",
                occurred_at=self._now(),
                resource_type="SideEffectExecution",
                resource_id=execution_id,
                severity="WARNING",
                correlation_id=request.request_id,
                details={
                    "request_id": request.request_id,
                    "agent_id": request.agent_id,
                    "capability_id": request.capability_id,
                    "component_kind": component_kind,
                    "component_id": component_id,
                    "operation": operation,
                    "error_code": "SIDE_EFFECT_COMPONENT_UNAVAILABLE",
                },
            )
        )
        return SideEffectResult(
            execution_id=execution_id,
            project_id=request.project_id,
            request_id=request.request_id,
            status=SideEffectExecutionStatus.FAILED,
            component_kind=component_kind,
            component_id=component_id,
            operation=operation,
            error_code="SIDE_EFFECT_COMPONENT_UNAVAILABLE",
            error_message=message,
            policy_decision_id=decision.decision_id,
        )

    def _replay_audit(
        self,
        record: SideEffectExecutionRecord,
        request: AgentRunRequest,
        decision: PolicyDecision,
        event_type: str,
        *,
        severity: str = "INFO",
    ):
        return build_audit_event(
            project_id=request.project_id,
            category="SIDE_EFFECT",
            event_type=event_type,
            occurred_at=self._now(),
            resource_type="SideEffectExecution",
            resource_id=record.execution_id,
            severity=severity,
            correlation_id=request.request_id,
            details={
                "request_id": request.request_id,
                "original_request_id": record.request_id,
                "agent_id": request.agent_id,
                "capability_id": request.capability_id,
                "capability_version": request.capability_version,
                "component_kind": record.component_kind,
                "component_id": record.component_id,
                "component_version": record.component_version,
                "operation": record.operation,
                "status": record.status.value,
                "policy_decision_id": decision.decision_id,
            },
        )

    def _audit_event(
        self,
        record: SideEffectExecutionRecord,
        event_type: str,
        at: datetime,
        *,
        severity: str = "INFO",
        details: dict | None = None,
    ):
        return build_audit_event(
            project_id=record.project_id,
            category="SIDE_EFFECT",
            event_type=event_type,
            occurred_at=at,
            resource_type="SideEffectExecution",
            resource_id=record.execution_id,
            severity=severity,
            correlation_id=record.request_id,
            details={
                "request_id": record.request_id,
                "agent_id": record.agent_id,
                "capability_id": record.capability_id,
                "capability_version": record.capability_version,
                "component_kind": record.component_kind,
                "component_id": record.component_id,
                "component_version": record.component_version,
                "operation": record.operation,
                "status": record.status.value,
                "policy_decision_id": record.policy_decision_id,
                **(details or {}),
            },
        )

    @staticmethod
    def _normalize_tool_result(result) -> tuple[dict, dict]:
        return dict(result.output), dict(result.metadata)

    @staticmethod
    def _normalize_provider_result(result) -> tuple[dict, dict]:
        return dict(result.payload), dict(result.metadata)

    @staticmethod
    def _signature(payload: dict, access_refs: tuple[AccessReference, ...]) -> str:
        encoded = json.dumps(
            {
                "payload": payload,
                "access_refs": [reference.uri for reference in access_refs],
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _execution_id(
        request: AgentRunRequest,
        component_kind: str,
        component_id: str,
        operation: str,
        idempotency_key: str | None,
    ) -> str:
        if idempotency_key is None:
            return f"SIDE_EFFECT_{uuid4().hex}"
        scope = "|".join(
            (
                request.project_id,
                request.agent_id,
                request.capability_id,
                request.capability_version,
                request.operation,
                component_kind,
                component_id,
                operation,
                idempotency_key,
            )
        )
        return f"SIDE_EFFECT_{hashlib.sha256(scope.encode('utf-8')).hexdigest()}"

    @staticmethod
    def _result_from_record(
        record: SideEffectExecutionRecord,
        *,
        replay: bool = False,
        error_code: str | None = None,
        error_message: str | None = None,
        force_status: SideEffectExecutionStatus | None = None,
        request_id: str | None = None,
        policy_decision_id: str | None = None,
    ) -> SideEffectResult:
        status = force_status or record.status
        if status == SideEffectExecutionStatus.PENDING:
            status = SideEffectExecutionStatus.BLOCKED
            error_code = error_code or "SIDE_EFFECT_IN_PROGRESS"
            error_message = error_message or "matching side-effect execution is still pending"
        return SideEffectResult(
            execution_id=record.execution_id,
            project_id=record.project_id,
            request_id=request_id or record.request_id,
            status=status,
            component_kind=record.component_kind,
            component_id=record.component_id,
            component_version=record.component_version,
            operation=record.operation,
            output=record.output,
            metadata=record.metadata,
            error_code=error_code or record.error_code,
            error_message=error_message or record.error_message,
            policy_decision_id=policy_decision_id or record.policy_decision_id,
            idempotent_replay=replay,
        )

    @staticmethod
    def _failure_result(
        record: SideEffectExecutionRecord,
        error_code: str,
        error_message: str,
        decision_id: str,
    ) -> SideEffectResult:
        return SideEffectResult(
            execution_id=record.execution_id,
            project_id=record.project_id,
            request_id=record.request_id,
            status=SideEffectExecutionStatus.FAILED,
            component_kind=record.component_kind,
            component_id=record.component_id,
            component_version=record.component_version,
            operation=record.operation,
            error_code=error_code,
            error_message=error_message,
            policy_decision_id=decision_id,
        )
