from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from factory import FilesystemRepositoryAdapter, ProjectFactory
from models.enums import ProjectLifecycleState
from service_api import (
    REPOSITORY_BOOTSTRAP_SCOPE,
    REPOSITORY_READ_SCOPE,
    ServiceApiV1,
)
from tests.phase6_support import LATER, make_project, make_spec, open_registry
from tests.v04_phase2_support import principal


def build_stack(tmp_path):
    store, projects = open_registry(tmp_path / "state.db")
    spec = make_spec()
    projects.register(make_project(spec), spec)
    project_factory = ProjectFactory(
        projects,
        (FilesystemRepositoryAdapter(tmp_path / "repos"),),
    )
    api = ServiceApiV1(
        projects,
        store,
        project_factory=project_factory,
    )
    return store, projects, project_factory, api


def test_repository_status_is_redacted_and_scope_bound(tmp_path):
    store, projects, _, api = build_stack(tmp_path)

    denied = api.dispatch(
        "GET",
        "/api/v1/projects/P6/repository",
        principal=principal("projects:read"),
    )
    assert denied.status_code == 403

    response = api.dispatch(
        "GET",
        "/api/v1/projects/P6/repository",
        principal=principal(REPOSITORY_READ_SCOPE),
    )
    assert response.status_code == 200
    data = response.body["data"]["repository"]
    assert data == {
        "configured": True,
        "provider": "FILESYSTEM",
        "owner": None,
        "name": "phase-six-demo",
        "visibility": "PRIVATE",
        "default_branch": "main",
        "provisioning": "AUTOMATABLE",
        "lifecycle_state": "APPROVED",
        "operational_state": "ACTIVE",
    }
    store.close()


def test_repository_bootstrap_is_explicit_restart_safe_service_command(tmp_path):
    store, projects, _, api = build_stack(tmp_path)
    key = "repo-bootstrap-1"

    first = api.dispatch(
        "POST",
        "/api/v1/projects/P6/repository/bootstrap",
        principal=principal(REPOSITORY_BOOTSTRAP_SCOPE),
        idempotency_key=key,
    )
    assert first.status_code == 200
    assert first.body["meta"]["idempotent_replay"] is False
    data = first.body["data"]["repository_bootstrap"]
    assert data["status"] == "BOOTSTRAPPED"
    assert data["repository"]["provider"] == "FILESYSTEM"
    assert "README.md" in data["files"]
    assert projects.get("P6").lifecycle_state == ProjectLifecycleState.BOOTSTRAPPED

    replay = api.dispatch(
        "POST",
        "/api/v1/projects/P6/repository/bootstrap",
        principal=principal(REPOSITORY_BOOTSTRAP_SCOPE),
        idempotency_key=key,
    )
    assert replay.status_code == 200
    assert replay.body["meta"]["idempotent_replay"] is True
    assert replay.body["data"] == first.body["data"]
    commands = store.list_service_commands("P6")
    assert len(commands) == 1
    assert commands[0].status.value == "SUCCEEDED"
    store.close()


def test_repository_bootstrap_replay_survives_store_reopen(tmp_path):
    path = tmp_path / "state.db"
    repos = tmp_path / "repos"

    store, projects = open_registry(path)
    spec = make_spec()
    projects.register(make_project(spec), spec)
    api = ServiceApiV1(
        projects,
        store,
        project_factory=ProjectFactory(
            projects,
            (FilesystemRepositoryAdapter(repos),),
        ),
    )
    key = "repo-reopen-1"
    first = api.dispatch(
        "POST",
        "/api/v1/projects/P6/repository/bootstrap",
        principal=principal(REPOSITORY_BOOTSTRAP_SCOPE),
        idempotency_key=key,
    )
    assert first.status_code == 200
    first_data = first.body["data"]
    store.close()

    reopened, reopened_projects = open_registry(path)
    recovered_api = ServiceApiV1(
        reopened_projects,
        reopened,
        project_factory=ProjectFactory(
            reopened_projects,
            (FilesystemRepositoryAdapter(repos),),
        ),
    )
    try:
        replay = recovered_api.dispatch(
            "POST",
            "/api/v1/projects/P6/repository/bootstrap",
            principal=principal(REPOSITORY_BOOTSTRAP_SCOPE),
            idempotency_key=key,
        )
        assert replay.status_code == 200
        assert replay.body["meta"]["idempotent_replay"] is True
        assert replay.body["data"] == first_data
        commands = reopened.list_service_commands("P6")
        assert len(commands) == 1
        assert commands[0].status.value == "SUCCEEDED"
        assert reopened_projects.get("P6").lifecycle_state == ProjectLifecycleState.BOOTSTRAPPED
        assert len(list(repos.rglob("README.md"))) == 1
    finally:
        reopened.close()


def test_project_factory_reconciles_bootstrapped_project_without_duplicate_files(tmp_path):
    store, projects, project_factory, _ = build_stack(tmp_path)

    first = project_factory.bootstrap("P6", LATER)
    replay = project_factory.bootstrap("P6", LATER + timedelta(minutes=1))

    assert replay.repository.repository_id == first.repository.repository_id
    assert replay.files == first.files
    assert projects.get("P6").lifecycle_state == ProjectLifecycleState.BOOTSTRAPPED
    assert len(list(Path(first.repository.locator).rglob("README.md"))) == 1
    store.close()


def test_repository_bootstrap_requires_write_scope_and_idempotency_key(tmp_path):
    store, projects, _, api = build_stack(tmp_path)

    denied = api.dispatch(
        "POST",
        "/api/v1/projects/P6/repository/bootstrap",
        principal=principal(REPOSITORY_READ_SCOPE),
        idempotency_key="denied",
    )
    assert denied.status_code == 403
    assert projects.get("P6").lifecycle_state == ProjectLifecycleState.APPROVED

    missing_key = api.dispatch(
        "POST",
        "/api/v1/projects/P6/repository/bootstrap",
        principal=principal(REPOSITORY_BOOTSTRAP_SCOPE),
    )
    assert missing_key.status_code == 400
    assert missing_key.body["error"]["code"] == "IDEMPOTENCY_REQUIRED"
    assert projects.get("P6").lifecycle_state == ProjectLifecycleState.APPROVED
    store.close()


def test_repository_owner_action_response_preserves_human_action_id(tmp_path):
    store, projects = open_registry(tmp_path / "state.db")
    spec = make_spec(provider="GITHUB", provisioning="OWNER_ACTION_REQUIRED")
    projects.register(make_project(spec), spec)

    from supervisor.human_intervention import HumanInterventionBroker

    human = HumanInterventionBroker(store, projects)
    factory = ProjectFactory(projects, (), human)
    api = ServiceApiV1(
        projects,
        store,
        human=human,
        project_factory=factory,
    )

    response = api.dispatch(
        "POST",
        "/api/v1/projects/P6/repository/bootstrap",
        principal=principal(REPOSITORY_BOOTSTRAP_SCOPE),
        idempotency_key="owner-blocked",
    )

    assert response.status_code == 409
    assert response.body["error"]["code"] == "OWNER_ACTION_REQUIRED"
    action_id = response.body["error"]["details"]["human_action_id"]
    assert action_id
    assert store.get_human_action(action_id) is not None
    command = store.list_service_commands("P6")[0]
    assert command.status.value == "PENDING"
    store.close()
