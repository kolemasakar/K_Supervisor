import os
from threading import Thread
from time import monotonic, sleep

from models.enums import ExecutionStatus
from registry import AgentRegistry, CapabilityRegistry
from registry.agent_registry import AgentAvailability
from runtime import AgentRuntimeDispatcher, ProcessRuntimeAdapter
from tests.phase5_support import make_agent, make_capability
from tests.phase8_support import make_request, success


def isolated_success(request, control):
    control.consume("tokens", 2)
    return success(request, {"pid": os.getpid()})


def isolated_unresponsive(request, control):
    while True:
        sleep(0.01)


def isolated_crash(request, control):
    os._exit(17)


def isolated_limit(request, control):
    control.consume("tokens", 2)
    return success(request)


def build_runtime(**adapter_kwargs):
    capabilities = CapabilityRegistry()
    capabilities.register(make_capability())
    agents = AgentRegistry(capabilities)
    agents.register(make_agent("A1"))
    adapter = ProcessRuntimeAdapter(**adapter_kwargs)
    runtime = AgentRuntimeDispatcher(agents, adapter)
    return agents, adapter, runtime


def test_process_runtime_executes_in_distinct_process_and_propagates_usage():
    agents, adapter, runtime = build_runtime()
    adapter.register("A1", isolated_success)
    parent_pid = os.getpid()

    result = runtime.dispatch(make_request(limits={"max_tokens": 3}))

    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.output["pid"] != parent_pid
    assert result.metrics["runtime_usage"]["tokens"] == 2.0
    assert adapter.active_worker_count == 0
    assert agents.availability("A1") == AgentAvailability.AVAILABLE


def test_unresponsive_worker_timeout_is_bounded_and_cleaned_up():
    _, adapter, runtime = build_runtime(
        cancellation_grace_seconds=0.01,
        termination_grace_seconds=0.05,
        kill_grace_seconds=0.05,
    )
    adapter.register("A1", isolated_unresponsive)
    started = monotonic()
    result = runtime.dispatch(make_request(limits={"timeout_seconds": 0.03}))
    elapsed = monotonic() - started

    assert result.status == ExecutionStatus.TIMED_OUT
    assert result.error is not None
    assert result.error.category == "TIMEOUT"
    assert elapsed < 0.75
    assert adapter.active_worker_count == 0


def test_unresponsive_worker_cancel_escalates_and_finishes():
    _, adapter, runtime = build_runtime(
        cancellation_grace_seconds=0.01,
        termination_grace_seconds=0.05,
        kill_grace_seconds=0.05,
    )
    adapter.register("A1", isolated_unresponsive)
    holder = {}

    thread = Thread(
        target=lambda: holder.setdefault(
            "result", runtime.dispatch(make_request(run_id="ISO-CANCEL"))
        )
    )
    thread.start()
    for _ in range(200):
        if runtime.cancel("ISO-CANCEL"):
            break
        sleep(0.002)
    thread.join(timeout=1)

    assert not thread.is_alive()
    assert holder["result"].status == ExecutionStatus.CANCELLED
    assert holder["result"].error is not None
    assert holder["result"].error.category == "CANCELLED"
    assert adapter.active_worker_count == 0


def test_worker_crash_is_contained_and_normalized():
    agents, adapter, runtime = build_runtime()
    adapter.register("A1", isolated_crash)

    result = runtime.dispatch(make_request(run_id="ISO-CRASH"))

    assert result.status == ExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "RUNTIME_WORKER_CRASH"
    assert result.error.category == "WORKER_CRASH"
    assert result.error.retryable is True
    assert adapter.active_worker_count == 0
    assert agents.availability("A1") == AgentAvailability.DEGRADED


def test_runtime_limit_error_survives_process_boundary():
    _, adapter, runtime = build_runtime()
    adapter.register("A1", isolated_limit)

    result = runtime.dispatch(make_request(limits={"max_tokens": 1}))

    assert result.status == ExecutionStatus.BLOCKED
    assert result.error is not None
    assert result.error.code == "RUNTIME_LIMIT_EXCEEDED"
    assert result.error.category == "POLICY_BLOCKED"
    assert adapter.active_worker_count == 0


def test_worker_failure_does_not_poison_next_run():
    _, adapter, runtime = build_runtime()
    adapter.register("A1", isolated_crash)
    failed = runtime.dispatch(make_request(run_id="ISO-FAIL", request_id="REQ-FAIL"))
    assert failed.status == ExecutionStatus.FAILED

    adapter.register("A1", isolated_success)
    recovered = runtime.dispatch(
        make_request(
            run_id="ISO-OK",
            request_id="REQ-OK",
            limits={"max_tokens": 3},
        )
    )
    assert recovered.status == ExecutionStatus.SUCCEEDED
    assert adapter.active_worker_count == 0
