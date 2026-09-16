from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TypeVar

from pydantic import BaseModel

from models.agent import AgentRunResult
from models.artifact import ArtifactReference
from models.audit import AuditEvent
from models.control import RuntimeIdempotencyRecord
from models.side_effect import SideEffectExecutionRecord
from models.intervention import (
    HumanActionRequest,
    NotificationDeliveryAttempt,
    NotificationEvent,
)
from models.lifecycle import ProjectLifecycleTransition
from models.observability_records import RoutingRecord, ReleaseValidationRecord
from models.operational import ProjectOperationalTransition
from models.project import Project, ProjectSpec
from models.release import Release, ReleaseTarget
from models.task import Task, WorkflowRun
from policy.contracts import ApprovalRecord, PolicyDecision
from .base import PersistenceConflictError, PersistenceStore

T = TypeVar("T", bound=BaseModel)


class SQLitePersistenceStore(PersistenceStore):
    """SQLite persistence backend with explicit connection and schema ownership."""

    SCHEMA_VERSION = "2"
    INITIAL_SCHEMA_VERSION = "1"
    BUSY_TIMEOUT_MS = 5_000

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("persistence store is not initialized")
        return self._conn

    @property
    def is_initialized(self) -> bool:
        return self._conn is not None

    @property
    def schema_version(self) -> str:
        row = self.conn.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()
        if row is None:
            raise RuntimeError("persistence schema version is not initialized")
        return str(row["value"])

    def __enter__(self) -> "SQLitePersistenceStore":
        self.initialize()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def initialize(self) -> None:
        if self._conn is not None:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=self.BUSY_TIMEOUT_MS / 1_000)
        connection.row_factory = sqlite3.Row
        self._conn = connection
        try:
            self._configure_connection()
            self._initialize_schema()
        except BaseException:
            self.close()
            raise

    def _configure_connection(self) -> None:
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute(f"PRAGMA busy_timeout={self.BUSY_TIMEOUT_MS}")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA synchronous=NORMAL")

    def _initialize_schema(self) -> None:
        with self.transaction():
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_meta("
                "key TEXT PRIMARY KEY,value TEXT NOT NULL)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS resources("
                "kind TEXT NOT NULL,"
                "resource_id TEXT NOT NULL,"
                "project_id TEXT NOT NULL,"
                "payload TEXT NOT NULL,"
                "updated_at TEXT NOT NULL,"
                "PRIMARY KEY(kind,resource_id))"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_resources_project_kind "
                "ON resources(project_id,kind)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS events("
                "event_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "kind TEXT NOT NULL,"
                "project_id TEXT NOT NULL,"
                "occurred_at TEXT NOT NULL,"
                "payload TEXT NOT NULL)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_project_kind "
                "ON events(project_id,kind,event_id)"
            )
            row = self.conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()
            if row is None:
                self.conn.execute(
                    "INSERT INTO schema_meta(key,value) VALUES('schema_version',?)",
                    (self.INITIAL_SCHEMA_VERSION,),
                )
            self._migrate_to_current()

    def _migrate_to_current(self) -> None:
        version = self.schema_version
        while version != self.SCHEMA_VERSION:
            if version == "1":
                self._migrate_v1_to_v2()
                version = "2"
                continue
            raise RuntimeError(
                f"unsupported schema version: {version}; "
                f"supported current version: {self.SCHEMA_VERSION}"
            )

    def _migrate_v1_to_v2(self) -> None:
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_resources_kind_updated "
            "ON resources(kind,updated_at)"
        )
        self.conn.execute(
            "INSERT INTO schema_meta(key,value) VALUES('storage_layout',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("resources-events-v1",),
        )
        self.conn.execute(
            "UPDATE schema_meta SET value='2' WHERE key='schema_version'"
        )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.conn
        if connection.in_transaction:
            yield connection
            return

        connection.execute("BEGIN IMMEDIATE")
        try:
            yield connection
        except BaseException:
            connection.rollback()
            raise
        else:
            connection.commit()

    def close(self) -> None:
        connection = self._conn
        if connection is None:
            return
        self._conn = None
        try:
            if connection.in_transaction:
                connection.rollback()
        finally:
            connection.close()

    @staticmethod
    def _json(value: BaseModel) -> str:
        return json.dumps(
            value.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )

    def _save(
        self,
        kind,
        resource_id,
        project_id,
        value,
        immutable=False,
        commit=True,
    ):
        if commit:
            with self.transaction():
                return self._save(
                    kind,
                    resource_id,
                    project_id,
                    value,
                    immutable=immutable,
                    commit=False,
                )

        payload = self._json(value)
        row = self.conn.execute(
            "SELECT payload FROM resources WHERE kind=? AND resource_id=?",
            (kind, resource_id),
        ).fetchone()
        if row is not None and immutable:
            if row["payload"] != payload:
                raise PersistenceConflictError(
                    f"immutable {kind} already exists: {resource_id}"
                )
            return

        stamp = str(
            getattr(value, "updated_at", getattr(value, "created_at", ""))
        )
        self.conn.execute(
            "INSERT INTO resources VALUES(?,?,?,?,?) "
            "ON CONFLICT(kind,resource_id) DO UPDATE SET "
            "project_id=excluded.project_id,"
            "payload=excluded.payload,"
            "updated_at=excluded.updated_at",
            (kind, resource_id, project_id, payload, stamp),
        )

    def _create(self, kind, resource_id, project_id, value, commit=True):
        if commit:
            with self.transaction():
                return self._create(kind, resource_id, project_id, value, commit=False)
        payload = self._json(value)
        stamp = str(getattr(value, "updated_at", getattr(value, "created_at", "")))
        try:
            self.conn.execute(
                "INSERT INTO resources(kind,resource_id,project_id,payload,updated_at) "
                "VALUES(?,?,?,?,?)",
                (kind, resource_id, project_id, payload, stamp),
            )
        except sqlite3.IntegrityError as exc:
            raise PersistenceConflictError(f"{kind} already exists: {resource_id}") from exc

    def _get(self, kind, resource_id, cls: type[T]) -> T | None:
        row = self.conn.execute(
            "SELECT payload FROM resources WHERE kind=? AND resource_id=?",
            (kind, resource_id),
        ).fetchone()
        return None if row is None else cls.model_validate_json(row["payload"])

    def _list(self, kind, project_id, cls: type[T]) -> tuple[T, ...]:
        rows = self.conn.execute(
            "SELECT payload FROM resources "
            "WHERE kind=? AND project_id=? ORDER BY rowid",
            (kind, project_id),
        ).fetchall()
        return tuple(cls.model_validate_json(row["payload"]) for row in rows)

    def _event(self, kind, project_id, occurred_at, value, commit=True):
        if commit:
            with self.transaction():
                return self._event(
                    kind, project_id, occurred_at, value, commit=False
                )
        self.conn.execute(
            "INSERT INTO events(kind,project_id,occurred_at,payload) "
            "VALUES(?,?,?,?)",
            (kind, project_id, occurred_at, self._json(value)),
        )

    def _events(self, kind, project_id, cls: type[T]) -> tuple[T, ...]:
        rows = self.conn.execute(
            "SELECT payload FROM events "
            "WHERE kind=? AND project_id=? ORDER BY event_id",
            (kind, project_id),
        ).fetchall()
        return tuple(cls.model_validate_json(row["payload"]) for row in rows)

    def _audit(self, value: AuditEvent) -> None:
        self._event(
            "audit_event",
            value.project_id,
            value.occurred_at.isoformat(),
            value,
            False,
        )

    def save_project(self, value): self._save("project", value.project_id, value.project_id, value)
    def save_project_with_audit(self, value, audit):
        with self.transaction():
            self._save("project", value.project_id, value.project_id, value, commit=False)
            self._audit(audit)
    def get_project(self, project_id): return self._get("project", project_id, Project)
    def list_projects(self):
        rows = self.conn.execute("SELECT payload FROM resources WHERE kind='project' ORDER BY rowid").fetchall()
        return tuple(Project.model_validate_json(row["payload"]) for row in rows)
    def save_project_spec(self, value): self._save("project_spec", value.project_spec_id, value.project_id, value, True)
    def get_project_spec(self, project_spec_id): return self._get("project_spec", project_spec_id, ProjectSpec)
    def list_project_specs(self, project_id): return self._list("project_spec", project_id, ProjectSpec)
    def append_lifecycle_transition(self, value): self._event("lifecycle_transition", value.project_id, value.timestamp.isoformat(), value)
    def apply_lifecycle_transition(self, project, value, audit=None):
        with self.transaction():
            self._event("lifecycle_transition", value.project_id, value.timestamp.isoformat(), value, False)
            self._save("project", project.project_id, project.project_id, project, commit=False)
            if audit is not None:
                self._audit(audit)
    def list_lifecycle_transitions(self, project_id): return self._events("lifecycle_transition", project_id, ProjectLifecycleTransition)
    def append_operational_transition(self, value): self._event("operational_transition", value.project_id, value.timestamp.isoformat(), value)
    def apply_operational_transition(self, project, value, audit=None):
        with self.transaction():
            self._event("operational_transition", value.project_id, value.timestamp.isoformat(), value, False)
            self._save("project", project.project_id, project.project_id, project, commit=False)
            if audit is not None:
                self._audit(audit)
    def list_operational_transitions(self, project_id): return self._events("operational_transition", project_id, ProjectOperationalTransition)
    def save_task(self, value): self._save("task", value.task_id, value.project_id, value)
    def get_task(self, task_id): return self._get("task", task_id, Task)
    def list_tasks(self, project_id): return self._list("task", project_id, Task)
    def save_workflow_run(self, value): self._save("workflow_run", value.workflow_run_id, value.project_id, value)
    def list_workflow_runs(self, project_id): return self._list("workflow_run", project_id, WorkflowRun)
    def save_agent_run(self, value): self._save("agent_run", value.run_id, value.project_id, value)
    def list_agent_runs(self, project_id): return self._list("agent_run", project_id, AgentRunResult)
    def save_artifact(self, value): self._save("artifact", value.artifact_id, value.project_id, value, True)
    def list_artifacts(self, project_id): return self._list("artifact", project_id, ArtifactReference)
    def save_release(self, value): self._save("release", value.release_id, value.project_id, value)
    def get_release(self, release_id): return self._get("release", release_id, Release)
    def list_releases(self, project_id): return self._list("release", project_id, Release)
    def save_release_target(self, value): self._save("release_target", value.release_target_id, value.project_id, value)
    def get_release_target(self, release_target_id): return self._get("release_target", release_target_id, ReleaseTarget)
    def list_release_targets(self, project_id): return self._list("release_target", project_id, ReleaseTarget)
    def save_human_action(self, value, audit=None):
        if audit is None:
            self._save("human_action", value.human_action_id, value.project_id, value)
            return
        with self.transaction():
            self._save("human_action", value.human_action_id, value.project_id, value, commit=False)
            self._audit(audit)
    def get_human_action(self, human_action_id): return self._get("human_action", human_action_id, HumanActionRequest)
    def list_human_actions(self, project_id): return self._list("human_action", project_id, HumanActionRequest)
    def save_notification(self, value): self._save("notification", value.notification_id, value.project_id, value, True)
    def get_notification(self, notification_id): return self._get("notification", notification_id, NotificationEvent)
    def list_notifications(self, project_id): return self._list("notification", project_id, NotificationEvent)
    def append_notification_delivery_attempt(self, value): self._event("notification_delivery_attempt", value.project_id, value.created_at.isoformat(), value)
    def list_notification_delivery_attempts(self, project_id): return self._events("notification_delivery_attempt", project_id, NotificationDeliveryAttempt)
    def apply_human_action_operational_transition(self, action, project, transition, audit=None):
        with self.transaction():
            self._save("human_action", action.human_action_id, action.project_id, action, commit=False)
            self._event("operational_transition", transition.project_id, transition.timestamp.isoformat(), transition, False)
            self._save("project", project.project_id, project.project_id, project, commit=False)
            if audit is not None:
                self._audit(audit)
    def save_approval(self, value, audit=None):
        if audit is None:
            self._save("approval", value.approval_id, value.project_id, value)
            return
        with self.transaction():
            self._save("approval", value.approval_id, value.project_id, value, commit=False)
            self._audit(audit)
    def get_approval(self, approval_id): return self._get("approval", approval_id, ApprovalRecord)
    def list_approvals(self, project_id): return self._list("approval", project_id, ApprovalRecord)
    def save_runtime_idempotency(self, value): self._save("runtime_idempotency", value.record_id, value.project_id, value, True)
    def get_runtime_idempotency(self, record_id): return self._get("runtime_idempotency", record_id, RuntimeIdempotencyRecord)
    def list_runtime_idempotency(self, project_id): return self._list("runtime_idempotency", project_id, RuntimeIdempotencyRecord)
    def claim_side_effect_execution(self, value, audit):
        with self.transaction():
            self._create("side_effect_execution", value.execution_id, value.project_id, value, commit=False)
            self._audit(audit)
    def complete_side_effect_execution(self, value, audit):
        with self.transaction():
            self._save("side_effect_execution", value.execution_id, value.project_id, value, commit=False)
            self._audit(audit)
    def get_side_effect_execution(self, execution_id): return self._get("side_effect_execution", execution_id, SideEffectExecutionRecord)
    def list_side_effect_executions(self, project_id): return self._list("side_effect_execution", project_id, SideEffectExecutionRecord)
    def append_policy_decision(self, value): self._event("policy_decision", value.project_id, value.evaluated_at.isoformat(), value)
    def list_policy_decisions(self, project_id): return self._events("policy_decision", project_id, PolicyDecision)
    def append_audit_event(self, value): self._event("audit_event", value.project_id, value.occurred_at.isoformat(), value)
    def list_audit_events(self, project_id): return self._events("audit_event", project_id, AuditEvent)
    def append_routing_record(self, value): self._event("routing_record", value.project_id, value.created_at.isoformat(), value)
    def list_routing_records(self, project_id): return self._events("routing_record", project_id, RoutingRecord)
    def append_release_validation_record(self, value): self._event("release_validation", value.project_id, value.created_at.isoformat(), value)
    def list_release_validation_records(self, project_id): return self._events("release_validation", project_id, ReleaseValidationRecord)
