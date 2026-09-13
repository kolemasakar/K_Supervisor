from models.agent import AgentRunResult
from models.enums import ExecutionStatus
from runtime import RuntimeProviderError

from tests.phase8_support import build_runtime, make_request, success


def test_provider_error_is_retryable():
    _, adapter, runtime = build_runtime()

    def unavailable(request, control):
        raise RuntimeProviderError("provider unavailable")

    adapter.register("A1", unavailable)
    result = runtime.dispatch(make_request())

    assert result.status == ExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.category == "PROVIDER_ERROR"
    assert result.error.retryable is True


def test_runtime_rejects_result_with_wrong_correlation():
    _, adapter, runtime = build_runtime()

    def wrong(request, control):
        value = success(request)
        return AgentRunResult(**{**value.model_dump(), "request_id": "WRONG"})

    adapter.register("A1", wrong)
    result = runtime.dispatch(make_request())

    assert result.status == ExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.category == "VALIDATION_ERROR"
    assert result.request_id == "REQ1"
