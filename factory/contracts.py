from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from access import AccessReference
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
    credential_ref: AccessReference | None = None

    @classmethod
    def from_spec(cls, spec: ProjectSpec) -> "RepositoryTarget":
        data = spec.repository
        name = str(data.get("repository_name") or data.get("name") or spec.short_name).strip()
        if not name or "/" in name or "\\" in name:
            raise ValueError("repository_name must be a single path segment")
        provider = str(data.get("repository_provider") or data.get("provider") or "FILESYSTEM").strip().upper()
        owner_value = data.get("repository_owner") or data.get("owner")
        owner = None if owner_value is None else str(owner_value).strip()
        if owner == "":
            owner = None
        if owner is not None and ("/" in owner or "\\" in owner):
            raise ValueError("repository_owner must be a single path segment")

        visibility = str(data.get("repository_visibility") or data.get("visibility") or "PRIVATE").strip().upper()
        if visibility not in {"PUBLIC", "PRIVATE", "INTERNAL"}:
            raise ValueError("repository_visibility must be PUBLIC, PRIVATE or INTERNAL")

        provisioning = str(data.get("provisioning") or "AUTOMATABLE").strip().upper()
        if provider == "GITHUB" and provisioning == "AUTOMATABLE" and owner is None:
            raise ValueError("automatable GitHub repository requires explicit repository_owner")

        credential_value = data.get("repository_credential_ref") or data.get("credential_ref")
        credential_ref = None
        if credential_value is not None:
            credential_ref = AccessReference(uri=str(credential_value))

        return cls(
            provider=provider,
            owner=owner,
            name=name,
            visibility=visibility,
            url=data.get("repository_url") or data.get("url"),
            default_branch=str(data.get("default_branch") or "main").strip() or "main",
            ci_required=bool(data.get("ci_required", True)),
            provisioning=provisioning,
            credential_ref=credential_ref,
        )


@dataclass(frozen=True)
class RepositoryOperationContext:
    project_id: str
    project_spec_id: str
    idempotency_key: str


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
