from __future__ import annotations

import hashlib
import sqlite3

import persistence.operations as persistence_operations
from datetime import datetime, timedelta, timezone

import pytest

from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import (
    SQLiteOperationalError,
    SQLiteOperationalManager,
    SQLitePersistenceStore,
)
from registry import ProjectRegistry
from tests.test_v03_phase1_persistence_hardening import create_legacy_v1_database

NOW = datetime(2026, 9, 16, 18, 10, tzinfo=timezone.utc)


def _project(project_id: str) -> Project:
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.IDEA,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_online_backup_is_verified_and_reopenable(tmp_path):
    path = tmp_path / "state.db"
    backup = tmp_path / "backups" / "state.sqlite"
    with SQLitePersistenceStore(path) as store:
        store.save_project(_project("P8_BACKUP"))
        manifest = SQLiteOperationalManager(store).backup_to(backup)
        assert manifest.schema_version == "2"
        assert manifest.integrity_ok
        assert manifest.sha256 == _sha256(backup)

    verified = SQLiteOperationalManager.verify_backup(
        backup, expected_sha256=manifest.sha256
    )
    assert verified == manifest
    with SQLitePersistenceStore(backup) as recovered:
        assert recovered.get_project("P8_BACKUP") == _project("P8_BACKUP")


def test_restore_uses_qualified_candidate_and_recovers_backup_state(tmp_path):
    path = tmp_path / "state.db"
    backup = tmp_path / "state.backup.db"
    store = SQLitePersistenceStore(path)
    store.initialize()
    registry = ProjectRegistry(store)
    registry.register(_project("P8_RESTORE"))
    manager = SQLiteOperationalManager(store)
    manifest = manager.backup_to(backup)
    registry.transition_operational(
        "P8_RESTORE", ProjectOperationalState.PAUSED, NOW + timedelta(minutes=1)
    )
    assert registry.get("P8_RESTORE").operational_state == ProjectOperationalState.PAUSED
    store.close()

    report = manager.restore_from(backup, expected_sha256=manifest.sha256)
    assert report.source_schema_version == "2"
    assert report.target_schema_version == "2"
    assert report.integrity_ok

    with SQLitePersistenceStore(path) as restored:
        assert (
            restored.get_project("P8_RESTORE").operational_state
            == ProjectOperationalState.ACTIVE
        )


def test_corrupt_restore_is_rejected_without_touching_authoritative_store(tmp_path):
    path = tmp_path / "state.db"
    bad = tmp_path / "corrupt.db"
    store = SQLitePersistenceStore(path)
    with store:
        store.save_project(_project("P8_SAFE"))
    before = _sha256(path)
    bad.write_bytes(b"not a sqlite database")

    manager = SQLiteOperationalManager(store)
    with pytest.raises(SQLiteOperationalError, match="invalid SQLite backup"):
        manager.restore_from(bad)

    assert _sha256(path) == before
    with SQLitePersistenceStore(path) as recovered:
        assert recovered.get_project("P8_SAFE") == _project("P8_SAFE")


def test_upgrade_qualification_migrates_copy_but_not_source(tmp_path):
    legacy = tmp_path / "legacy-v1.db"
    create_legacy_v1_database(legacy)
    before = _sha256(legacy)

    report = SQLiteOperationalManager.qualify_upgrade(legacy)

    assert report.source_schema_version == "1"
    assert report.target_schema_version == "2"
    assert report.source_sha256 == before
    assert report.integrity_ok
    assert _sha256(legacy) == before
    connection = sqlite3.connect(legacy)
    try:
        version = connection.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert version == "1"


def test_unsupported_upgrade_fails_without_source_mutation(tmp_path):
    future = tmp_path / "future.db"
    connection = sqlite3.connect(future)
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
    before = _sha256(future)

    with pytest.raises(SQLiteOperationalError, match="unsupported schema version"):
        SQLiteOperationalManager.qualify_upgrade(future)

    assert _sha256(future) == before


def test_restore_requires_closed_authoritative_store(tmp_path):
    path = tmp_path / "state.db"
    backup = tmp_path / "state.backup.db"
    with SQLitePersistenceStore(path) as store:
        store.save_project(_project("P8_CLOSED"))
        manager = SQLiteOperationalManager(store)
        manager.backup_to(backup)
        with pytest.raises(SQLiteOperationalError, match="close authoritative store"):
            manager.restore_from(backup)


def test_restore_replace_failure_leaves_authoritative_store_untouched(tmp_path, monkeypatch):
    path = tmp_path / "state.db"
    backup = tmp_path / "state.backup.db"
    store = SQLitePersistenceStore(path)
    with store:
        store.save_project(_project("P8_REPLACE_FAIL"))
        manifest = SQLiteOperationalManager(store).backup_to(backup)
    before = _sha256(path)
    manager = SQLiteOperationalManager(store)

    def fail_replace(source, destination):
        raise OSError("injected replace failure")

    monkeypatch.setattr(persistence_operations.os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected replace failure"):
        manager.restore_from(backup, expected_sha256=manifest.sha256)

    assert _sha256(path) == before
    with SQLitePersistenceStore(path) as recovered:
        assert recovered.get_project("P8_REPLACE_FAIL") == _project("P8_REPLACE_FAIL")
