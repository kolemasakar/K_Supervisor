from persistence import SQLitePersistenceStore

from tests.phase11_support import build_policy_stack, register_success


def test_policy_decisions_survive_store_restart(tmp_path):
    stack = build_policy_stack(tmp_path)
    store, _, _, delegate, _, _, kernel, requirement = stack
    calls = []
    register_success(delegate, calls)
    kernel.run_task("P11", "audited operation", requirement, {})
    assert store.list_policy_decisions("P11")
    store.close()

    reopened = SQLitePersistenceStore(tmp_path / "state.db")
    reopened.initialize()
    decisions = reopened.list_policy_decisions("P11")
    assert decisions
    assert decisions[-1].effect.value == "ALLOW"
    reopened.close()
