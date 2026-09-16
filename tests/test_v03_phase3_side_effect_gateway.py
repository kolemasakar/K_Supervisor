from datetime import datetime, timezone

from access import AccessReference
from integrations.gateway import SideEffectGateway
from models.agent import AgentRunRequest
from models.side_effect import SideEffectExecutionStatus
from persistence import SQLitePersistenceStore
from policy.contracts import ApprovalStatus
from providers import ProviderDescriptor, ProviderResponse
from registry import ProviderRegistry, ToolRegistry
from registry.project_registry import ProjectRegistry
from tests.phase10_support import FakeProvider, FakeTool
from tests.phase11_support import build_policy_stack
from tools import ToolDescriptor

NOW = datetime(2026, 9, 16, 8, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 16, 8, 5, tzinfo=timezone.utc)


def request(*, policy=None, request_id="REQ_PHASE3", idempotency_key=None):
    return AgentRunRequest(
        request_id=request_id,
        project_id="P11",
        task_id="TASK_PHASE3",
        workflow_run_id="WF_PHASE3",
        run_id=f"RUN_{request_id}",
        agent_id="agent.policy",
        capability_id="policy.test",
        capability_version="1.0.0",
        operation="run",
        input={"value": 1},
        policy=policy or {},
        idempotency_key=idempotency_key,
    )


def allowed_stack(tmp_path):
    project_policy = {
        "allowed_side_effects": ["WRITE_EXTERNAL"],
        "approval_side_effects": [],
        "approval_risk_classes": [],
        "agent_tool_permissions": {
            "agent.policy": {
                "repo.tool": ["write", "read"],
            }
        },
        "allowed_access_refs": [
            "secret://project/P11/repo",
            "secret://project/P11/other",
        ],
    }
    return build_policy_stack(
        tmp_path,
        side_effects=("WRITE_EXTERNAL",),
        risk_class="LOW",
        policy=project_policy,
    )


def test_allow_invokes_tool_once_and_propagates_correlation(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    tools = ToolRegistry()
    tool = FakeTool(ToolDescriptor(tool_id="repo.tool", version="1.0", operations=("write",)))
    tools.register(tool)
    gateway = SideEffectGateway(store, engine, tools=tools)
    ref = AccessReference(uri="secret://project/P11/repo")
    run = request(
        policy={"tools": {"repo.tool": ["write"]}, "access_refs": [ref.uri]},
        idempotency_key="idem-allow",
    )

    result = gateway.invoke_tool(run, "repo.tool", "write", {"path": "README.md"}, access_refs=(ref,))

    assert result.status == SideEffectExecutionStatus.SUCCEEDED
    assert len(tool.requests) == 1
    forwarded = tool.requests[0]
    assert forwarded.request_id == run.request_id
    assert forwarded.agent_id == run.agent_id
    assert forwarded.capability_id == run.capability_id
    assert forwarded.capability_version == run.capability_version
    assert forwarded.idempotency_key == "idem-allow"
    record = store.list_side_effect_executions("P11")[-1]
    assert record.request_id == run.request_id
    assert record.agent_id == run.agent_id
    assert record.capability_id == run.capability_id
    types = [event.event_type for event in store.list_audit_events("P11")]
    assert "SIDE_EFFECT_ATTEMPTED" in types
    assert "SIDE_EFFECT_SUCCEEDED" in types
    store.close()


def test_deny_never_invokes_tool(tmp_path):
    stack = build_policy_stack(
        tmp_path,
        side_effects=("DELETE_RESOURCE",),
        risk_class="LOW",
        policy={
            "denied_side_effects": ["DELETE_RESOURCE"],
            "agent_tool_permissions": {"agent.policy": {"repo.tool": ["write"]}},
        },
    )
    store, _, _, _, _, engine, _, _ = stack
    tools = ToolRegistry()
    tool = FakeTool(ToolDescriptor(tool_id="repo.tool", version="1.0", operations=("write",)))
    tools.register(tool)
    gateway = SideEffectGateway(store, engine, tools=tools)

    result = gateway.invoke_tool(
        request(policy={"tools": {"repo.tool": ["write"]}}),
        "repo.tool",
        "write",
        {},
    )

    assert result.status == SideEffectExecutionStatus.BLOCKED
    assert result.error_code == "SIDE_EFFECT_DENIED"
    assert tool.requests == []
    assert store.list_side_effect_executions("P11") == ()
    assert store.list_audit_events("P11")[-1].event_type == "SIDE_EFFECT_BLOCKED"
    store.close()


def test_require_approval_never_invokes_until_approved(tmp_path):
    stack = build_policy_stack(
        tmp_path,
        side_effects=("CREATE_RESOURCE",),
        risk_class="LOW",
        policy={"agent_tool_permissions": {"agent.policy": {"repo.tool": ["write"]}}},
    )
    store, _, _, _, approval, engine, _, _ = stack
    tools = ToolRegistry()
    tool = FakeTool(ToolDescriptor(tool_id="repo.tool", version="1.0", operations=("write",)))
    tools.register(tool)
    gateway = SideEffectGateway(store, engine, tools=tools)
    initial = request(policy={"tools": {"repo.tool": ["write"]}})

    blocked = gateway.invoke_tool(initial, "repo.tool", "write", {})
    assert blocked.status == SideEffectExecutionStatus.BLOCKED
    assert blocked.error_code == "APPROVAL_REQUIRED"
    assert tool.requests == []

    pending = approval.request(initial, NOW)
    assert pending.status == ApprovalStatus.PENDING
    approval.approve(pending.approval_id, LATER)
    approved_request = initial.model_copy(
        update={"policy": {**initial.policy, "approval_id": pending.approval_id}}
    )
    succeeded = gateway.invoke_tool(approved_request, "repo.tool", "write", {})

    assert succeeded.status == SideEffectExecutionStatus.SUCCEEDED
    assert len(tool.requests) == 1
    store.close()


def test_tool_operation_and_protected_reference_are_enforced_at_gateway(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    tools = ToolRegistry()
    tool = FakeTool(
        ToolDescriptor(tool_id="repo.tool", version="1.0", operations=("read", "write"))
    )
    tools.register(tool)
    gateway = SideEffectGateway(store, engine, tools=tools)

    wrong_operation = gateway.invoke_tool(
        request(policy={"tools": {"repo.tool": ["read"]}}),
        "repo.tool",
        "write",
        {},
    )
    assert wrong_operation.status == SideEffectExecutionStatus.BLOCKED
    assert wrong_operation.error_code == "SIDE_EFFECT_PERMISSION_DENIED"

    allowed_ref = AccessReference(uri="secret://project/P11/repo")
    other_ref = AccessReference(uri="secret://project/P11/other")
    wrong_reference = gateway.invoke_tool(
        request(
            policy={
                "tools": {"repo.tool": ["read"]},
                "access_refs": [allowed_ref.uri],
            },
            request_id="REQ_REF",
        ),
        "repo.tool",
        "read",
        {},
        access_refs=(other_ref,),
    )
    assert wrong_reference.status == SideEffectExecutionStatus.BLOCKED
    assert wrong_reference.error_code == "SIDE_EFFECT_PERMISSION_DENIED"
    assert tool.requests == []
    store.close()


def test_idempotency_replays_success_without_duplicate_and_survives_reopen(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    tools = ToolRegistry()
    tool = FakeTool(ToolDescriptor(tool_id="repo.tool", version="1.0", operations=("write",)))
    tools.register(tool)
    gateway = SideEffectGateway(store, engine, tools=tools)
    policy = {"tools": {"repo.tool": ["write"]}}

    first = gateway.invoke_tool(
        request(policy=policy, request_id="REQ_FIRST", idempotency_key="same-key"),
        "repo.tool",
        "write",
        {"value": 7},
    )
    replay = gateway.invoke_tool(
        request(policy=policy, request_id="REQ_REPLAY", idempotency_key="same-key"),
        "repo.tool",
        "write",
        {"value": 7},
    )

    assert first.status == SideEffectExecutionStatus.SUCCEEDED
    assert replay.status == SideEffectExecutionStatus.SUCCEEDED
    assert replay.idempotent_replay
    assert replay.request_id == "REQ_REPLAY"
    assert len(tool.requests) == 1
    replay_event = store.list_audit_events("P11")[-1]
    assert replay_event.event_type == "SIDE_EFFECT_REPLAYED"
    assert replay_event.correlation_id == "REQ_REPLAY"

    conflict = gateway.invoke_tool(
        request(policy=policy, request_id="REQ_CONFLICT", idempotency_key="same-key"),
        "repo.tool",
        "write",
        {"value": 8},
    )
    assert conflict.status == SideEffectExecutionStatus.BLOCKED
    assert conflict.error_code == "SIDE_EFFECT_IDEMPOTENCY_CONFLICT"
    assert len(tool.requests) == 1

    execution_id = first.execution_id
    db_path = store.path
    store.close()

    reopened = SQLitePersistenceStore(db_path)
    reopened.initialize()
    record = reopened.get_side_effect_execution(execution_id)
    assert record is not None
    assert record.status == SideEffectExecutionStatus.SUCCEEDED
    snapshot = ProjectRegistry(reopened).recover("P11")
    assert any(item.execution_id == execution_id for item in snapshot.side_effect_executions)
    reopened.close()


def test_tool_failure_is_normalized_and_durably_audited(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)

    class FailingTool(FakeTool):
        def invoke(self, request):
            self.requests.append(request)
            raise RuntimeError("tool exploded")

    tools = ToolRegistry()
    tool = FailingTool(
        ToolDescriptor(tool_id="repo.tool", version="1.0", operations=("write",))
    )
    tools.register(tool)
    gateway = SideEffectGateway(store, engine, tools=tools)

    result = gateway.invoke_tool(
        request(
            policy={"tools": {"repo.tool": ["write"]}},
            idempotency_key="tool-fail",
        ),
        "repo.tool",
        "write",
        {"path": "README.md"},
    )

    assert result.status == SideEffectExecutionStatus.FAILED
    assert result.error_code == "SIDE_EFFECT_ADAPTER_ERROR"
    assert "tool exploded" in result.error_message
    assert len(tool.requests) == 1
    assert tool.requests[0].request_id == "REQ_PHASE3"
    assert tool.requests[0].idempotency_key == "tool-fail"
    record = store.list_side_effect_executions("P11")[-1]
    assert record.status == SideEffectExecutionStatus.FAILED
    assert store.list_audit_events("P11")[-1].event_type == "SIDE_EFFECT_FAILED"
    store.close()


def test_provider_failure_is_normalized_and_durably_audited(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)

    class FailingProvider(FakeProvider):
        def execute(self, request):
            self.requests.append(request)
            raise RuntimeError("provider exploded")

    providers = ProviderRegistry()
    provider = FailingProvider(
        ProviderDescriptor(
            provider_id="cloud.test",
            version="1.0",
            provider_type="CLOUD",
            operations=("provision",),
        )
    )
    providers.register(provider)
    gateway = SideEffectGateway(store, engine, providers=providers)

    result = gateway.execute_provider(
        request(policy={}, idempotency_key="provider-fail"),
        "cloud.test",
        "provision",
        {"kind": "DATABASE"},
    )

    assert result.status == SideEffectExecutionStatus.FAILED
    assert result.error_code == "SIDE_EFFECT_ADAPTER_ERROR"
    assert "provider exploded" in result.error_message
    assert len(provider.requests) == 1
    assert provider.requests[0].request_id == "REQ_PHASE3"
    assert provider.requests[0].idempotency_key == "provider-fail"
    record = store.list_side_effect_executions("P11")[-1]
    assert record.status == SideEffectExecutionStatus.FAILED
    assert store.list_audit_events("P11")[-1].event_type == "SIDE_EFFECT_FAILED"
    store.close()


def test_provider_adapter_remains_replaceable_behind_gateway(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)

    first_registry = ProviderRegistry()
    first_registry.register(
        FakeProvider(
            ProviderDescriptor(
                provider_id="cloud.replaceable",
                version="1.0",
                provider_type="CLOUD",
                operations=("write",),
            ),
            response=ProviderResponse(payload={"provider": "first"}),
        )
    )
    first = SideEffectGateway(store, engine, providers=first_registry).execute_provider(
        request(request_id="REQ_PROVIDER_1"),
        "cloud.replaceable",
        "write",
        {},
    )

    second_registry = ProviderRegistry()
    second_registry.register(
        FakeProvider(
            ProviderDescriptor(
                provider_id="cloud.replaceable",
                version="1.0",
                provider_type="CLOUD",
                operations=("write",),
            ),
            response=ProviderResponse(payload={"provider": "second"}),
        )
    )
    second = SideEffectGateway(store, engine, providers=second_registry).execute_provider(
        request(request_id="REQ_PROVIDER_2"),
        "cloud.replaceable",
        "write",
        {},
    )

    assert first.output == {"provider": "first"}
    assert second.output == {"provider": "second"}
    store.close()
