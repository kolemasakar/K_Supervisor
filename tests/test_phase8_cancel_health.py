from threading import Thread
from time import sleep

from models.enums import ExecutionStatus
from registry.agent_registry import AgentAvailability

from tests.phase8_support import build_runtime, make_request


def test_runtime_supports_cooperative_cancellation():
    agents, adapter, runtime = build_runtime()
    holder = {}

    def handler(request, control):
        while True:
            control.check_cancelled()
            sleep(0.002)

    adapter.register("A1", handler)

    def invoke():
        holder["result"] = runtime.dispatch(make_request(run_id="RUNC"))

    thread = Thread(target=invoke)
    thread.start()
    for _ in range(100):
        if runtime.cancel("RUNC"):
            break
        sleep(0.001)
    thread.join(timeout=1)

    result = holder["result"]
    assert result.status == ExecutionStatus.CANCELLED
    assert result.error is not None
    assert result.error.category == "CANCELLED"
    assert agents.availability("A1") == AgentAvailability.AVAILABLE


def test_repeated_runtime_failures_mark_agent_unavailable():
    agents, adapter, runtime = build_runtime(unavailable_after=2)

    def broken(request, control):
        raise RuntimeError("failure")

    adapter.register("A1", broken)
    first = runtime.dispatch(make_request(request_id="REQ1", run_id="RUN1"))
    second = runtime.dispatch(make_request(request_id="REQ2", run_id="RUN2"))

    assert first.status == ExecutionStatus.FAILED
    assert second.status == ExecutionStatus.FAILED
    assert agents.availability("A1") == AgentAvailability.UNAVAILABLE
