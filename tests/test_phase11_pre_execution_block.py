from models.enums import ExecutionStatus

from tests.phase11_support import build_policy_stack, register_success


def test_denied_side_effect_is_blocked_before_agent_execution(tmp_path):
    stack = build_policy_stack(
        tmp_path,
        side_effects=("DELETE_RESOURCE",),
        risk_class="CRITICAL",
        policy={"denied_side_effects": ["DELETE_RESOURCE"]},
    )
    store, _, _, delegate, _, _, kernel, requirement = stack
    calls = []
    register_success(delegate, calls)

    result = kernel.run_task("P11", "denied operation", requirement, {})

    assert result.status == ExecutionStatus.BLOCKED
    assert result.error is not None
    assert result.error.category == "POLICY_BLOCKED"
    assert result.error.code == "SIDE_EFFECT_DENIED"
    assert calls == []
    assert store.list_tasks("P11")[-1].status == "BLOCKED"
    decisions = store.list_policy_decisions("P11")
    assert decisions[-1].effect.value == "DENY"
    assert decisions[-1].reason_code == "SIDE_EFFECT_DENIED"
    store.close()
