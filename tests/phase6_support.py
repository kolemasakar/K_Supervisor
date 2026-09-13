from datetime import datetime, timezone
from pathlib import Path

from models.enums import ProjectLifecycleState, ProjectOperationalState, ProjectSpecStatus
from models.project import Project, ProjectSpec
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry

NOW = datetime(2026, 9, 13, 17, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 13, 17, 5, tzinfo=timezone.utc)


def make_spec(
    *,
    project_id: str = "P6",
    spec_id: str = "PS6",
    status: ProjectSpecStatus = ProjectSpecStatus.APPROVED,
    provider: str = "FILESYSTEM",
    provisioning: str = "AUTOMATABLE",
) -> ProjectSpec:
    approved_at = NOW if status == ProjectSpecStatus.APPROVED else None
    return ProjectSpec(
        project_spec_id=spec_id,
        project_id=project_id,
        spec_version="1.0",
        status=status,
        created_at=NOW,
        updated_at=NOW,
        approved_at=approved_at,
        name="Phase Six Demo",
        short_name="phase-six-demo",
        purpose="Validate automated project bootstrap.",
        problem_statement="A managed project repository must be created from an approved specification.",
        project_type="AI",
        success_criteria=("bootstrap is reproducible",),
        first_working_criteria=("baseline repository validates",),
        documentation={"roadmap_required": True},
        repository={
            "repository_provider": provider,
            "repository_name": "phase-six-demo",
            "repository_visibility": "PRIVATE",
            "ci_required": True,
            "provisioning": provisioning,
        },
        architecture={"architecture_style": "MODULAR"},
        agents={"required_capabilities": ["planning.project"]},
        notifications={"primary_channel": "EMAIL"},
    )


def make_project(spec: ProjectSpec | None = None) -> Project:
    return Project(
        project_id="P6",
        name="Phase Six Demo",
        active_project_spec_id=spec.project_spec_id if spec and spec.status == ProjectSpecStatus.APPROVED else None,
        lifecycle_state=ProjectLifecycleState.APPROVED,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def open_registry(path: Path) -> tuple[SQLitePersistenceStore, ProjectRegistry]:
    store = SQLitePersistenceStore(path)
    store.initialize()
    return store, ProjectRegistry(store)
