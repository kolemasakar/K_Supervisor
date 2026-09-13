from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from models.project import ProjectSpec


@dataclass(frozen=True)
class BootstrapFile:
    path: str
    content: str

    def __post_init__(self) -> None:
        pure = PurePosixPath(self.path)
        if pure.is_absolute() or ".." in pure.parts or self.path in {"", "."}:
            raise ValueError("bootstrap file path must be relative and safe")
        try:
            self.path.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("bootstrap file path must use ASCII") from exc


@dataclass(frozen=True)
class RepositoryTarget:
    provider: str
    owner: str | None
    name: str
    visibility: str
    url: str | None
    default_branch: str
    ci_required: bool
    provisioning: str

    @classmethod
    def from_spec(cls, spec: ProjectSpec) -> "RepositoryTarget":
        data = spec.repository
        name = str(data.get("repository_name") or data.get("name") or spec.short_name)
        if not name or "/" in name or "\\" in name:
            raise ValueError("repository_name must be a single path segment")
        return cls(
            provider=str(data.get("repository_provider") or data.get("provider") or "FILESYSTEM").upper(),
            owner=data.get("repository_owner") or data.get("owner"),
            name=name,
            visibility=str(data.get("repository_visibility") or data.get("visibility") or "PRIVATE").upper(),
            url=data.get("repository_url") or data.get("url"),
            default_branch=str(data.get("default_branch") or "main"),
            ci_required=bool(data.get("ci_required", True)),
            provisioning=str(data.get("provisioning") or "AUTOMATABLE").upper(),
        )


@dataclass(frozen=True)
class ManagedRepository:
    provider: str
    repository_id: str
    locator: str
    default_branch: str
    created: bool


@dataclass(frozen=True)
class BootstrapResult:
    project_id: str
    project_spec_id: str
    repository: ManagedRepository
    files: tuple[str, ...]
    status: str = "BOOTSTRAPPED"
