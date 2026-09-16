from __future__ import annotations

from dataclasses import dataclass

from persistence import SQLiteOperationalManager, SQLitePersistenceStore

from .health import ComponentHealth, ServiceHealthEvaluator
from .reliability import ReliabilityValidator


@dataclass(frozen=True)
class DeploymentQualificationReport:
    ready: bool
    checks: tuple[ComponentHealth, ...]


class DeploymentQualifier:
    """Qualify persisted/runtime prerequisites without performing deployment."""

    def __init__(self, store, projects, service_health: ServiceHealthEvaluator):
        self.store = store
        self.projects = projects
        self.service_health = service_health

    def qualify(self, project_ids: tuple[str, ...] | None = None) -> DeploymentQualificationReport:
        checks: list[ComponentHealth] = []
        if isinstance(self.store, SQLitePersistenceStore):
            try:
                manifest = SQLiteOperationalManager(self.store).inspect_current()
                checks.append(
                    ComponentHealth(
                        name="sqlite-schema-current",
                        ready=manifest.schema_version == SQLitePersistenceStore.SCHEMA_VERSION,
                        detail=manifest.schema_version,
                    )
                )
                checks.append(
                    ComponentHealth(
                        name="sqlite-integrity",
                        ready=manifest.integrity_ok,
                    )
                )
            except Exception as exc:
                checks.extend(
                    (
                        ComponentHealth(
                            name="sqlite-schema-current",
                            ready=False,
                            detail=type(exc).__name__,
                        ),
                        ComponentHealth(
                            name="sqlite-integrity",
                            ready=False,
                            detail=type(exc).__name__,
                        ),
                    )
                )

        readiness = self.service_health.readiness()
        checks.append(
            ComponentHealth(
                name="service-readiness",
                ready=readiness.ready,
                detail=None if readiness.ready else "required service probe failed",
            )
        )
        checks.extend(
            ComponentHealth(
                name=f"service:{item.name}",
                ready=item.ready,
                required=item.required,
                detail=item.detail,
            )
            for item in readiness.components
        )

        ids = project_ids if project_ids is not None else tuple(
            item.project_id for item in self.projects.list()
        )
        validator = ReliabilityValidator(self.store)
        for project_id in sorted(set(ids)):
            try:
                recovered = self.projects.recover(project_id)
                recovery_ok = recovered.project.project_id == project_id
            except Exception as exc:
                recovery_ok = False
                recovery_detail = type(exc).__name__
            else:
                recovery_detail = None
            checks.append(
                ComponentHealth(
                    name=f"project-recovery:{project_id}",
                    ready=recovery_ok,
                    detail=recovery_detail,
                )
            )
            reliability = validator.check(project_id)
            checks.append(
                ComponentHealth(
                    name=f"project-integrity:{project_id}",
                    ready=reliability.passed,
                    detail="; ".join(reliability.errors) or None,
                )
            )

        return DeploymentQualificationReport(
            ready=all(item.ready for item in checks if item.required),
            checks=tuple(checks),
        )
