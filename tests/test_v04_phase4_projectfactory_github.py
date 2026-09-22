from __future__ import annotations

from datetime import datetime, timezone

import pytest

from access import AccessReference
from factory import (
    BootstrapBlockedError,
    GovernedGitHubRepositoryAdapter,
    ProjectFactory,
    register_github_repository_governance,
)
from integrations import AvailabilityReport, AvailabilityState
from integrations.gateway import SideEffectGateway
from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project, ProjectSpec
from persistence import SQLitePersistenceStore
from policy.approval import PolicyApprovalBroker
from policy.engine import PolicyEngine
from policy.persistence import PersistencePolicyAuditSink
from providers import ProviderDescriptor, ProviderResponse
from registry import AgentRegistry, CapabilityRegistry, ProjectRegistry, ProviderRegistry
from supervisor.human_intervention import HumanInterventionBroker
from tests.phase6_support import make_spec


NOW = datetime(2026, 9, 22, 15, 0, tzinfo=timezone.utc)
CREDENTIAL = AccessReference(uri="secret://project/P4/github")


class SequenceRepositoryProvider:
    def __init__(self):
        self.descriptor = ProviderDescriptor(
            provider_id="github.repository",
            version="1.0",
            provider_type="REPOSITORY",
            operations=(
                "resolve_repository",
                "create_repository",
                "bootstrap_files",
                "handoff_pull_request",
                "create_tag",
            ),
        )
        self.requests = []

    def check_availability(self):
        return AvailabilityReport(
            component_id="github.repository",
            state=AvailabilityState.AVAILABLE,
            checked_at=NOW,
        )

    def execute(self, request):
        self.requests.append(request)
        if request.operation == "create_repository":
            return ProviderResponse(
                payload={
                    "repository_id": "github:4001",
                    "locator": "https://github.com/ExampleOrg/demo",
                    "default_branch": "main",
                    "created": False,
                }
            )
        if request.operation == "bootstrap_files":
            return ProviderResponse(
                payload={
                    "repository_id": "github:4001",
                    "locator": "https://github.com/ExampleOrg/demo",
                    "default_branch": "main",
                    "commit_sha": "abc",
                    "files": [item["path"] for item in request.payload["files"]],
                    "created_files": [item["path"] for item in request.payload["files"]],
                    "noop": False,
                }
            )
        raise AssertionError(f"unexpected provider operation: {request.operation}")


def spec(*, approval=True):
    base = make_spec(project_id="P4", spec_id="PS4", provider="GITHUB")
    data = base.model_dump(mode="python")
    data["repository"] = {
        **base.repository,
        "repository_owner": "ExampleOrg",
        "repository_name": "demo",
        "repository_credential_ref": CREDENTIAL.uri,
        "provisioning": "AUTOMATABLE",
    }
    policy = {"allowed_access_refs": [CREDENTIAL.uri], "approval_risk_classes": []}
    if not approval:
        policy.update(
            {
                "allowed_side_effects": [
                    "READ_EXTERNAL",
                    "WRITE_EXTERNAL",
                    "CREATE_RESOURCE",
                    "MODIFY_RESOURCE",
                ],
                "approval_side_effects": [],
            }
        )
    data["autonomy"] = {"policy": policy}
    return ProjectSpec.model_validate(data)


def stack(tmp_path, *, approval=True):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()
    projects = ProjectRegistry(store)
    active = spec(approval=approval)
    projects.register(
        Project(
            project_id="P4",
            name="Phase Four",
            active_project_spec_id=active.project_spec_id,
            lifecycle_state=ProjectLifecycleState.APPROVED,
            operational_state=ProjectOperationalState.ACTIVE,
            created_at=NOW,
            updated_at=NOW,
        ),
        active,
    )

    capabilities = CapabilityRegistry()
    agents = AgentRegistry(capabilities)
    register_github_repository_governance(agents)
    human = HumanInterventionBroker(store, projects)
    approvals = PolicyApprovalBroker(store, agents, human)
    policy = PolicyEngine(
        projects,
        agents,
        approvals=approvals,
        audit=PersistencePolicyAuditSink(store),
    )
    item = SequenceRepositoryProvider()
    providers = ProviderRegistry()
    providers.register(item)
    gateway = SideEffectGateway(store, policy, providers=providers)
    adapter = GovernedGitHubRepositoryAdapter(gateway, policy, approvals)
    factory = ProjectFactory(projects, (adapter,), human)
    return store, projects, human, approvals, item, factory


def test_project_factory_bootstrap_uses_governed_provider_without_raw_bypass(tmp_path):
    store, projects, _, _, item, factory = stack(tmp_path, approval=False)

    result = factory.bootstrap("P4", NOW)

    assert result.repository.repository_id == "github:4001"
    assert result.status == "BOOTSTRAPPED"
    assert projects.get("P4").lifecycle_state == ProjectLifecycleState.BOOTSTRAPPED
    assert [request.operation for request in item.requests] == [
        "create_repository",
        "bootstrap_files",
    ]
    records = store.list_side_effect_executions("P4")
    assert [record.status.value for record in records] == ["SUCCEEDED", "SUCCEEDED"]
    assert all(record.component_id == "github.repository" for record in records)
    assert CREDENTIAL.uri not in repr([record.signature for record in records])
    store.close()


def test_project_factory_policy_approval_blocks_before_provider_and_resumes(tmp_path):
    store, projects, _, approvals, item, factory = stack(tmp_path, approval=True)

    with pytest.raises(BootstrapBlockedError) as first:
        factory.bootstrap("P4", NOW)
    assert first.value.human_action_id is not None
    assert item.requests == []
    assert projects.get("P4").lifecycle_state == ProjectLifecycleState.PROVISIONING

    pending = [record for record in store.list_approvals("P4") if record.status.value == "PENDING"]
    assert len(pending) == 1
    approvals.approve(pending[0].approval_id, NOW)

    with pytest.raises(BootstrapBlockedError) as second:
        factory.bootstrap("P4", NOW)
    assert second.value.human_action_id is not None
    assert [request.operation for request in item.requests] == ["create_repository"]

    pending = [record for record in store.list_approvals("P4") if record.status.value == "PENDING"]
    assert len(pending) == 1
    approvals.approve(pending[0].approval_id, NOW)

    result = factory.bootstrap("P4", NOW)
    assert result.status == "BOOTSTRAPPED"
    assert [request.operation for request in item.requests] == [
        "create_repository",
        "bootstrap_files",
    ]
    assert projects.get("P4").lifecycle_state == ProjectLifecycleState.BOOTSTRAPPED
    store.close()


def test_missing_policy_access_reference_blocks_before_provider_and_opens_repository_action(tmp_path):
    store, projects, human, _, item, factory = stack(tmp_path, approval=False)
    current = store.get_project_spec("PS4")
    data = current.model_dump(mode="python")
    data["autonomy"] = {
        "policy": {
            "allowed_side_effects": ["READ_EXTERNAL", "CREATE_RESOURCE"],
            "approval_side_effects": [],
            "allowed_access_refs": [],
            "approval_risk_classes": [],
        }
    }
    replacement = ProjectSpec.model_validate(data)
    store.save_project_spec(replacement)

    with pytest.raises(BootstrapBlockedError) as blocked:
        factory.bootstrap("P4", NOW)

    assert blocked.value.human_action_id is not None
    assert item.requests == []
    actions = store.list_human_actions("P4")
    assert any(action.action_type == "REPOSITORY_PROVISIONING" for action in actions)
    store.close()
