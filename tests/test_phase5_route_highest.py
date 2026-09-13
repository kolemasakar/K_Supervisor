from models.enums import ExecutionStatus
from tests.phase5_support import build_stack, make_agent, make_requirement, success


def test_route_highest(tmp_path):
    store, _, agents, dispatcher, kernel = build_stack(tmp_path, ("1.0.0", "1.5.0"))
    agents.register(make_agent("agent.old", "1.0.0"))
    agents.register(make_agent("agent.new", "1.5.0"))
    dispatcher.register("agent.old", success)
    dispatcher.register("agent.new", success)
    result = kernel.run_task("P1", "analyze", make_requirement(), {"value": 1})
    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.agent_id == "agent.new"
    assert store.list_tasks("P1")[0].status == "SUCCEEDED"
    store.close()
