from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from factory.contracts import BootstrapFile, RepositoryTarget
from factory.repository import FilesystemRepositoryAdapter
from models.enums import (
    HumanActionStatus,
    ProjectLifecycleState,
    ProjectOperationalState,
    ProjectSpecStatus,
    ReleaseStatus,
)
from models.project import Project, ProjectSpec
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry
from release_manager import (
    OPERATIONAL_RECOVERY_INTEGRITY,
    OPERATIONAL_SCHEMA_CURRENT,
    OPERATIONAL_STORE_INTEGRITY,
    ReleaseManager,
    ReleaseNotReadyError,
)
from supervisor.human_intervention import HumanInterventionBroker

NOW = datetime(2026, 9, 16, 18, 30, tzinfo=timezone.utc)
OPERATIONAL_CRITERIA = (
    OPERATIONAL_SCHEMA_CURRENT,
    OPERATIONAL_STORE_INTEGRITY,
    OPERATIONAL_RECOVERY_INTEGRITY,
)


def _spec(project_id: str, *, criteria=OPERATIONAL_CRITERIA) -> ProjectSpec:
    return ProjectSpec(
        project_spec_id=f"SPEC_{project_id}",
        project_id=project_id,
        spec_version="1.0",
        status=ProjectSpecStatus.APPROVED,
        created_at=NOW,
        updated_at=NOW,
        approved_at=NOW,
        name=f"Phase 8 {project_id}",
        short_name=project_id.lower().replace("_", "-"),
        purpose="Qualify operational release readiness.",
        problem_statement="Release readiness must use authoritative operational evidence.",
        project_type="AI",
        success_criteria=("owner-controlled release",),
        first_working_criteria=("working path exists",),
        documentation={"required_documents": ["README.md", "ARCHITECTURE.md", "ROADMAP.md"]},
        repository={"repository_provider": "FILESYSTEM"},
        architecture={"architecture_style": "MODULAR"},
        notifications={"primary_channel": "EMAIL"},
        release={
            "release_targets": ["PACKAGE_INDEX"],
            "release_readiness_criteria": list(criteria),
            "publication_owner": "OWNER",
        },
    )


def _repository(tmp_path, project_id: str):
    repos = FilesystemRepositoryAdapter(tmp_path / "repos")
    repository = repos.prepare(
        RepositoryTarget(
            provider="FILESYSTEM",
            owner=None,
            name=project_id.lower().replace("_", "-"),
            visibility="PRIVATE",
            url=None,
            default_branch="main",
            ci_required=True,
            provisioning="AUTOMATABLE",
        )
    )
    repos.apply_files(
        repository,
        tuple(
            BootstrapFile(path, f"# {path}\n")
            for path in ("README.md", "ARCHITECTURE.md", "ROADMAP.md")
        ),
    )
    return repos, repository


def _advance_to_first_working(registry: ProjectRegistry, project_id: str) -> None:
    states = (
        ProjectLifecycleState.ONBOARDING,
        ProjectLifecycleState.SPEC_REVIEW,
        ProjectLifecycleState.APPROVED,
        ProjectLifecycleState.PROVISIONING,
        ProjectLifecycleState.BOOTSTRAPPED,
        ProjectLifecycleState.BUILDING,
        ProjectLifecycleState.VALIDATING,
        ProjectLifecycleState.FIRST_WORKING,
    )
    for index, state in enumerate(states, start=1):
        registry.transition_lifecycle(
            project_id,
            state,
            f"Phase 8 qualification -> {state.value}",
            "PHASE8_QUALIFICATION",
            NOW + timedelta(minutes=index),
        )


def test_approved_projectspec_reaches_release_ready_with_operational_evidence(tmp_path):
    path = tmp_path / "state.db"
    store = SQLitePersistenceStore(path)
    store.initialize()
    registry = ProjectRegistry(store)
    project = Project(
        project_id="P8_FULL",
        name="Phase 8 Full Lifecycle",
        lifecycle_state=ProjectLifecycleState.IDEA,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )
    registry.register(project)
    registry.transition_lifecycle(
        project.project_id,
        ProjectLifecycleState.ONBOARDING,
        "onboarding",
        "PHASE8_QUALIFICATION",
        NOW + timedelta(minutes=1),
    )
    registry.transition_lifecycle(
        project.project_id,
        ProjectLifecycleState.SPEC_REVIEW,
        "spec review",
        "PHASE8_QUALIFICATION",
        NOW + timedelta(minutes=2),
    )
    spec = _spec(project.project_id)
    registry.activate_spec(project.project_id, spec, NOW + timedelta(minutes=3))
    for index, state in enumerate(
        (
            ProjectLifecycleState.APPROVED,
            ProjectLifecycleState.PROVISIONING,
            ProjectLifecycleState.BOOTSTRAPPED,
            ProjectLifecycleState.BUILDING,
            ProjectLifecycleState.VALIDATING,
            ProjectLifecycleState.FIRST_WORKING,
        ),
        start=4,
    ):
        registry.transition_lifecycle(
            project.project_id,
            state,
            f"qualification -> {state.value}",
            "PHASE8_QUALIFICATION",
            NOW + timedelta(minutes=index),
        )

    human = HumanInterventionBroker(store, registry)
    repos, repository = _repository(tmp_path, project.project_id)
    manager = ReleaseManager(store, registry, repos, human)
    outcome = manager.handle_first_working(
        project.project_id,
        "0.1.0",
        repository,
        NOW + timedelta(minutes=11),
    )

    assert all(report.ready for report in outcome.reports)
    assert registry.get(project.project_id).lifecycle_state == ProjectLifecycleState.RELEASE_READY
    assert registry.get(project.project_id).operational_state == ProjectOperationalState.WAITING_FOR_OWNER
    assert outcome.release.status == ReleaseStatus.PUBLICATION_REQUIRED
    assert outcome.targets[0].status == ReleaseStatus.PUBLICATION_REQUIRED
    assert outcome.targets[0].human_action_id is not None
    action = store.get_human_action(outcome.targets[0].human_action_id)
    assert action.status == HumanActionStatus.WAITING_FOR_OWNER
    assert store.list_release_validation_records(project.project_id)
    store.close()

    with SQLitePersistenceStore(path) as reopened:
        recovered = ProjectRegistry(reopened).recover(project.project_id)
        assert recovered.project.lifecycle_state == ProjectLifecycleState.RELEASE_READY
        assert recovered.project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER
        assert recovered.releases[0].status == ReleaseStatus.PUBLICATION_REQUIRED
        assert recovered.release_targets[0].status == ReleaseStatus.PUBLICATION_REQUIRED
        assert recovered.human_actions[0].status == HumanActionStatus.WAITING_FOR_OWNER
        assert recovered.release_validation_records


def test_operational_provider_does_not_guess_arbitrary_readiness_criteria(tmp_path):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()
    registry = ProjectRegistry(store)
    spec = _spec("P8_EXPLICIT", criteria=("external-owner-proof",))
    project = Project(
        project_id="P8_EXPLICIT",
        name="Explicit evidence",
        active_project_spec_id=spec.project_spec_id,
        lifecycle_state=ProjectLifecycleState.FIRST_WORKING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )
    registry.register(project, spec)
    human = HumanInterventionBroker(store, registry)
    repos, repository = _repository(tmp_path, project.project_id)
    manager = ReleaseManager(store, registry, repos, human)

    with pytest.raises(ReleaseNotReadyError):
        manager.handle_first_working(
            project.project_id,
            "0.1.0",
            repository,
            NOW + timedelta(minutes=1),
        )

    outcome = manager.handle_first_working(
        project.project_id,
        "0.1.0",
        repository,
        NOW + timedelta(minutes=2),
        satisfied_criteria=("external-owner-proof",),
    )
    assert outcome.release.status == ReleaseStatus.PUBLICATION_REQUIRED
    store.close()
