from time import sleep

from models.enums import ExecutionStatus
from registry.agent_registry import AgentAvailability

from tests.phase8_support import build_runtime, make_request, success


def test_runtime_timeout_is_normalized():
    agents, adapter, runtime = build_runtime()

    def slow(request, control):
        sleep(0.05)
        return success(request)

    adapter.register("A1", slow)
    result = runtime.dispatch(make_request(limits={"timeout_seconds": 0.01}))

    assert result.status == ExecutionStatus.TIMED_OUT
    assert result.error is not None
    assert result.error.category == "TIMEOUT"
    assert result.error.retryable is True
    assert agents.availability("A1") == AgentAvailability.DEGRADED


def test_resource_limit_is_enforced_cooperatively():
    agents, adapter, runtime = build_runtime()

    def limited(request, control):
        control.consume("tokens", 2)
        return success(request)

    adapter.register("A1", limited)
    result = runtime.dispatch(make_request(limits={"max_tokens": 1}))

    assert result.status == ExecutionStatus.BLOCKED
    assert result.error is not None
    assert result.error.category == "POLICY_BLOCKED"
    assert agents.availability("A1") == AgentAvailability.AVAILABLE
