from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .sqlite_store import SQLitePersistenceStore


class SQLiteOperationalError(RuntimeError):
    pass


@dataclass(frozen=True)
class SQLiteBackupManifest:
    path: Path
    schema_version: str
    sha256: str
    size_bytes: int
    integrity_ok: bool


@dataclass(frozen=True)
class SQLiteUpgradeQualification:
    source_schema_version: str
    target_schema_version: str
    source_sha256: str
    qualified_sha256: str
    integrity_ok: bool


class SQLiteOperationalManager:
    """Operational safety boundary for SQLite backup, restore and upgrade qualification."""

    def __init__(self, store: SQLitePersistenceStore):
        self.store = store

    def inspect_current(self) -> SQLiteBackupManifest:
        if not self.store.is_initialized:
            raise SQLiteOperationalError("persistence store must be initialized")
        integrity = self.store.conn.execute("PRAGMA integrity_check").fetchone()
        integrity_ok = bool(integrity and str(integrity[0]).lower() == "ok")
        if not integrity_ok:
            raise SQLiteOperationalError("authoritative SQLite store failed integrity_check")
        path = self.store.path
        # WAL may contain committed pages not yet checkpointed; checksum is informational here.
        return SQLiteBackupManifest(
            path=path,
            schema_version=self.store.schema_version,
            sha256=self._sha256(path) if path.exists() else "",
            size_bytes=path.stat().st_size if path.exists() else 0,
            integrity_ok=True,
        )

    def backup_to(self, destination: str | Path) -> SQLiteBackupManifest:
        if not self.store.is_initialized:
            raise SQLiteOperationalError("persistence store must be initialized")
        destination = Path(destination)
        if destination.resolve() == self.store.path.resolve():
            raise SQLiteOperationalError("backup destination must differ from authoritative store")
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".backup.tmp", dir=destination.parent
        )
        os.close(fd)
        temp = Path(temp_name)
        try:
            target = sqlite3.connect(temp)
            try:
                self.store.conn.backup(target)
                target.commit()
            finally:
                target.close()
            manifest = self.verify_backup(temp)
            os.replace(temp, destination)
            return SQLiteBackupManifest(
                path=destination,
                schema_version=manifest.schema_version,
                sha256=manifest.sha256,
                size_bytes=manifest.size_bytes,
                integrity_ok=manifest.integrity_ok,
            )
        except BaseException:
            temp.unlink(missing_ok=True)
            raise

    @classmethod
    def verify_backup(
        cls,
        path: str | Path,
        *,
        expected_sha256: str | None = None,
    ) -> SQLiteBackupManifest:
        path = Path(path)
        if not path.is_file():
            raise SQLiteOperationalError(f"backup file does not exist: {path}")
        digest = cls._sha256(path)
        if expected_sha256 is not None and digest != expected_sha256:
            raise SQLiteOperationalError("backup SHA-256 does not match expected value")
        try:
            connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
            try:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if not integrity or str(integrity[0]).lower() != "ok":
                    raise SQLiteOperationalError("backup failed SQLite integrity_check")
                row = connection.execute(
                    "SELECT value FROM schema_meta WHERE key='schema_version'"
                ).fetchone()
                if row is None:
                    raise SQLiteOperationalError("backup has no persistence schema version")
                schema_version = str(row[0])
            finally:
                connection.close()
        except SQLiteOperationalError:
            raise
        except sqlite3.Error as exc:
            raise SQLiteOperationalError(f"invalid SQLite backup: {exc}") from exc
        return SQLiteBackupManifest(
            path=path,
            schema_version=schema_version,
            sha256=digest,
            size_bytes=path.stat().st_size,
            integrity_ok=True,
        )

    @classmethod
    def qualify_upgrade(cls, path: str | Path) -> SQLiteUpgradeQualification:
        source = cls.verify_backup(path)
        source_hash_before = source.sha256
        candidate, report = cls._qualified_candidate(Path(path))
        try:
            if cls._sha256(Path(path)) != source_hash_before:
                raise SQLiteOperationalError("upgrade qualification modified source backup")
            return report
        finally:
            candidate.unlink(missing_ok=True)

    def restore_from(
        self,
        backup_path: str | Path,
        *,
        expected_sha256: str | None = None,
    ) -> SQLiteUpgradeQualification:
        if self.store.is_initialized:
            raise SQLiteOperationalError("close authoritative store before restore")
        source = self.verify_backup(backup_path, expected_sha256=expected_sha256)
        candidate, report = self._qualified_candidate(source.path, destination_dir=self.store.path.parent)
        self.store.path.parent.mkdir(parents=True, exist_ok=True)
        rollback_dir = Path(tempfile.mkdtemp(prefix=".ksupervisor-restore-", dir=self.store.path.parent))
        originals: list[tuple[Path, Path]] = []
        replaced = False
        try:
            for current in self._database_family(self.store.path):
                if current.exists():
                    saved = rollback_dir / current.name
                    shutil.copy2(current, saved)
                    originals.append((current, saved))
            os.replace(candidate, self.store.path)
            replaced = True
            self._remove_sidecars(self.store.path)
            restored = self.verify_backup(self.store.path, expected_sha256=report.qualified_sha256)
            if restored.schema_version != SQLitePersistenceStore.SCHEMA_VERSION:
                raise SQLiteOperationalError("restored store is not on current schema")
            return report
        except BaseException:
            if replaced:
                self.store.path.unlink(missing_ok=True)
                self._remove_sidecars(self.store.path)
                for current, saved in originals:
                    shutil.copy2(saved, current)
            raise
        finally:
            candidate.unlink(missing_ok=True)
            shutil.rmtree(rollback_dir, ignore_errors=True)

    @classmethod
    def _qualified_candidate(
        cls,
        source_path: Path,
        *,
        destination_dir: Path | None = None,
    ) -> tuple[Path, SQLiteUpgradeQualification]:
        source = cls.verify_backup(source_path)
        directory = destination_dir or source_path.parent
        directory.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=".ksupervisor-upgrade-", suffix=".sqlite", dir=directory
        )
        os.close(fd)
        candidate = Path(temp_name)
        try:
            shutil.copy2(source_path, candidate)
            try:
                with SQLitePersistenceStore(candidate) as qualified:
                    target_version = qualified.schema_version
                    integrity = qualified.conn.execute("PRAGMA integrity_check").fetchone()
                    if not integrity or str(integrity[0]).lower() != "ok":
                        raise SQLiteOperationalError(
                            "qualified candidate failed SQLite integrity_check"
                        )
            except SQLiteOperationalError:
                raise
            except Exception as exc:
                raise SQLiteOperationalError(f"upgrade qualification failed: {exc}") from exc
            manifest = cls.verify_backup(candidate)
            if target_version != SQLitePersistenceStore.SCHEMA_VERSION:
                raise SQLiteOperationalError(
                    f"qualified schema {target_version} is not current "
                    f"{SQLitePersistenceStore.SCHEMA_VERSION}"
                )
            return candidate, SQLiteUpgradeQualification(
                source_schema_version=source.schema_version,
                target_schema_version=target_version,
                source_sha256=source.sha256,
                qualified_sha256=manifest.sha256,
                integrity_ok=True,
            )
        except BaseException:
            candidate.unlink(missing_ok=True)
            raise

    @staticmethod
    def _database_family(path: Path) -> tuple[Path, Path, Path]:
        return path, Path(f"{path}-wal"), Path(f"{path}-shm")

    @classmethod
    def _remove_sidecars(cls, path: Path) -> None:
        for sidecar in cls._database_family(path)[1:]:
            sidecar.unlink(missing_ok=True)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
