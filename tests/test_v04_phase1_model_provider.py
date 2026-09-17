from __future__ import annotations

from dataclasses import dataclass

import pytest

from access import AccessReference, EnvironmentSecretBackend, environment_key
from integrations import AvailabilityState
from integrations.gateway import SideEffectGateway
from models.agent import AgentRunRequest
from models.side_effect import SideEffectExecutionStatus
from policy.contracts import ApprovalStatus
from providers import (
    ModelProfile,
    OpenAIResponsesProvider,
    OpenAITransportCancelled,
    OpenAITransportNetworkError,
    OpenAITransportResponse,
    OpenAITransportTimeout,
    ProviderExecutionError,
    ProviderRequest,
)
from providers.model_hook import model_candidates
from registry import ProviderRegistry
from tests.phase11_support import LATER, NOW, build_policy_stack

CREDENTIAL = AccessReference(uri="secret://project/P11/openai")
MODEL = ModelProfile(model_id="configured-model", features=("text",), context_window=128000)


@dataclass
class Call:
    api_key: str
    body: dict
    connect_timeout_seconds: float
    request_timeout_seconds: float
    idempotency_key: str | None


class FakeTransport:
    def __init__(self, outcomes=None):
        self.outcomes = list(outcomes or [success_response()])
        self.calls: list[Call] = []

    def create_response(
        self,
        *,
        api_key,
        body,
        connect_timeout_seconds,
        request_timeout_seconds,
        idempotency_key,
    ):
        self.calls.append(
            Call(
                api_key=api_key,
                body=dict(body),
                connect_timeout_seconds=connect_timeout_seconds,
                request_timeout_seconds=request_timeout_seconds,
                idempotency_key=idempotency_key,
            )
        )
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def success_response(*, text="hello", status="completed", usage=None):
    payload = {
        "id": "resp_123",
        "model": "configured-model",
        "status": status,
        "output_text": text,
        "usage": usage or {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
    }
    return OpenAITransportResponse(status_code=200, payload=payload, request_id="req_openai_123")


def backend(value="sk-test-secret"):
    return EnvironmentSecretBackend({environment_key(CREDENTIAL): value})


def provider(*, transport=None, secret_backend=None, **kwargs):
    return OpenAIResponsesProvider(
        secret_backend=secret_backend or backend(),
        credential_ref=CREDENTIAL,
        models=(MODEL,),
        default_model=MODEL.model_id,
        transport=transport or FakeTransport(),
        **kwargs,
    )


def direct_request(*, payload=None, refs=(CREDENTIAL,), key="idem-provider"):
    return ProviderRequest(
        project_id="P11",
        operation="generate",
        payload=payload or {"input": "say hello"},
        access_refs=refs,
        request_id="REQ_PHASE1",
        agent_id="agent.policy",
        capability_id="policy.test",
        capability_version="1.0.0",
        idempotency_key=key,
    )


def agent_request(*, policy=None, request_id="REQ_PHASE1", key="idem-provider"):
    return AgentRunRequest(
        request_id=request_id,
        project_id="P11",
        task_id="TASK_PHASE1",
        workflow_run_id="WF_PHASE1",
        run_id=f"RUN_{request_id}",
        agent_id="agent.policy",
        capability_id="policy.test",
        capability_version="1.0.0",
        operation="run",
        input={"prompt": "say hello"},
        policy=policy or {},
        idempotency_key=key,
    )


def allowed_stack(tmp_path, *, approval=False):
    policy = {
        "allowed_side_effects": [] if approval else ["WRITE_EXTERNAL"],
        "approval_side_effects": ["WRITE_EXTERNAL"] if approval else [],
        "approval_risk_classes": [],
        "allowed_access_refs": [CREDENTIAL.uri],
    }
    return build_policy_stack(
        tmp_path,
        side_effects=("WRITE_EXTERNAL",),
        risk_class="LOW",
        policy=policy,
    )


def register(provider_instance):
    registry = ProviderRegistry()
    registry.register(provider_instance)
    return registry


def test_provider_descriptor_availability_and_model_candidate_projection():
    transport = FakeTransport()
    item = provider(transport=transport)
    assert item.descriptor.provider_id == "openai.responses"
    assert item.descriptor.version == "1.0"
    assert item.descriptor.provider_type == "MODEL"
    assert item.descriptor.operations == ("generate",)
    assert item.check_availability().state == AvailabilityState.AVAILABLE

    candidates = model_candidates(register(item))
    assert candidates == (
        {
            "provider_id": "openai.responses",
            "provider_version": "1.0",
            "model_id": "configured-model",
            "features": ("text",),
            "context_window": 128000,
            "priority": 0,
        },
    )


def test_missing_credential_is_unavailable_and_fails_without_transport_call():
    missing = EnvironmentSecretBackend({})
    transport = FakeTransport()
    item = provider(transport=transport, secret_backend=missing)
    assert item.check_availability().state == AvailabilityState.UNAVAILABLE

    with pytest.raises(ProviderExecutionError) as captured:
        item.execute(direct_request())
    assert captured.value.code == "PROVIDER_CONFIGURATION_ERROR"
    assert "secret" not in str(captured.value).lower()
    assert transport.calls == []


def test_credential_must_be_authorized_in_provider_request_before_resolution():
    transport = FakeTransport()
    item = provider(transport=transport)
    with pytest.raises(ProviderExecutionError) as captured:
        item.execute(direct_request(refs=()))
    assert captured.value.code == "PROVIDER_CONFIGURATION_ERROR"
    assert transport.calls == []


def test_outbound_request_is_stateless_bounded_and_contains_no_provider_tools():
    transport = FakeTransport()
    item = provider(transport=transport, default_max_output_tokens=777, max_output_tokens_limit=1000)
    result = item.execute(
        direct_request(payload={"input": "hello", "instructions": "concise", "max_output_tokens": 900})
    )

    assert result.payload == {"text": "hello"}
    call = transport.calls[0]
    assert call.api_key == "sk-test-secret"
    assert call.body == {
        "model": "configured-model",
        "input": "hello",
        "instructions": "concise",
        "max_output_tokens": 900,
        "store": False,
    }
    assert "tools" not in call.body
    assert "previous_response_id" not in call.body
    assert "background" not in call.body
    assert call.connect_timeout_seconds == 5.0
    assert call.request_timeout_seconds == 60.0
    assert call.idempotency_key == "idem-provider"


def test_model_is_configurable_but_must_be_in_configured_provider_set():
    second = ModelProfile(model_id="configured-model-2", features=("text",))
    transport = FakeTransport(
        [OpenAITransportResponse(status_code=200, payload={
            "id": "resp_2",
            "model": "configured-model-2",
            "status": "completed",
            "output_text": "ok",
            "usage": {},
        })]
    )
    item = OpenAIResponsesProvider(
        secret_backend=backend(),
        credential_ref=CREDENTIAL,
        models=(MODEL, second),
        default_model=MODEL.model_id,
        transport=transport,
    )
    result = item.execute(direct_request(payload={"model": second.model_id, "input": "hello"}))
    assert result.metadata["model"] == second.model_id
    assert transport.calls[0].body["model"] == second.model_id

    with pytest.raises(ProviderExecutionError) as captured:
        item.execute(direct_request(payload={"model": "not-configured", "input": "hello"}))
    assert captured.value.code == "PROVIDER_INVALID_REQUEST"


def test_unknown_provider_native_fields_fail_closed():
    item = provider()
    with pytest.raises(ProviderExecutionError) as captured:
        item.execute(direct_request(payload={"input": "hello", "tools": [{"type": "web_search"}]}))
    assert captured.value.code == "PROVIDER_INVALID_REQUEST"


def test_output_token_bound_is_enforced_before_transport():
    transport = FakeTransport()
    item = provider(transport=transport, default_max_output_tokens=50, max_output_tokens_limit=100)
    with pytest.raises(ProviderExecutionError) as captured:
        item.execute(direct_request(payload={"input": "hello", "max_output_tokens": 101}))
    assert captured.value.code == "PROVIDER_INVALID_REQUEST"
    assert transport.calls == []


def test_success_normalizes_text_identity_status_and_usage():
    item = provider()
    result = item.execute(direct_request())
    assert result.payload == {"text": "hello"}
    assert result.metadata == {
        "provider_response_id": "resp_123",
        "model": "configured-model",
        "status": "completed",
        "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
        "provider_request_id": "req_openai_123",
    }


def test_output_array_fallback_is_supported_without_reasoning_persistence():
    response = OpenAITransportResponse(
        status_code=200,
        payload={
            "id": "resp_array",
            "model": "configured-model",
            "status": "completed",
            "output": [
                {"type": "reasoning", "summary": [{"text": "do not persist me"}]},
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "part 1"},
                        {"type": "output_text", "text": " part 2"},
                    ],
                },
            ],
            "usage": {"input_tokens": 1, "output_tokens": 4, "total_tokens": 5},
        },
    )
    result = provider(transport=FakeTransport([response])).execute(direct_request())
    assert result.payload == {"text": "part 1 part 2"}
    assert "reasoning" not in repr(result.model_dump())


@pytest.mark.parametrize(
    ("outcome", "code", "category", "retryable"),
    [
        (OpenAITransportTimeout("timeout"), "PROVIDER_TIMEOUT", "timeout", True),
        (OpenAITransportCancelled("cancelled"), "PROVIDER_CANCELLED", "cancellation", False),
        (OpenAITransportNetworkError("network"), "PROVIDER_TRANSIENT_ERROR", "transient", True),
        (OpenAITransportResponse(401, {"error": {"code": "invalid_api_key", "message": "raw"}}), "PROVIDER_AUTHENTICATION_ERROR", "authentication", False),
        (OpenAITransportResponse(400, {"error": {"code": "invalid_request_error", "message": "raw"}}), "PROVIDER_INVALID_REQUEST", "invalid_request", False),
        (OpenAITransportResponse(429, {"error": {"code": "rate_limit_exceeded", "message": "raw"}}), "PROVIDER_RATE_LIMITED", "rate_limit", True),
        (OpenAITransportResponse(503, {"error": {"code": "server_error", "message": "raw"}}), "PROVIDER_TRANSIENT_ERROR", "transient", True),
        (OpenAITransportResponse(501, {"error": {"code": "not_implemented", "message": "raw"}}), "PROVIDER_FAILURE", "provider_failure", False),
    ],
)
def test_failure_taxonomy_is_safe_and_typed(outcome, code, category, retryable):
    item = provider(transport=FakeTransport([outcome]))
    with pytest.raises(ProviderExecutionError) as captured:
        item.execute(direct_request(key=None))
    error = captured.value
    assert error.code == code
    assert error.category == category
    assert error.retryable is retryable
    assert "sk-test-secret" not in str(error)
    assert "raw" not in str(error)


def test_malformed_and_incomplete_responses_are_not_success():
    malformed = OpenAITransportResponse(
        200,
        {"id": "resp_bad", "model": "configured-model", "status": "completed", "output": []},
    )
    with pytest.raises(ProviderExecutionError) as malformed_error:
        provider(transport=FakeTransport([malformed])).execute(direct_request())
    assert malformed_error.value.code == "PROVIDER_MALFORMED_RESPONSE"

    incomplete = OpenAITransportResponse(
        200,
        {
            "id": "resp_inc",
            "model": "configured-model",
            "status": "incomplete",
            "incomplete_details": {"reason": "max_output_tokens"},
        },
    )
    with pytest.raises(ProviderExecutionError) as incomplete_error:
        provider(transport=FakeTransport([incomplete])).execute(direct_request())
    assert incomplete_error.value.code == "PROVIDER_FAILURE"
    assert incomplete_error.value.provider_code == "max_output_tokens"


def test_retry_is_bounded_and_requires_idempotency_key():
    transient = OpenAITransportResponse(503, {"error": {"code": "server_error"}})
    transport = FakeTransport([transient, transient, success_response(text="recovered")])
    item = provider(transport=transport, max_retries=2)
    result = item.execute(direct_request(key="same-key"))
    assert result.payload == {"text": "recovered"}
    assert len(transport.calls) == 3
    assert {call.idempotency_key for call in transport.calls} == {"same-key"}

    no_key_transport = FakeTransport([transient, success_response()])
    no_key_item = provider(transport=no_key_transport, max_retries=2)
    with pytest.raises(ProviderExecutionError) as captured:
        no_key_item.execute(direct_request(key=None))
    assert captured.value.retryable
    assert len(no_key_transport.calls) == 1


def test_gateway_allow_invokes_once_and_persists_only_safe_metadata(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    transport = FakeTransport()
    item = provider(transport=transport)
    gateway = SideEffectGateway(store, engine, providers=register(item))
    run = agent_request(policy={"access_refs": [CREDENTIAL.uri]})

    result = gateway.execute_provider(
        run,
        "openai.responses",
        "generate",
        {"input": "hello"},
        access_refs=(CREDENTIAL,),
    )

    assert result.status == SideEffectExecutionStatus.SUCCEEDED
    assert result.output == {"text": "hello"}
    assert len(transport.calls) == 1
    record = store.list_side_effect_executions("P11")[-1]
    serialized = repr(record.model_dump())
    assert "sk-test-secret" not in serialized
    assert CREDENTIAL.uri not in record.signature
    assert "sk-test-secret" not in repr(store.list_audit_events("P11"))
    store.close()


def test_gateway_deny_and_missing_access_authorization_make_zero_transport_calls(tmp_path):
    denied = build_policy_stack(
        tmp_path,
        side_effects=("WRITE_EXTERNAL",),
        risk_class="LOW",
        policy={"denied_side_effects": ["WRITE_EXTERNAL"], "allowed_access_refs": [CREDENTIAL.uri]},
    )
    store, _, _, _, _, engine, _, _ = denied
    transport = FakeTransport()
    gateway = SideEffectGateway(store, engine, providers=register(provider(transport=transport)))
    result = gateway.execute_provider(
        agent_request(policy={"access_refs": [CREDENTIAL.uri]}),
        "openai.responses",
        "generate",
        {"input": "hello"},
        access_refs=(CREDENTIAL,),
    )
    assert result.status == SideEffectExecutionStatus.BLOCKED
    assert transport.calls == []
    store.close()


def test_gateway_require_approval_invokes_only_after_valid_approval(tmp_path):
    store, _, _, _, approval, engine, _, _ = allowed_stack(tmp_path, approval=True)
    transport = FakeTransport()
    gateway = SideEffectGateway(store, engine, providers=register(provider(transport=transport)))
    initial = agent_request(policy={"access_refs": [CREDENTIAL.uri]})

    blocked = gateway.execute_provider(
        initial,
        "openai.responses",
        "generate",
        {"input": "hello"},
        access_refs=(CREDENTIAL,),
    )
    assert blocked.status == SideEffectExecutionStatus.BLOCKED
    assert blocked.error_code == "APPROVAL_REQUIRED"
    assert transport.calls == []

    pending = approval.request(initial, NOW)
    assert pending.status == ApprovalStatus.PENDING
    approval.approve(pending.approval_id, LATER)
    approved = initial.model_copy(
        update={"policy": {**initial.policy, "approval_id": pending.approval_id}}
    )
    succeeded = gateway.execute_provider(
        approved,
        "openai.responses",
        "generate",
        {"input": "hello"},
        access_refs=(CREDENTIAL,),
    )
    assert succeeded.status == SideEffectExecutionStatus.SUCCEEDED
    assert len(transport.calls) == 1
    store.close()


def test_gateway_preserves_typed_provider_failure_and_legacy_generic_behavior(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    transport = FakeTransport([OpenAITransportResponse(429, {"error": {"code": "rate_limit_exceeded"}})])
    gateway = SideEffectGateway(store, engine, providers=register(provider(transport=transport)))
    result = gateway.execute_provider(
        agent_request(policy={"access_refs": [CREDENTIAL.uri]}, key=None),
        "openai.responses",
        "generate",
        {"input": "hello"},
        access_refs=(CREDENTIAL,),
        idempotency_key=None,
    )
    assert result.status == SideEffectExecutionStatus.FAILED
    assert result.error_code == "PROVIDER_RATE_LIMITED"
    assert result.metadata["error_category"] == "rate_limit"
    assert result.metadata["retryable"] is True
    assert result.metadata["provider_code"] == "rate_limit_exceeded"
    assert "sk-test-secret" not in repr(result.model_dump())
    store.close()


def test_gateway_idempotent_replay_does_not_repeat_provider_transport(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    transport = FakeTransport()
    gateway = SideEffectGateway(store, engine, providers=register(provider(transport=transport)))
    policy = {"access_refs": [CREDENTIAL.uri]}

    first = gateway.execute_provider(
        agent_request(policy=policy, request_id="REQ_FIRST", key="same-key"),
        "openai.responses",
        "generate",
        {"input": "hello"},
        access_refs=(CREDENTIAL,),
    )
    replay = gateway.execute_provider(
        agent_request(policy=policy, request_id="REQ_REPLAY", key="same-key"),
        "openai.responses",
        "generate",
        {"input": "hello"},
        access_refs=(CREDENTIAL,),
    )
    assert first.status == SideEffectExecutionStatus.SUCCEEDED
    assert replay.status == SideEffectExecutionStatus.SUCCEEDED
    assert replay.idempotent_replay is True
    assert len(transport.calls) == 1
    store.close()
