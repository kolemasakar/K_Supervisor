from models.enums import ExecutionStatus
from registry.agent_registry import AgentAvailability

from tests.phase8_support import build_runtime, make_request, success


def test_runtime_success_restores_availability():
    agents, adapter, runtime = build_runtime()
    adapter.register("A1", lambda request, control: success(request))

    result = runtime.dispatch(make_request())

    assert result.status == ExecutionStatus.SUCCEEDED
    assert agents.availability("A1") == AgentAvailability.AVAILABLE


def test_runtime_exception_is_normalized():
    agents, adapter, runtime = build_runtime()

    def broken(request, control):
        raise ValueError("boom")

    adapter.register("A1", broken)
    result = runtime.dispatch(make_request())

    assert result.status == ExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.category == "EXECUTION_ERROR"
    assert result.error.retryable is False
    assert agents.availability("A1") == AgentAvailability.DEGRADED
