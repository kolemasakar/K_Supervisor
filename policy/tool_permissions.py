from __future__ import annotations

from .contracts import LeastPrivilegeExecutionContext


def tool_operation_allowed(
    context: LeastPrivilegeExecutionContext,
    tool_id: str,
    operation: str,
) -> bool:
    return operation in context.tool_permissions.get(tool_id, ())
