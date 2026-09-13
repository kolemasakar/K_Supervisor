from __future__ import annotations

from .contracts import LeastPrivilegeExecutionContext


def tool_operation_allowed(
    context: LeastPrivilegeExecutionContext,
    tool_id: str,
    operation: str,
) -> bool:
    return operation in context.tool_permissions.get(tool_id, ())


def require_tool_operation(
    context: LeastPrivilegeExecutionContext,
    tool_id: str,
    operation: str,
) -> None:
    if not tool_operation_allowed(context, tool_id, operation):
        raise PermissionError(f"tool operation is not permitted: {tool_id}:{operation}")
