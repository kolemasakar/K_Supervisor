from __future__ import annotations

from observability.reliability import ReliabilityValidator
from persistence import SQLiteOperationalManager, SQLitePersistenceStore

OPERATIONAL_SCHEMA_CURRENT = "operational:schema-current"
OPERATIONAL_STORE_INTEGRITY = "operational:store-integrity"
OPERATIONAL_RECOVERY_INTEGRITY = "operational:recovery-integrity"


class OperationalReleaseEvidenceProvider:
    """Derive reserved release-readiness criteria from authoritative runtime state."""

    def __init__(self, store, projects):
        self.store = store
        self.projects = projects

    def collect(self, project_id: str) -> tuple[str, ...]:
        satisfied: list[str] = []
        if isinstance(self.store, SQLitePersistenceStore):
            try:
                manifest = SQLiteOperationalManager(self.store).inspect_current()
            except Exception:
                manifest = None
            if manifest is not None and manifest.integrity_ok:
                satisfied.append(OPERATIONAL_STORE_INTEGRITY)
                if manifest.schema_version == SQLitePersistenceStore.SCHEMA_VERSION:
                    satisfied.append(OPERATIONAL_SCHEMA_CURRENT)

        try:
            snapshot = self.projects.recover(project_id)
            reliability = ReliabilityValidator(self.store).check(project_id)
        except Exception:
            snapshot = None
            reliability = None
        if (
            snapshot is not None
            and snapshot.project.project_id == project_id
            and snapshot.active_spec is not None
            and reliability is not None
            and reliability.passed
        ):
            satisfied.append(OPERATIONAL_RECOVERY_INTEGRITY)
        return tuple(satisfied)
