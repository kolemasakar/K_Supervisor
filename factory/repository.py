from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Protocol

from .contracts import BootstrapFile, ManagedRepository, RepositoryTarget
from .errors import RepositoryConflictError, RepositoryUnavailableError


class RepositoryAdapter(Protocol):
    provider: str

    def prepare(self, target: RepositoryTarget) -> ManagedRepository: ...
    def apply_files(self, repository: ManagedRepository, files: tuple[BootstrapFile, ...]) -> None: ...
    def list_files(self, repository: ManagedRepository) -> tuple[str, ...]: ...


class FilesystemRepositoryAdapter:
    provider = "FILESYSTEM"

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def prepare(self, target: RepositoryTarget) -> ManagedRepository:
        path = (self.root / target.name).resolve()
        if self.root != path and self.root not in path.parents:
            raise RepositoryUnavailableError("repository path escapes managed root")

        created = not path.exists()
        if created:
            path.mkdir(parents=True)
            try:
                run(
                    ["git", "init", "-b", target.default_branch],
                    cwd=path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except (CalledProcessError, FileNotFoundError) as exc:
                raise RepositoryUnavailableError("git repository initialization failed") from exc
        elif not path.is_dir() or not (path / ".git").is_dir():
            raise RepositoryUnavailableError("existing target is not a Git repository")

        return ManagedRepository(
            provider=self.provider,
            repository_id=f"filesystem:{target.name}",
            locator=str(path),
            default_branch=target.default_branch,
            created=created,
        )

    def apply_files(self, repository: ManagedRepository, files: tuple[BootstrapFile, ...]) -> None:
        base = Path(repository.locator).resolve()
        for item in files:
            path = (base / item.path).resolve()
            if base not in path.parents and path != base:
                raise RepositoryConflictError("generated path escapes repository")
            if path.exists():
                if not path.is_file() or path.read_text(encoding="utf-8") != item.content:
                    raise RepositoryConflictError(f"existing file conflicts with bootstrap: {item.path}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(item.content, encoding="utf-8")

    def list_files(self, repository: ManagedRepository) -> tuple[str, ...]:
        base = Path(repository.locator).resolve()
        return tuple(
            sorted(
                path.relative_to(base).as_posix()
                for path in base.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(base).parts
            )
        )
