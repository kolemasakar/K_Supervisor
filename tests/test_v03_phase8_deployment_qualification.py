from datetime import datetime, timezone

from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from observability import DeploymentQualifier, ServiceHealthEvaluator
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry

NOW = datetime(2026, 9, 16, 19, 30, tzinfo=timezone.utc)


def _project() -> Project:
    return Project(
        project_id="P8_DEPLOY",
        name="Deployment qualification",
        lifecycle_state=ProjectLifecycleState.BUILDING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def test_deployment_qualification_combines_store_service_and_project_integrity(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        projects = ProjectRegistry(store)
        projects.register(_project())
        health = ServiceHealthEvaluator(
            {
                "persistence": (lambda: store.is_initialized, True),
                "optional-exporter": (lambda: False, False),
            }
        )
        report = DeploymentQualifier(store, projects, health).qualify()
        assert report.ready
        checks = {item.name: item for item in report.checks}
        assert checks["sqlite-schema-current"].ready
        assert checks["sqlite-integrity"].ready
        assert checks["service-readiness"].ready
        assert checks["project-recovery:P8_DEPLOY"].ready
        assert checks["project-integrity:P8_DEPLOY"].ready
        assert checks["service:optional-exporter"].required is False


def test_deployment_qualification_fails_on_required_service_probe(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        projects = ProjectRegistry(store)
        projects.register(_project())
        health = ServiceHealthEvaluator({"required-provider": (lambda: False, True)})
        report = DeploymentQualifier(store, projects, health).qualify(("P8_DEPLOY",))
        assert not report.ready
        assert any(
            item.name == "service:required-provider" and not item.ready
            for item in report.checks
        )
