from __future__ import annotations

import json

import pytest

from access import AccessReference, EnvironmentSecretBackend, environment_key
from factory import GitHubHttpResponse, GitHubRestClient, GitHubTransportError
from integrations.gateway import SideEffectGateway
from models.agent import AgentRunRequest
from models.side_effect import SideEffectExecutionStatus
from policy.contracts import ApprovalStatus
from providers import GitHubRepositoryProvider, ProviderExecutionError
from registry import ProviderRegistry
from tests.phase11_support import LATER, NOW, build_policy_stack


CREDENTIAL = AccessReference(uri="secret://project/P11/github")
TOKEN = "phase4-github-secret"


class FakeTransport:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def request(self, method, url, *, headers, body, timeout_seconds):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        if not self.outcomes:
            raise AssertionError("unexpected GitHub transport call")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def response(status=200, body=None, headers=None):
    return GitHubHttpResponse(
        status=status,
        headers=headers or {},
        body=b"" if body is None else json.dumps(body).encode("utf-8"),
    )


def repo_body(**updates):
    return {
        "id": 7001,
        "full_name": "ExampleOrg/demo-repo",
        "visibility": "private",
        "private": True,
        "default_branch": "main",
        "archived": False,
        "disabled": False,
        "html_url": "https://github.com/ExampleOrg/demo-repo",
        **updates,
    }


def payload(**updates):
    return {
        "owner": "ExampleOrg",
        "name": "demo-repo",
        "visibility": "PRIVATE",
        "default_branch": "main",
        "provisioning": "AUTOMATABLE",
        **updates,
    }


def provider(transport):
    backend = EnvironmentSecretBackend({environment_key(CREDENTIAL): TOKEN})
    return GitHubRepositoryProvider(
        GitHubRestClient(backend, transport=transport, timeout_seconds=3)
    )


def direct_request(operation, *, refs=(CREDENTIAL,), request_payload=None, key="phase4-key"):
    from providers import ProviderRequest

    return ProviderRequest(
        project_id="P11",
        operation=operation,
        payload=payload() if request_payload is None else request_payload,
        access_refs=refs,
        request_id="REQ_PHASE4",
        agent_id="agent.policy",
        capability_id="policy.test",
        capability_version="1.0.0",
        idempotency_key=key,
    )


def agent_request(*, request_id="REQ_PHASE4", key="phase4-key", policy=None):
    return AgentRunRequest(
        request_id=request_id,
        project_id="P11",
        task_id="TASK_PHASE4",
        workflow_run_id="WF_PHASE4",
        run_id=f"RUN_{request_id}",
        agent_id="agent.policy",
        capability_id="policy.test",
        capability_version="1.0.0",
        operation="run",
        input={},
        policy=policy or {},
        idempotency_key=key,
    )


def registry(item):
    providers = ProviderRegistry()
    providers.register(item)
    return providers


def allowed_stack(tmp_path, *, approval=False):
    policy = {
        "allowed_side_effects": [] if approval else ["CREATE_RESOURCE"],
        "approval_side_effects": ["CREATE_RESOURCE"] if approval else [],
        "approval_risk_classes": [],
        "allowed_access_refs": [CREDENTIAL.uri],
    }
    return build_policy_stack(
        tmp_path,
        side_effects=("CREATE_RESOURCE",),
        risk_class="LOW",
        policy=policy,
    )


def test_provider_descriptor_and_resolve_are_read_only_and_safe():
    transport = FakeTransport(response(body=repo_body()))
    item = provider(transport)

    assert item.descriptor.provider_id == "github.repository"
    assert item.descriptor.provider_type == "REPOSITORY"
    assert set(item.descriptor.operations) == {
        "resolve_repository",
        "create_repository",
        "bootstrap_files",
        "list_files",
        "read_file",
        "handoff_pull_request",
        "create_tag",
    }

    result = item.execute(direct_request("resolve_repository"))

    assert result.payload == {
        "repository_id": "github:7001",
        "locator": "https://github.com/ExampleOrg/demo-repo",
        "default_branch": "main",
        "created": False,
    }
    assert result.metadata == {"recovered": False}
    assert [call["method"] for call in transport.calls] == ["GET"]
    assert TOKEN not in repr(result.model_dump())


def test_provider_requires_exactly_one_authorized_credential_reference():
    transport = FakeTransport()
    item = provider(transport)

    with pytest.raises(ProviderExecutionError) as missing:
        item.execute(direct_request("resolve_repository", refs=()))
    assert missing.value.code == "GITHUB_CREDENTIAL_REQUIRED"

    with pytest.raises(ProviderExecutionError) as duplicate:
        item.execute(direct_request("resolve_repository", refs=(CREDENTIAL, CREDENTIAL)))
    assert duplicate.value.code == "GITHUB_CREDENTIAL_REQUIRED"
    assert transport.calls == []


def test_create_reuses_exact_existing_repository_without_write():
    transport = FakeTransport(response(body=repo_body()))
    result = provider(transport).execute(direct_request("create_repository"))

    assert result.payload["created"] is False
    assert result.metadata["recovered"] is True
    assert len(transport.calls) == 1
    assert transport.calls[0]["method"] == "GET"


def test_create_organization_repository_then_rereads_canonical_state():
    transport = FakeTransport(
        response(404, body={"message": "not found"}),
        response(body={"login": "ExampleOrg", "type": "Organization"}),
        response(201, body=repo_body()),
        response(body=repo_body()),
    )

    result = provider(transport).execute(direct_request("create_repository"))

    assert result.payload["repository_id"] == "github:7001"
    assert result.payload["created"] is True
    assert result.metadata["recovered"] is False
    assert [call["method"] for call in transport.calls] == ["GET", "GET", "POST", "GET"]
    assert transport.calls[2]["url"].endswith("/orgs/ExampleOrg/repos")
    assert json.loads(transport.calls[2]["body"]) == {"name": "demo-repo", "private": True}


def test_uncertain_create_transport_failure_recovers_by_exact_resolve():
    transport = FakeTransport(
        response(404, body={"message": "not found"}),
        response(body={"login": "ExampleOrg", "type": "Organization"}),
        GitHubTransportError("response lost after create"),
        response(body=repo_body()),
    )

    result = provider(transport).execute(direct_request("create_repository"))

    assert result.payload["created"] is True
    assert result.metadata["recovered"] is True
    assert [call["method"] for call in transport.calls] == ["GET", "GET", "POST", "GET"]
    assert TOKEN not in repr(result.model_dump())


def test_create_conflicting_existing_repository_fails_without_write():
    transport = FakeTransport(response(body=repo_body(visibility="public", private=False)))

    with pytest.raises(ProviderExecutionError) as raised:
        provider(transport).execute(direct_request("create_repository"))

    assert raised.value.code == "GITHUB_REPOSITORY_CONFLICT"
    assert raised.value.category == "conflict"
    assert len(transport.calls) == 1


def test_provider_normalizes_rate_limit_without_raw_provider_body():
    transport = FakeTransport(
        GitHubHttpResponse(
            status=429,
            headers={"Retry-After": "30"},
            body=b'{"message":"raw GitHub provider detail"}',
        )
    )

    with pytest.raises(ProviderExecutionError) as raised:
        provider(transport).execute(direct_request("resolve_repository"))

    assert raised.value.code == "GITHUB_RATE_LIMITED"
    assert raised.value.category == "rate_limit"
    assert raised.value.retryable is True
    assert "raw GitHub" not in str(raised.value)
    assert TOKEN not in str(raised.value)


def test_gateway_allow_persists_safe_idempotent_create_and_replay(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    transport = FakeTransport(
        response(404, body={"message": "not found"}),
        response(body={"login": "ExampleOrg", "type": "Organization"}),
        response(201, body=repo_body()),
        response(body=repo_body()),
    )
    gateway = SideEffectGateway(
        store,
        engine,
        providers=registry(provider(transport)),
    )
    policy = {"access_refs": [CREDENTIAL.uri]}

    first = gateway.execute_provider(
        agent_request(policy=policy, request_id="REQ_FIRST"),
        "github.repository",
        "create_repository",
        payload(),
        access_refs=(CREDENTIAL,),
        idempotency_key="repo-create",
    )
    replay = gateway.execute_provider(
        agent_request(policy=policy, request_id="REQ_REPLAY"),
        "github.repository",
        "create_repository",
        payload(),
        access_refs=(CREDENTIAL,),
        idempotency_key="repo-create",
    )

    assert first.status == SideEffectExecutionStatus.SUCCEEDED
    assert first.output["repository_id"] == "github:7001"
    assert replay.status == SideEffectExecutionStatus.SUCCEEDED
    assert replay.idempotent_replay is True
    assert len(transport.calls) == 4
    record = store.list_side_effect_executions("P11")[-1]
    serialized = repr(record.model_dump())
    assert TOKEN not in serialized
    assert CREDENTIAL.uri not in record.signature
    assert TOKEN not in repr(store.list_audit_events("P11"))
    store.close()


def test_gateway_same_idempotency_key_different_payload_is_blocked(tmp_path):
    store, _, _, _, _, engine, _, _ = allowed_stack(tmp_path)
    transport = FakeTransport(
        response(404, body={"message": "not found"}),
        response(body={"login": "ExampleOrg", "type": "Organization"}),
        response(201, body=repo_body()),
        response(body=repo_body()),
    )
    gateway = SideEffectGateway(store, engine, providers=registry(provider(transport)))
    policy = {"access_refs": [CREDENTIAL.uri]}

    first = gateway.execute_provider(
        agent_request(policy=policy, request_id="REQ_FIRST_DIFFERENT"),
        "github.repository",
        "create_repository",
        payload(),
        access_refs=(CREDENTIAL,),
        idempotency_key="same-key-different-payload",
    )
    before = len(transport.calls)
    changed = {**payload(), "visibility": "PUBLIC"}
    conflict = gateway.execute_provider(
        agent_request(policy=policy, request_id="REQ_SECOND_DIFFERENT"),
        "github.repository",
        "create_repository",
        changed,
        access_refs=(CREDENTIAL,),
        idempotency_key="same-key-different-payload",
    )

    assert first.status == SideEffectExecutionStatus.SUCCEEDED
    assert conflict.status == SideEffectExecutionStatus.BLOCKED
    assert conflict.error_code == "SIDE_EFFECT_IDEMPOTENCY_CONFLICT"
    assert len(transport.calls) == before
    store.close()


def test_gateway_deny_blocks_before_any_github_transport_call(tmp_path):
    stack = build_policy_stack(
        tmp_path,
        side_effects=("CREATE_RESOURCE",),
        risk_class="LOW",
        policy={
            "denied_side_effects": ["CREATE_RESOURCE"],
            "allowed_access_refs": [CREDENTIAL.uri],
        },
    )
    store, _, _, _, _, engine, _, _ = stack
    transport = FakeTransport()
    gateway = SideEffectGateway(store, engine, providers=registry(provider(transport)))

    result = gateway.execute_provider(
        agent_request(policy={"access_refs": [CREDENTIAL.uri]}),
        "github.repository",
        "create_repository",
        payload(),
        access_refs=(CREDENTIAL,),
        idempotency_key="denied",
    )

    assert result.status == SideEffectExecutionStatus.BLOCKED
    assert transport.calls == []
    store.close()


def test_gateway_requires_approval_before_github_write(tmp_path):
    store, _, _, _, approvals, engine, _, _ = allowed_stack(tmp_path, approval=True)
    transport = FakeTransport(
        response(404, body={"message": "not found"}),
        response(body={"login": "ExampleOrg", "type": "Organization"}),
        response(201, body=repo_body()),
        response(body=repo_body()),
    )
    gateway = SideEffectGateway(store, engine, providers=registry(provider(transport)))
    initial = agent_request(policy={"access_refs": [CREDENTIAL.uri]})

    blocked = gateway.execute_provider(
        initial,
        "github.repository",
        "create_repository",
        payload(),
        access_refs=(CREDENTIAL,),
        idempotency_key="approval-create",
    )
    assert blocked.status == SideEffectExecutionStatus.BLOCKED
    assert blocked.error_code == "APPROVAL_REQUIRED"
    assert transport.calls == []

    approval = approvals.request(initial, NOW)
    assert approval.status == ApprovalStatus.PENDING
    approvals.approve(approval.approval_id, LATER)
    approved = initial.model_copy(
        update={"policy": {**initial.policy, "approval_id": approval.approval_id}}
    )
    result = gateway.execute_provider(
        approved,
        "github.repository",
        "create_repository",
        payload(),
        access_refs=(CREDENTIAL,),
        idempotency_key="approval-create",
    )

    assert result.status == SideEffectExecutionStatus.SUCCEEDED
    assert len(transport.calls) == 4
    store.close()


def test_read_file_operation_returns_utf8_content_without_material_write():
    import base64

    content = "# Reference\n"
    transport = FakeTransport(
        response(
            body={
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            }
        )
    )
    result = provider(transport).execute(
        direct_request("read_file", request_payload={**payload(), "path": "docs/REFERENCE.md"})
    )

    assert result.payload == {
        "path": "docs/REFERENCE.md",
        "found": True,
        "content": content,
    }
    assert [call["method"] for call in transport.calls] == ["GET"]


def test_read_file_missing_is_normalized_as_absent():
    transport = FakeTransport(response(404, body={"message": "not found"}))
    result = provider(transport).execute(
        direct_request("read_file", request_payload={**payload(), "path": "docs/MISSING.md"})
    )

    assert result.payload == {
        "path": "docs/MISSING.md",
        "found": False,
        "content": None,
    }


def test_read_file_rejects_path_escape_before_transport():
    transport = FakeTransport()
    with pytest.raises(ProviderExecutionError) as raised:
        provider(transport).execute(
            direct_request("read_file", request_payload={**payload(), "path": "../secret.txt"})
        )

    assert raised.value.code == "GITHUB_INVALID_REQUEST"
    assert transport.calls == []
