from models.enums import ExecutionStatus, ProjectOperationalState
from policy.contracts import ApprovalStatus

from tests.phase11_support import LATER, build_policy_stack, register_success


def test_material_permission_scope_requires_owner_approval(tmp_path):
    stack = build_policy_stack(
        tmp_path,
        side_effects=("CREATE_RESOURCE",),
        risk_class="HIGH",
    )
    store, projects, _, delegate, approval, _, kernel, requirement = stack
    calls = []
    register_success(delegate, calls)

    blocked = kernel.run_task("P11", "create resource", requirement, {})
    assert blocked.status == ExecutionStatus.BLOCKED
    assert calls == []
    assert projects.get("P11").operational_state == ProjectOperationalState.WAITING_FOR_OWNER

    approval_id = blocked.error.details["approval_id"]
    pending = store.get_approval(approval_id)
    assert pending is not None
    assert pending.status == ApprovalStatus.PENDING
    assert pending.human_action_id is not None

    approved = approval.approve(approval_id, LATER)
    assert approved.status == ApprovalStatus.APPROVED
    assert projects.get("P11").operational_state == ProjectOperationalState.ACTIVE

    result = kernel.run_task("P11", "create resource after approval", requirement, {})
    assert result.status == ExecutionStatus.SUCCEEDED
    assert len(calls) == 1
    assert calls[0].policy["effect"] == "ALLOW"
    assert calls[0].policy["execution_context"]["approval_id"] == approval_id

    effects = [item.effect.value for item in store.list_policy_decisions("P11")]
    assert "REQUIRE_APPROVAL" in effects
    assert effects[-1] == "ALLOW"
    store.close()
