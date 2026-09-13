from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import field_validator

from models.base import ContractModel, JsonObject, ensure_tz


class PolicyEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class RiskClass(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SideEffect(StrEnum):
    NONE = "NONE"
    READ_EXTERNAL = "READ_EXTERNAL"
    WRITE_EXTERNAL = "WRITE_EXTERNAL"
    SEND_MESSAGE = "SEND_MESSAGE"
    CREATE_RESOURCE = "CREATE_RESOURCE"
    MODIFY_RESOURCE = "MODIFY_RESOURCE"
    DELETE_RESOURCE = "DELETE_RESOURCE"
    EXECUTE_CODE = "EXECUTE_CODE"


class PermissionGrant(ContractModel):
    side_effects: tuple[SideEffect, ...] = (SideEffect.NONE,)
    tools: JsonObject = {}
    access_refs: tuple[str, ...] = ()


class PolicyConstraints(ContractModel):
    denied_capabilities: tuple[str, ...] = ()
    allowed_capabilities: tuple[str, ...] = ()
    allowed_side_effects: tuple[SideEffect, ...] = (SideEffect.NONE, SideEffect.READ_EXTERNAL)
    approval_side_effects: tuple[SideEffect, ...] = (
        SideEffect.WRITE_EXTERNAL,
        SideEffect.SEND_MESSAGE,
        SideEffect.CREATE_RESOURCE,
        SideEffect.MODIFY_RESOURCE,
        SideEffect.DELETE_RESOURCE,
        SideEffect.EXECUTE_CODE,
    )
    denied_side_effects: tuple[SideEffect, ...] = ()
    agent_tool_permissions: JsonObject = {}
    allowed_access_refs: tuple[str, ...] = ()
    approval_risk_classes: tuple[RiskClass, ...] = (RiskClass.HIGH, RiskClass.CRITICAL)


class LeastPrivilegeExecutionContext(ContractModel):
    project_id: str
    agent_id: str
    capability_id: str
    operation: str
    side_effects: tuple[SideEffect, ...]
    tool_permissions: JsonObject = {}
    access_refs: tuple[str, ...] = ()
    approval_id: str | None = None


class PolicyDecision(ContractModel):
    decision_id: str
    project_id: str
    request_id: str
    effect: PolicyEffect
    reason_code: str
    reason: str
    risk_class: RiskClass
    evaluated_at: datetime
    execution_context: LeastPrivilegeExecutionContext | None = None
    approval_id: str | None = None
    metadata: JsonObject = {}

    @field_validator("evaluated_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        return ensure_tz(value)


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRecord(ContractModel):
    approval_id: str
    project_id: str
    human_action_id: str | None = None
    scope_hash: str
    requested_permissions: PermissionGrant
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime
    decided_at: datetime | None = None
    metadata: JsonObject = {}

    @field_validator("created_at", "decided_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_tz(value)
