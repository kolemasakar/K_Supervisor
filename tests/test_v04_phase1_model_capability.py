from __future__ import annotations

from datetime import datetime, timezone

from access import AccessReference, EnvironmentSecretBackend, environment_key
from agents import ModelBackedAgent
from integrations.gateway import SideEffectGateway
from models.agent import AgentDescriptor, AgentRunRequest, CapabilityRef
from models.capability import CapabilityDescriptor
from models.enums import ExecutionStatus, ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from policy.engine import PolicyEngine
from policy.persistence import PersistencePolicyAuditSink
from providers import (
    ModelProfile,
    OpenAIResponsesProvider,
    OpenAITransportResponse,
    PriorityModelSelector,
)
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry, ProviderRegistry
from runtime import ExecutionControl, RuntimeLimits
from tests.phase6_support import make_spec

NOW = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
CREDENTIAL = AccessReference(uri="secret://project/P11/openai")
MODEL = ModelProfile(
    model_id="configured-model",
    features=("text", "reasoning"),
    context_window=128000,
    priority=10,
)


class FakeTransport:
    def __init__(self, outcomes=None):
        self.outcomes = list(
            outcomes
            or [
                OpenAITransportResponse(
                    status_code=200,
                    payload={
                        "id": "resp_capability",
                        "model": MODEL.model_id,
                        "status": "completed",
                        "output_text": "model output",
                        "usage": {
                            "input_tokens": 4,
                            "output_tokens": 3,
                            "total_tokens": 7,
                        },
                    },
                    request_id="req_capability",
                )
            ]
        )
        self.calls: list[dict] = []

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
            {
                "api_key": api_key,
                "body": dict(body),
                "connect_timeout_seconds": connect_timeout_seconds,
                "request_timeout_seconds": request_timeout_seconds,
                "idempotency_key": idempotency_key,
            }
        )
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def build_stack(tmp_path, *, allowed=True, transport=None):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()

    policy = {
        "allowed_side_effects": ["WRITE_EXTERNAL"] if allowed else [],
        "approval_side_effects": [],
        "approval_risk_classes": [],
        "denied_side_effects": [] if allowed else ["WRITE_EXTERNAL"],
        "allowed_access_refs": [CREDENTIAL.uri],
    }
    spec = make_spec(project_id="P11", spec_id="PS11").model_copy(
        update={"autonomy": {"policy": policy}}
    )
    project = Project(
        project_id="P11",
        name="Model Capability Project",
        active_project_spec_id=spec.project_spec_id,
        lifecycle_state=ProjectLifecycleState.BUILDING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )
    projects = ProjectRegistry(store)
    projects.register(project, spec)

    capabilities = CapabilityRegistry()
    capability = CapabilityDescriptor(
        capability_id="generation.model",
        capability_version="1.0.0",
        description="Generate text through a governed MODEL provider.",
        operations=("run",),
        input_schema="schema://model/generation/input",
        output_schema="schema://model/generation/output",
        side_effects=("WRITE_EXTERNAL",),
        risk_class="LOW",
        metadata={"reference": False, "model_backed": True},
    )
    capabilities.register(capability)

    agents = AgentRegistry(capabilities)
    descriptor = AgentDescriptor(
        agent_id="agent.model.production",
        agent_type="MODEL_BACKED",
        agent_version="1.0.0",
        display_name="Governed Model Agent",
        capabilities=(
            CapabilityRef(
                capability_id=capability.capability_id,
                capability_version=capability.capability_version,
            ),
        ),
        status="AVAILABLE",
        metadata={"reference": False},
    )
    agents.register(descriptor)

    engine = PolicyEngine(
        projects,
        agents,
        audit=PersistencePolicyAuditSink(store),
    )
    actual_transport = transport or FakeTransport()
    provider = OpenAIResponsesProvider(
        secret_backend=EnvironmentSecretBackend(
            {environment_key(CREDENTIAL): "sk-test-secret"}
        ),
        credential_ref=CREDENTIAL,
        models=(MODEL,),
        default_model=MODEL.model_id,
        transport=actual_transport,
        default_max_output_tokens=64,
        max_output_tokens_limit=256,
    )
    providers = ProviderRegistry()
    providers.register(provider)
    gateway = SideEffectGateway(store, engine, providers=providers)
    agent = ModelBackedAgent(
        gateway,
        PriorityModelSelector(),
        provider_access_refs={"openai.responses": (CREDENTIAL,)},
    )
    return store, descriptor, capability, actual_transport, agent


def request(*, prompt="Generate a short result.", requirements=None):
    return AgentRunRequest(
        request_id="REQ_MODEL_CAPABILITY",
        project_id="P11",
        task_id="TASK_MODEL_CAPABILITY",
        workflow_run_id="WF_MODEL_CAPABILITY",
        run_id="RUN_MODEL_CAPABILITY",
        agent_id="agent.model.production",
        capability_id="generation.model",
        capability_version="1.0.0",
        operation="run",
        input={
            "prompt": prompt,
            "model_requirements": requirements or {"features": ["text"]},
        },
        policy={"access_refs": [CREDENTIAL.uri]},
        limits={"max_tokens": 16},
        idempotency_key="model-capability-idem",
    )


def test_priority_selector_is_provider_neutral_and_deterministic():
    selector = PriorityModelSelector()
    selected = selector.select_model(
        (
            {
                "provider_id": "provider.b",
                "provider_version": "1.0",
                "model_id": "b",
                "features": ("text",),
                "context_window": 64000,
                "priority": 2,
            },
            {
                "provider_id": "provider.a",
                "provider_version": "1.0",
                "model_id": "a",
                "features": ("text", "reasoning"),
                "context_window": 128000,
                "priority": 7,
            },
        ),
        {"features": ["text"], "minimum_context_window": 100000},
    )
    assert selected is not None
    assert selected["provider_id"] == "provider.a"
    assert selected["model_id"] == "a"

    assert selector.select_model(
        (
            {
                "provider_id": "provider.a",
                "provider_version": "1.0",
                "model_id": "a",
                "features": ("text",),
                "context_window": 128000,
                "priority": 7,
            },
        ),
        {"provider_id": "provider.other"},
    ) is None


def test_non_reference_model_capability_executes_through_governed_provider(tmp_path):
    store, descriptor, capability, transport, agent = build_stack(tmp_path)
    assert descriptor.metadata["reference"] is False
    assert capability.metadata["reference"] is False

    control = ExecutionControl(RuntimeLimits.from_request({"max_tokens": 16}))
    result = agent(request(), control)

    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.output == {"text": "model output"}
    assert result.metadata["model_execution"]["provider_id"] == "openai.responses"
    assert result.metadata["model_execution"]["model_id"] == MODEL.model_id
    assert result.metadata["model_execution"]["provider_response_id"] == "resp_capability"
    assert control.usage["tokens"] == 3.0

    assert len(transport.calls) == 1
    assert transport.calls[0]["body"] == {
        "model": MODEL.model_id,
        "input": "Generate a short result.",
        "max_output_tokens": 16,
        "store": False,
    }
    assert transport.calls[0]["idempotency_key"] == "model-capability-idem"

    executions = store.list_side_effect_executions("P11")
    assert len(executions) == 1
    assert executions[0].component_kind == "PROVIDER"
    assert executions[0].component_id == "openai.responses"
    assert "sk-test-secret" not in repr(result.model_dump())
    assert "sk-test-secret" not in repr(executions[0].model_dump())
    assert "sk-test-secret" not in repr(store.list_audit_events("P11"))
    store.close()


def test_model_capability_policy_deny_makes_zero_transport_calls(tmp_path):
    store, _, _, transport, agent = build_stack(tmp_path, allowed=False)
    result = agent(
        request(),
        ExecutionControl(RuntimeLimits.from_request({"max_tokens": 16})),
    )

    assert result.status == ExecutionStatus.BLOCKED
    assert result.error is not None
    assert result.error.code == "SIDE_EFFECT_DENIED"
    assert transport.calls == []
    store.close()


def test_model_capability_preserves_safe_provider_failure(tmp_path):
    transport = FakeTransport(
        [
            OpenAITransportResponse(
                status_code=429,
                payload={
                    "error": {
                        "code": "credit_balance_exhausted",
                        "message": "provider-private-message",
                    }
                },
                request_id="req_rate_limited",
            )
        ]
    )
    store, _, _, transport, agent = build_stack(tmp_path, transport=transport)
    result = agent(
        request(),
        ExecutionControl(RuntimeLimits.from_request({"max_tokens": 16})),
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "PROVIDER_RATE_LIMITED"
    assert result.error.category == "rate_limit"
    assert result.error.retryable is True
    assert result.error.details["provider_code"] == "credit_balance_exhausted"
    serialized = repr(result.model_dump())
    assert "sk-test-secret" not in serialized
    assert "provider-private-message" not in serialized
    store.close()


def test_model_capability_fails_closed_before_transport_for_invalid_input(tmp_path):
    store, _, _, transport, agent = build_stack(tmp_path)
    result = agent(
        request(prompt=""),
        ExecutionControl(RuntimeLimits.from_request({"max_tokens": 16})),
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "MODEL_INPUT_INVALID"
    assert transport.calls == []
    store.close()
