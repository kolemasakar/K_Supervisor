from __future__ import annotations

import gc
import sqlite3
import warnings
from datetime import datetime, timezone

import pytest

from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore

NOW = datetime(2026, 9, 14, 3, 15, tzinfo=timezone.utc)


def make_project(project_id: str) -> Project:
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.IDEA,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def create_legacy_v1_database(path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE schema_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_meta(key,value) VALUES('schema_version','1')"
        )
        connection.execute(
            "CREATE TABLE resources("
            "kind TEXT NOT NULL,"
            "resource_id TEXT NOT NULL,"
            "project_id TEXT NOT NULL,"
            "payload TEXT NOT NULL,"
            "updated_at TEXT NOT NULL,"
            "PRIMARY KEY(kind,resource_id))"
        )
        connection.execute(
            "CREATE TABLE events("
            "event_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "kind TEXT NOT NULL,"
            "project_id TEXT NOT NULL,"
            "occurred_at TEXT NOT NULL,"
            "payload TEXT NOT NULL)"
        )
        project = make_project("LEGACY")
        connection.execute(
            "INSERT INTO resources(kind,resource_id,project_id,payload,updated_at) "
            "VALUES(?,?,?,?,?)",
            (
                "project",
                project.project_id,
                project.project_id,
                project.model_dump_json(),
                NOW.isoformat(),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def test_context_manager_owns_connection_lifecycle(tmp_path):
    path = tmp_path / "state.db"
    store = SQLitePersistenceStore(path)

    assert not store.is_initialized
    with store as opened:
        assert opened is store
        assert store.is_initialized
        store.save_project(make_project("P1"))

    assert not store.is_initialized
    with pytest.raises(RuntimeError, match="not initialized"):
        _ = store.conn


def test_initialize_is_idempotent_and_close_is_idempotent(tmp_path):
    store = SQLitePersistenceStore(tmp_path / "state.db")
    store.initialize()
    connection = store.conn

    store.initialize()
    assert store.conn is connection

    store.close()
    store.close()
    assert not store.is_initialized


def test_legacy_v1_schema_migrates_forward_and_preserves_data(tmp_path):
    path = tmp_path / "legacy.db"
    create_legacy_v1_database(path)

    with SQLitePersistenceStore(path) as store:
        assert store.schema_version == store.SCHEMA_VERSION == "2"
        assert store.get_project("LEGACY") == make_project("LEGACY")
        layout = store.conn.execute(
            "SELECT value FROM schema_meta WHERE key='storage_layout'"
        ).fetchone()
        assert layout["value"] == "resources-events-v1"
        index = store.conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name='idx_resources_kind_updated'"
        ).fetchone()
        assert index["name"] == "idx_resources_kind_updated"


def test_unsupported_schema_fails_closed_without_rewriting_version(tmp_path):
    path = tmp_path / "future.db"
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE schema_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_meta(key,value) VALUES('schema_version','999')"
        )
        connection.commit()
    finally:
        connection.close()

    store = SQLitePersistenceStore(path)
    with pytest.raises(RuntimeError, match="unsupported schema version"):
        store.initialize()
    assert not store.is_initialized

    connection = sqlite3.connect(path)
    try:
        version = connection.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert version == "999"


def test_failed_transaction_rolls_back_authoritative_write(tmp_path):
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        with pytest.raises(RuntimeError, match="force rollback"):
            with store.transaction():
                store.save_project(make_project("ROLLBACK"))
                raise RuntimeError("force rollback")

        assert store.get_project("ROLLBACK") is None


def test_two_store_instances_can_write_same_database_sequentially(tmp_path):
    path = tmp_path / "state.db"
    first = SQLitePersistenceStore(path)
    second = SQLitePersistenceStore(path)
    try:
        first.initialize()
        second.initialize()
        first.save_project(make_project("P1"))
        second.save_project(make_project("P2"))

        assert {item.project_id for item in first.list_projects()} == {"P1", "P2"}
        assert {item.project_id for item in second.list_projects()} == {"P1", "P2"}
    finally:
        second.close()
        first.close()


def test_finalizer_prevents_unclosed_sqlite_resource_warning(tmp_path):
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", ResourceWarning)
        store = SQLitePersistenceStore(tmp_path / "state.db")
        store.initialize()
        store.save_project(make_project("GC"))
        del store
        gc.collect()

    sqlite_warnings = [
        item
        for item in captured
        if item.category is ResourceWarning and "sqlite3.Connection" in str(item.message)
    ]
    assert sqlite_warnings == []
