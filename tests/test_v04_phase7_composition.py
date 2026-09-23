from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from access import AccessReference, EnvironmentSecretBackend, environment_key
from factory.contracts import BootstrapFile, RepositoryOperationContext, RepositoryTarget
from factory.repository import RoutedRepositoryAdapter
from ksupervisor.cli import build_parser
from ksupervisor.config import PlatformConfig
from models.enums import (
    HumanActionStatus,
    ProjectLifecycleState,
    ProjectOperationalState,
    ProjectSpecStatus,
    ReleaseStatus,
)
from models.project import Project, ProjectSpec
from providers import OpenAITransportResponse
from service_api import ServicePrincipal
from service_api.runtime import (
    MODEL_AGENT_ID,
    MODEL_CAPABILITY_ID,
    build_service_runtime,
)


NOW = datetime(2026, 9, 23, 6, 0, tzinfo=timezone.utc)
SERVICE_REF = AccessReference(uri="secret://service/owner")
MODEL_REF = AccessReference(uri="secret://project/P7_MODEL/openai")


class FakeModelTransport:
    def __init__(self):
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
        return OpenAITransportResponse(
            status_code=200,
            payload={
                "id": "resp_p7a",
                "model": "configured-model",
                "status": "completed",
                "output_text": "phase seven model output",
                "usage": {
                    "input_tokens": 4,
                    "output_tokens": 3,
                    "total_tokens": 7,
                },
            },
            request_id="req_p7a",
        )


def _backend(*, model=False):
    values = {environment_key(SERVICE_REF): "service-test-token"}
    if model:
        values[environment_key(MODEL_REF)] = "sk-phase7-secret"
    return EnvironmentSecretBackend(values)


def _config(tmp_path, *, model=False):
    kwargs = {}
    if model:
        kwargs["model_provider"] = {
            "credential_ref": MODEL_REF.model_dump(mode="json"),
            "models": [
                {
                    "model_id": "configured-model",
                    "features": ["text", "reasoning"],
                    "context_window": 128000,
                    "priority": 10,
                }
            ],
            "default_model": "configured-model",
            "default_max_output_tokens": 64,
            "max_output_tokens_limit": 256,
        }
    return PlatformConfig(
        state_db_path=str(tmp_path / "state.db"),
        service_host={
            "port": 0,
            "principals": [
                {
                    "principal_id": "owner",
                    "scopes": [
                        "executions:start",
                        "releases:read",
                        "releases:prepare",
                    ],
                    "token_ref": SERVICE_REF.model_dump(mode="json"),
                }
            ],
        },
        **kwargs,
    )


def _model_spec():
    policy = {
        "allowed_side_effects": ["WRITE_EXTERNAL"],
        "approval_side_effects": [],
        "approval_risk_classes": [],
        "denied_side_effects": [],
        "allowed_access_refs": [MODEL_REF.uri],
    }
    return ProjectSpec(
        project_spec_id="PS7_MODEL",
        project_id="P7_MODEL",
        spec_version="1.0",
        status=ProjectSpecStatus.APPROVED,
        created_at=NOW,
        updated_at=NOW,
        approved_at=NOW,
        name="Phase 7 Model",
        short_name="phase-7-model",
        purpose="Qualify the production model composition.",
        problem_statement="ServiceRuntime must expose the governed model capability.",
        project_type="AI",
        success_criteria=("model task succeeds",),
        first_working_criteria=("model output exists",),
        repository={"repository_provider": "FILESYSTEM"},
        architecture={"architecture_style": "MODULAR"},
        notifications={"primary_channel": "EMAIL"},
        autonomy={"policy": policy},
    )


def _release_spec():
    return ProjectSpec(
        project_spec_id="PS7_RELEASE",
        project_id="P7_RELEASE",
        spec_version="1.0",
        status=ProjectSpecStatus.APPROVED,
        created_at=NOW,
        updated_at=NOW,
        approved_at=NOW,
        name="Phase 7 Release",
        short_name="phase-7-release",
        purpose="Qualify owner-controlled Plugin release preparation.",
        problem_statement="The operator API must reach ReleaseManager without auto-publication.",
        project_type="AI",
        success_criteria=("release remains owner controlled",),
        first_working_criteria=("working path exists",),
        documentation={"required_documents": ["README.md", "ARCHITECTURE.md", "ROADMAP.md"]},
        repository={
            "repository_provider": "FILESYSTEM",
            "repository_name": "phase-7-release",
            "repository_visibility": "PRIVATE",
            "default_branch": "main",
            "ci_required": True,
            "provisioning": "AUTOMATABLE",
        },
        architecture={"architecture_style": "MODULAR"},
        notifications={"primary_channel": "EMAIL"},
        release={
            "release_targets": ["CHATGPT_PLUGIN"],
            "release_readiness_criteria": ["release tests pass"],
            "publication_owner": "OWNER",
            "chatgpt_plugin": {
                "plugin_name": "phase-7-release",
                "name": "Phase 7 Release",
                "description": "Phase 7 Plugin qualification.",
            },
        },
    )


def test_model_provider_config_is_explicit_and_fail_closed():
    with pytest.raises(ValidationError, match="credential_ref"):
        PlatformConfig(model_provider={"enabled": True})

    disabled = PlatformConfig(model_provider={"enabled": False})
    assert disabled.model_provider is not None
    assert disabled.model_provider.enabled is False

    with pytest.raises(ValidationError, match="default_model"):
        PlatformConfig(
            model_provider={
                "credential_ref": MODEL_REF.model_dump(mode="json"),
                "models": [{"model_id": "configured-model"}],
                "default_model": "missing-model",
            }
        )


def test_service_runtime_composes_governed_model_path(tmp_path):
    transport = FakeModelTransport()
    runtime = build_service_runtime(
        _config(tmp_path, model=True),
        secret_backend=_backend(model=True),
        model_transport=transport,
    )
    try:
        spec = _model_spec()
        runtime.projects.register(
            Project(
                project_id=spec.project_id,
                name=spec.name,
                active_project_spec_id=spec.project_spec_id,
                lifecycle_state=ProjectLifecycleState.BUILDING,
                operational_state=ProjectOperationalState.ACTIVE,
                created_at=NOW,
                updated_at=NOW,
            ),
            spec,
        )

        assert runtime.capabilities.get(MODEL_CAPABILITY_ID, "1.0.0") is not None
        assert runtime.agents.get(MODEL_AGENT_ID) is not None

        response = runtime.api.dispatch(
            "POST",
            "/api/v1/projects/P7_MODEL/tasks",
            principal=ServicePrincipal(
                principal_id="owner",
                scopes=frozenset({"executions:start"}),
            ),
            body={
                "title": "Run governed production model",
                "requirement": {
                    "capability_id": MODEL_CAPABILITY_ID,
                    "version_constraint": "*",
                    "operation": "run",
                },
                "input": {
                    "prompt": "Generate the Phase 7 composition result.",
                    "model_requirements": {"features": ["text"]},
                },
                "policy": {"access_refs": [MODEL_REF.uri]},
                "limits": {"max_tokens": 16},
            },
            idempotency_key="p7a-model-task",
        )

        assert response.status_code == 200
        assert response.body["data"]["task"]["status"] == "SUCCEEDED"
        assert len(transport.calls) == 1
        assert transport.calls[0]["api_key"] == "sk-phase7-secret"
        assert transport.calls[0]["body"] == {
            "model": "configured-model",
            "input": "Generate the Phase 7 composition result.",
            "max_output_tokens": 16,
            "store": False,
        }
        executions = runtime.store.list_side_effect_executions("P7_MODEL")
        assert len(executions) == 1
        assert executions[0].component_id == "openai.responses"
        assert "sk-phase7-secret" not in repr(runtime.store.list_audit_events("P7_MODEL"))
        assert "sk-phase7-secret" not in repr(runtime.store.list_policy_decisions("P7_MODEL"))
    finally:
        runtime.close()


def test_release_prepare_api_uses_routed_repository_and_is_idempotent(tmp_path):
    runtime = build_service_runtime(
        _config(tmp_path),
        secret_backend=_backend(),
    )
    try:
        spec = _release_spec()
        runtime.projects.register(
            Project(
                project_id=spec.project_id,
                name=spec.name,
                active_project_spec_id=spec.project_spec_id,
                lifecycle_state=ProjectLifecycleState.FIRST_WORKING,
                operational_state=ProjectOperationalState.ACTIVE,
                created_at=NOW,
                updated_at=NOW,
            ),
            spec,
        )

        adapter = runtime.project_factory.adapters["FILESYSTEM"]
        target = RepositoryTarget.from_spec(spec)
        repository = adapter.prepare(
            target,
            context=RepositoryOperationContext(
                project_id=spec.project_id,
                project_spec_id=spec.project_spec_id,
                idempotency_key="p7a-release-fixture",
            ),
        )
        adapter.apply_files(
            repository,
            tuple(
                BootstrapFile(path, f"# {path}\n")
                for path in ("README.md", "ARCHITECTURE.md", "ROADMAP.md")
            ),
            context=RepositoryOperationContext(
                project_id=spec.project_id,
                project_spec_id=spec.project_spec_id,
                idempotency_key="p7a-release-files",
            ),
        )

        assert isinstance(runtime.releases.repository_adapter, RoutedRepositoryAdapter)
        principal = ServicePrincipal(
            principal_id="owner",
            scopes=frozenset({"releases:prepare", "releases:read"}),
        )
        body = {
            "version": "0.1.0",
            "satisfied_criteria": ["release tests pass"],
        }
        first = runtime.api.dispatch(
            "POST",
            "/api/v1/projects/P7_RELEASE/releases",
            principal=principal,
            body=body,
            idempotency_key="p7a-release-prepare",
        )
        assert first.status_code == 200
        assert first.body["meta"]["idempotent_replay"] is False
        release = first.body["data"]["release"]
        assert release["status"] == ReleaseStatus.PUBLICATION_REQUIRED.value
        assert release["release_targets"][0]["target_type"] == "CHATGPT_PLUGIN"
        assert release["release_targets"][0]["status"] == ReleaseStatus.PUBLICATION_REQUIRED.value
        assert release["release_targets"][0]["published_at"] is None

        project = runtime.projects.get("P7_RELEASE")
        assert project.lifecycle_state == ProjectLifecycleState.RELEASE_READY
        assert project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER
        actions = runtime.store.list_human_actions("P7_RELEASE")
        assert len(actions) == 1
        assert actions[0].status == HumanActionStatus.WAITING_FOR_OWNER

        replay = runtime.api.dispatch(
            "POST",
            "/api/v1/projects/P7_RELEASE/releases",
            principal=principal,
            body=body,
            idempotency_key="p7a-release-prepare",
        )
        assert replay.status_code == 200
        assert replay.body["meta"]["idempotent_replay"] is True
        assert replay.body["data"]["release"]["release_id"] == release["release_id"]
        assert len(runtime.store.list_human_actions("P7_RELEASE")) == 1
        assert len(runtime.store.list_releases("P7_RELEASE")) == 1
        assert len(runtime.store.list_release_targets("P7_RELEASE")) == 1
    finally:
        runtime.close()


def test_release_prepare_scope_and_cli_surface(tmp_path):
    runtime = build_service_runtime(
        _config(tmp_path),
        secret_backend=_backend(),
    )
    try:
        spec = _release_spec()
        runtime.projects.register(
            Project(
                project_id=spec.project_id,
                name=spec.name,
                active_project_spec_id=spec.project_spec_id,
                lifecycle_state=ProjectLifecycleState.FIRST_WORKING,
                operational_state=ProjectOperationalState.ACTIVE,
                created_at=NOW,
                updated_at=NOW,
            ),
            spec,
        )
        denied = runtime.api.dispatch(
            "POST",
            "/api/v1/projects/P7_RELEASE/releases",
            principal=ServicePrincipal(
                principal_id="reader",
                scopes=frozenset({"releases:read"}),
            ),
            body={"version": "0.1.0"},
            idempotency_key="denied",
        )
        assert denied.status_code == 403
    finally:
        runtime.close()

    args = build_parser().parse_args(
        [
            "releases",
            "prepare",
            "P7_RELEASE",
            "--config",
            "platform.json",
            "--body",
            "release.json",
        ]
    )
    assert args.command == "releases"
    assert args.releases_command == "prepare"
    assert args.project_id == "P7_RELEASE"
