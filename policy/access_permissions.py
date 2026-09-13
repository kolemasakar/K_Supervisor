from __future__ import annotations

from access import AccessReference

from .contracts import LeastPrivilegeExecutionContext


def access_reference_allowed(
    context: LeastPrivilegeExecutionContext,
    reference: AccessReference,
) -> bool:
    return reference.uri in context.access_refs


def require_access_reference(
    context: LeastPrivilegeExecutionContext,
    reference: AccessReference,
) -> None:
    if not access_reference_allowed(context, reference):
        raise PermissionError("access reference is outside least-privilege context")
