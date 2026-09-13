from datetime import datetime, timezone

from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry

NOW = datetime(2026, 9, 13, 18, 0, tzinfo=timezone.utc)


def make_project(project_id: str, state=ProjectOperationalState.ACTIVE) -> Project:
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.BUILDING,
        operational_state=state,
        created_at=NOW,
        updated_at=NOW,
    )


def open_projects(tmp_path, states=None):
    states = states or {
        "P1": ProjectOperationalState.ACTIVE,
        "P2": ProjectOperationalState.ACTIVE,
    }
    store = SQLitePersistenceStore(tmp_path / "scheduler.db")
    store.initialize()
    projects = ProjectRegistry(store)
    for project_id, state in states.items():
        projects.register(make_project(project_id, state))
    return store, projects
