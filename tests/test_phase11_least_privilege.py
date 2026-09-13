import pytest

from access import AccessReference
from models.enums import ExecutionStatus
from policy.access_permissions import require_access_reference
from policy.contracts import LeastPrivilegeExecutionContext
from policy.tool_permissions import require_tool_operation

from tests.phase11_support import build_policy_stack, register_success


def test_workflow_policy_can_only_narrow_project_permissions(tmp_path):
    project_policy = {
        "agent_tool_permissions": {
            "agent.policy": {
                "repo.read": ["read"],
                "repo.write": ["write"],
            }
        },
        "allowed_access_refs": [
            "secret://project/P11/read",
            "secret://project/P11/write",
        ],
    }
    stack = build_policy_stack(tmp_path, policy=project_policy)
    store, _, _, delegate, _, _, kernel, requirement = stack
    calls = []
    register_success(delegate, calls)

    run_policy = {
        "tools": {"repo.read": ["read"]},
        "access_refs": ["secret://project/P11/read"],
        "workflow_constraints": {
            "agent_tool_permissions": {"agent.policy": {"repo.read": ["read"]}},
            "allowed_access_refs": ["secret://project/P11/read"],
        },
    }
    result = kernel.run_task("P11", "least privilege", requirement, {}, policy=run_policy)
    assert result.status == ExecutionStatus.SUCCEEDED
    raw_context = calls[0].policy["execution_context"]
    context = LeastPrivilegeExecutionContext.model_validate(raw_context)
    assert context.tool_permissions == {"repo.read": ["read"]}
    assert context.access_refs == ("secret://project/P11/read",)

    require_tool_operation(context, "repo.read", "read")
    with pytest.raises(PermissionError):
        require_tool_operation(context, "repo.write", "write")
    require_access_reference(context, AccessReference(uri="secret://project/P11/read"))
    with pytest.raises(PermissionError):
        require_access_reference(context, AccessReference(uri="secret://project/P11/write"))
    store.close()
