from models.enums import ExecutionStatus

from tests.phase8_support import build_runtime, make_request, success


def test_idempotency_replay_preserves_new_correlation_ids():
    _, adapter, runtime = build_runtime()
    calls = {"count": 0}

    def handler(request, control):
        calls["count"] += 1
        return success(request, {"call": calls["count"]})

    adapter.register("A1", handler)
    first = runtime.dispatch(make_request(key="K1", request_id="REQ1", run_id="RUN1"))
    second = runtime.dispatch(make_request(key="K1", request_id="REQ2", run_id="RUN2"))

    assert first.status == ExecutionStatus.SUCCEEDED
    assert second.status == ExecutionStatus.SUCCEEDED
    assert calls["count"] == 1
    assert second.request_id == "REQ2"
    assert second.run_id == "RUN2"
    assert second.output == {"call": 1}
    assert second.metadata["idempotent_replay"] is True


def test_idempotency_key_rejects_different_input():
    _, adapter, runtime = build_runtime()
    adapter.register("A1", lambda request, control: success(request))
    runtime.dispatch(make_request(key="K1", input_data={"value": 1}))

    result = runtime.dispatch(
        make_request(key="K1", request_id="REQ2", run_id="RUN2", input_data={"value": 2})
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.category == "VALIDATION_ERROR"
