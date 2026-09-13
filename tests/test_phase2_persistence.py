from datetime import datetime, timezone
from pathlib import Path
import tempfile

import pytest

from models.artifact import ArtifactReference
from models.enums import (
    ProjectLifecycleState,
    ProjectOperationalState,
    ProjectSpecStatus,
    ReleaseStatus,
)
from models.project import Project, ProjectSpec
from models.release import Release
from models.task import Task, WorkflowRun
from persistence import PersistenceConflictError, SQLitePersistenceStore
from registry import ProjectRegistry

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 13, 12, 5, tzinfo=timezone.utc)


def make_project(project_id="P1"):
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.IDEA,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def make_spec(project_id="P1", spec_id="S1", version="1.0"):
    return ProjectSpec(
        project_spec_id=spec_id,
        project_id=project_id,
        spec_version=version,
        status=ProjectSpecStatus.APPROVED,
        created_at=NOW,
        updated_at=NOW,
        approved_at=NOW,
        name=project_id,
        short_name=project_id,
        purpose="test",
        problem_statement="test",
        project_type="AI",
        success_criteria=("ok",),
        first_working_criteria=("runs",),
        documentation={},
        repository={},
        architecture={},
        notifications={"primary_channel": "EMAIL"},
    )


def open_store(path):
    store = SQLitePersistenceStore(path)
    store.initialize()
    return store


def test_project_survives_restart_and_recovers():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "state.db"
        store = open_store(path)
        registry = ProjectRegistry(store)
        registry.register(make_project(), make_spec())
        registry.activate_spec("P1", make_spec(), LATER)
        registry.transition_lifecycle(
            "P1", ProjectLifecycleState.ONBOARDING, "start", "owner", LATER
        )
        store.save_task(
            Task(
                task_id="T1",
                project_id="P1",
                title="task",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        store.save_workflow_run(
            WorkflowRun(
                workflow_run_id="W1",
                project_id="P1",
                task_id="T1",
                workflow_id="wf",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        store.save_artifact(
            ArtifactReference(
                artifact_id="A1",
                project_id="P1",
                uri="artifact://a",
                created_at=NOW,
            )
        )
        store.save_release(
            Release(
                release_id="R1",
                project_id="P1",
                version="0.1",
                targets=("GPT_STORE",),
                status=ReleaseStatus.DRAFT,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        store.close()

        store = open_store(path)
        snapshot = ProjectRegistry(store).recover("P1")
        assert snapshot.project.lifecycle_state == ProjectLifecycleState.ONBOARDING
        assert snapshot.active_spec.project_spec_id == "S1"
        assert [item.task_id for item in snapshot.tasks] == ["T1"]
        assert [item.workflow_run_id for item in snapshot.workflow_runs] == ["W1"]
        assert [item.artifact_id for item in snapshot.artifacts] == ["A1"]
        assert [item.release_id for item in snapshot.releases] == ["R1"]
        assert len(snapshot.lifecycle_transitions) == 1
        store.close()


def test_multiple_projects_are_isolated():
    with tempfile.TemporaryDirectory() as directory:
        store = open_store(Path(directory) / "state.db")
        registry = ProjectRegistry(store)
        registry.register(make_project("P1"))
        registry.register(make_project("P2"))
        store.save_task(Task(task_id="T1", project_id="P1", title="one", created_at=NOW, updated_at=NOW))
        store.save_task(Task(task_id="T2", project_id="P2", title="two", created_at=NOW, updated_at=NOW))
        assert {project.project_id for project in registry.list()} == {"P1", "P2"}
        assert [task.task_id for task in registry.recover("P1").tasks] == ["T1"]
        assert [task.task_id for task in registry.recover("P2").tasks] == ["T2"]
        store.close()


def test_project_spec_history_is_immutable():
    with tempfile.TemporaryDirectory() as directory:
        store = open_store(Path(directory) / "state.db")
        registry = ProjectRegistry(store)
        registry.register(make_project())
        initial = make_spec()
        registry.add_spec(initial)
        registry.add_spec(initial)
        changed = initial.model_copy(update={"purpose": "changed"})
        with pytest.raises(PersistenceConflictError):
            registry.add_spec(changed)
        assert len(store.list_project_specs("P1")) == 1
        store.close()


def test_invalid_transition_is_rejected_without_mutation():
    with tempfile.TemporaryDirectory() as directory:
        store = open_store(Path(directory) / "state.db")
        registry = ProjectRegistry(store)
        registry.register(make_project())
        with pytest.raises(ValueError):
            registry.transition_lifecycle(
                "P1", ProjectLifecycleState.RELEASE_READY, "skip", "test", LATER
            )
        assert registry.get("P1").lifecycle_state == ProjectLifecycleState.IDEA
        assert store.list_lifecycle_transitions("P1") == ()
        store.close()
