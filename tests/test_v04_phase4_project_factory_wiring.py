from __future__ import annotations

import json
import pytest

from access import AccessReference, EnvironmentSecretBackend, environment_key
from factory import BootstrapBlockedError, GitHubHttpResponse, ProjectFactory
from factory.governed_github import build_governed_github_repository_adapter
from ksupervisor.config import PlatformConfig
from models.project import ProjectSpec
from service_api.runtime import build_service_runtime
from supervisor.human_intervention import HumanInterventionBroker
from tests.phase6_support import LATER, make_project, make_spec, open_registry


SERVICE_TOKEN = "phase4-service-token"
GITHUB_TOKEN = "phase4-project-factory-token"


class FakeTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
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
        if not self.responses:
            raise AssertionError("unexpected GitHub transport call")
        return self.responses.pop(0)


def response(status=200, body=None, headers=None):
    return GitHubHttpResponse(
        status=status,
        headers=headers or {},
        body=b"" if body is None else json.dumps(body).encode("utf-8"),
    )


def github_spec(*, approval=True):
    base = make_spec(provider="GITHUB", project_id="P6", spec_id="PS6")
    data = base.model_dump(mode="python")
    data["repository"] = {
        **base.repository,
        "repository_owner": "ExampleOrg",
        "repository_name": "phase-six-demo",
        "repository_credential_ref": "secret://project/P6/github",
    }
    data["autonomy"] = {
        "policy": {
            "allowed_side_effects": ["READ_EXTERNAL"],
            "approval_side_effects": (
                ["CREATE_RESOURCE", "WRITE_EXTERNAL", "MODIFY_RESOURCE"]
                if approval
                else []
            ),
            "allowed_access_refs": ["secret://project/P6/github"],
            "approval_risk_classes": [],
        }
    }
    return ProjectSpec.model_validate(data)


def test_service_runtime_wires_project_factory_without_github_credential(tmp_path):
    config = PlatformConfig(
        state_db_path=str(tmp_path / "state.db"),
        service_host={
            "port": 0,
            "principals": [
                {
                    "principal_id": "owner",
                    "scopes": ["projects:read"],
                    "token_ref": {"uri": "secret://service/owner"},
                }
            ],
        },
    )
    runtime = build_service_runtime(
        config,
        secret_backend=EnvironmentSecretBackend(
            {"KSUP_SECRET__SERVICE_OWNER": SERVICE_TOKEN}
        ),
    )
    try:
        assert runtime.project_factory is not None
        assert set(runtime.project_factory.adapters) == {"FILESYSTEM", "GITHUB"}
    finally:
        runtime.close()


def test_project_factory_policy_approval_blocks_before_github_transport(tmp_path):
    store, registry = open_registry(tmp_path / "state.db")
    spec = github_spec(approval=True)
    registry.register(make_project(spec), spec)
    human = HumanInterventionBroker(store, registry)
    credential = AccessReference(uri="secret://project/P6/github")
    backend = EnvironmentSecretBackend({environment_key(credential): GITHUB_TOKEN})
    transport = FakeTransport()
    adapter = build_governed_github_repository_adapter(
        store,
        registry,
        human,
        backend,
        transport=transport,
    )

    with pytest.raises(BootstrapBlockedError) as blocked:
        ProjectFactory(registry, (adapter,), human).bootstrap("P6", LATER)

    approvals = store.list_approvals("P6")
    assert len(approvals) == 1
    assert approvals[0].status.value == "PENDING"
    assert blocked.value.human_action_id == approvals[0].human_action_id
    assert transport.calls == []
    assert len(store.list_human_actions("P6")) == 1
    store.close()


def test_governed_prepare_uses_gateway_and_never_persists_token(tmp_path):
    store, registry = open_registry(tmp_path / "state.db")
    spec = github_spec(approval=False)
    data = spec.model_dump(mode="python")
    data["autonomy"]["policy"]["allowed_side_effects"] = [
        "READ_EXTERNAL",
        "CREATE_RESOURCE",
    ]
    spec = ProjectSpec.model_validate(data)
    registry.register(make_project(spec), spec)
    human = HumanInterventionBroker(store, registry)
    credential = AccessReference(uri="secret://project/P6/github")
    backend = EnvironmentSecretBackend({environment_key(credential): GITHUB_TOKEN})
    transport = FakeTransport(
        response(404, {"message": "not found"}),
        response(200, {"login": "ExampleOrg", "type": "Organization"}),
        response(201, {"id": 41}),
        response(
            200,
            {
                "id": 41,
                "full_name": "ExampleOrg/phase-six-demo",
                "visibility": "private",
                "private": True,
                "default_branch": "main",
                "archived": False,
                "disabled": False,
                "html_url": "https://github.com/ExampleOrg/phase-six-demo",
            },
        ),
    )
    adapter = build_governed_github_repository_adapter(
        store,
        registry,
        human,
        backend,
        transport=transport,
    )
    from factory import RepositoryOperationContext, RepositoryTarget

    managed = adapter.prepare(
        RepositoryTarget.from_spec(spec),
        context=RepositoryOperationContext(
            project_id="P6",
            project_spec_id="PS6",
            idempotency_key="project-factory:PS6:bootstrap",
        ),
    )

    assert managed.repository_id == "github:41"
    assert [call["method"] for call in transport.calls] == ["GET", "GET", "POST", "GET"]
    assert GITHUB_TOKEN not in repr(store.list_side_effect_executions("P6"))
    assert GITHUB_TOKEN not in repr(store.list_audit_events("P6"))
    store.close()
