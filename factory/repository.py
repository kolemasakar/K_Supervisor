from __future__ import annotations

from pathlib import Path, PurePosixPath
from subprocess import CalledProcessError, run
from typing import Protocol

from .contracts import BootstrapFile, ManagedRepository, RepositoryOperationContext, RepositoryTarget
from .errors import RepositoryConflictError, RepositoryUnavailableError


class RepositoryAdapter(Protocol):
    provider: str

    def prepare(
        self,
        target: RepositoryTarget,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> ManagedRepository: ...
    def apply_files(
        self,
        repository: ManagedRepository,
        files: tuple[BootstrapFile, ...],
        *,
        context: RepositoryOperationContext | None = None,
    ) -> None: ...
    def list_files(
        self,
        repository: ManagedRepository,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> tuple[str, ...]: ...
    def read_text_file(
        self,
        repository: ManagedRepository,
        path: str,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> str | None: ...


class FilesystemRepositoryAdapter:
    provider = "FILESYSTEM"
    supports_operation_context = True

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def prepare(
        self,
        target: RepositoryTarget,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> ManagedRepository:
        del context
        path = (self.root / target.name).resolve()
        if self.root != path and self.root not in path.parents:
            raise RepositoryUnavailableError("repository path escapes managed root")

        created = not path.exists()
        if created and target.provisioning != "AUTOMATABLE":
            raise RepositoryUnavailableError("repository creation requires owner action")

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

    def apply_files(
        self,
        repository: ManagedRepository,
        files: tuple[BootstrapFile, ...],
        *,
        context: RepositoryOperationContext | None = None,
    ) -> None:
        del context
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

    def list_files(
        self,
        repository: ManagedRepository,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> tuple[str, ...]:
        del context
        base = Path(repository.locator).resolve()
        return tuple(
            sorted(
                path.relative_to(base).as_posix()
                for path in base.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(base).parts
            )
        )


    def read_text_file(
        self,
        repository: ManagedRepository,
        path: str,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> str | None:
        del context
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or path in {"", "."}:
            raise RepositoryConflictError("repository read path must be relative and safe")
        base = Path(repository.locator).resolve()
        candidate = (base / Path(*pure.parts)).resolve()
        if candidate != base and base not in candidate.parents:
            raise RepositoryConflictError("repository read path escapes managed root")
        if not candidate.exists():
            return None
        if not candidate.is_file():
            raise RepositoryConflictError("repository read path is not a regular file")
        try:
            return candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RepositoryConflictError("repository reference file must be UTF-8 text") from exc
