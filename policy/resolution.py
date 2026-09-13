from __future__ import annotations

import hashlib
import json

from models.agent import AgentRunRequest
from models.project import ProjectSpec

from .contracts import PermissionGrant, PolicyConstraints, RiskClass, SideEffect


def _side_effects(values) -> tuple[SideEffect, ...]:
    return tuple(dict.fromkeys(SideEffect(value) for value in values))


def _risk_classes(values) -> tuple[RiskClass, ...]:
    return tuple(dict.fromkeys(RiskClass(value) for value in values))


def constraints_from_spec(spec: ProjectSpec | None) -> PolicyConstraints:
    if spec is None:
        return PolicyConstraints()
    raw = spec.autonomy.get("policy", spec.autonomy)
    known = {
        "denied_capabilities",
        "allowed_capabilities",
        "allowed_side_effects",
        "approval_side_effects",
        "denied_side_effects",
        "agent_tool_permissions",
        "allowed_access_refs",
        "approval_risk_classes",
    }
    data = {key: raw[key] for key in known if key in raw}
    return PolicyConstraints.model_validate(data)


def apply_workflow_constraints(
    base: PolicyConstraints,
    patch: dict | None,
) -> PolicyConstraints:
    if not patch:
        return base
    data = base.model_dump(mode="python")
    data["denied_capabilities"] = tuple(
        dict.fromkeys((*base.denied_capabilities, *patch.get("denied_capabilities", ())))
    )
    if "allowed_capabilities" in patch:
        requested = set(patch["allowed_capabilities"])
        current = set(base.allowed_capabilities)
        data["allowed_capabilities"] = tuple(sorted(requested if not current else current & requested))
    if "allowed_side_effects" in patch:
        requested = set(_side_effects(patch["allowed_side_effects"]))
        data["allowed_side_effects"] = tuple(
            item for item in base.allowed_side_effects if item in requested
        )
    data["denied_side_effects"] = tuple(
        dict.fromkeys((*base.denied_side_effects, *_side_effects(patch.get("denied_side_effects", ()))))
    )
    data["approval_side_effects"] = tuple(
        dict.fromkeys((*base.approval_side_effects, *_side_effects(patch.get("approval_side_effects", ()))))
    )
    if "allowed_access_refs" in patch:
        requested = set(patch["allowed_access_refs"])
        data["allowed_access_refs"] = tuple(
            item for item in base.allowed_access_refs if item in requested
        )
    if "approval_risk_classes" in patch:
        data["approval_risk_classes"] = tuple(
            dict.fromkeys((*base.approval_risk_classes, *_risk_classes(patch["approval_risk_classes"])))
        )
    if "agent_tool_permissions" in patch:
        data["agent_tool_permissions"] = intersect_tool_permissions(
            base.agent_tool_permissions,
            patch["agent_tool_permissions"],
        )
    return PolicyConstraints.model_validate(data)


def intersect_tool_permissions(base: dict, patch: dict) -> dict:
    if not base:
        return {}
    result: dict[str, dict[str, tuple[str, ...]]] = {}
    for agent_id, tools in base.items():
        patch_tools = patch.get(agent_id, {})
        allowed: dict[str, tuple[str, ...]] = {}
        for tool_id, operations in tools.items():
            if tool_id not in patch_tools:
                continue
            intersection = tuple(sorted(set(operations) & set(patch_tools[tool_id])))
            if intersection:
                allowed[tool_id] = intersection
        if allowed:
            result[agent_id] = allowed
    return result


def requested_permissions(
    request: AgentRunRequest,
    declared_side_effects: tuple[str, ...],
) -> PermissionGrant:
    raw = request.policy or {}
    side_effects = raw.get("side_effects", declared_side_effects)
    declared = {SideEffect(value) for value in declared_side_effects}
    requested = _side_effects(side_effects)
    if not set(requested).issubset(declared):
        raise ValueError("requested side effects exceed capability declaration")
    return PermissionGrant(
        side_effects=requested,
        tools=raw.get("tools", {}),
        access_refs=tuple(raw.get("access_refs", ())),
    )


def permission_scope_hash(
    request: AgentRunRequest,
    grant: PermissionGrant,
    risk_class: RiskClass,
) -> str:
    payload = {
        "project_id": request.project_id,
        "agent_id": request.agent_id,
        "capability_id": request.capability_id,
        "capability_version": request.capability_version,
        "operation": request.operation,
        "risk_class": risk_class.value,
        "permissions": grant.model_dump(mode="json"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
