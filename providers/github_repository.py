from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from access import AccessReference
from factory import (
    GitHubRepositoryError,
    GitHubRepositoryResolver,
    GitHubRestClient,
    RepositoryConflictError,
    RepositoryTarget,
)
from integrations import AvailabilityReport, AvailabilityState

from .contracts import ProviderDescriptor, ProviderRequest, ProviderResponse
from .errors import ProviderExecutionError


class GitHubRepositoryProvider:
    """Provider-layer GitHub repository operations for governed SideEffectGateway use."""

    PROVIDER_ID = "github.repository"
    VERSION = "1.0"
    OPERATIONS = ("resolve_repository", "create_repository")

    def __init__(self, client: GitHubRestClient) -> None:
        self.client = client
        self.resolver = GitHubRepositoryResolver(client)
        self.descriptor = ProviderDescriptor(
            provider_id=self.PROVIDER_ID,
            version=self.VERSION,
            provider_type="REPOSITORY",
            operations=self.OPERATIONS,
            metadata={
                "api_version": client.api_version,
                "material_writes_require_gateway": True,
            },
        )

    def check_availability(self) -> AvailabilityReport:
        return AvailabilityReport(
            component_id=self.PROVIDER_ID,
            state=AvailabilityState.AVAILABLE,
            checked_at=datetime.now(timezone.utc),
            detail="credentials are resolved per governed request",
        )

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        if request.operation not in self.OPERATIONS:
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "unsupported GitHub repository operation",
                "invalid_request",
            )
        if len(request.access_refs) != 1:
            raise self._error(
                "GITHUB_CREDENTIAL_REQUIRED",
                "exactly one authorized GitHub credential reference is required",
                "configuration",
            )

        target = self._target(request.payload, request.access_refs[0])
        if request.operation == "resolve_repository":
            return self._resolve(target)
        return self._create_or_recover(target)

    def _target(self, payload: dict, credential_ref: AccessReference) -> RepositoryTarget:
        allowed = {
            "owner",
            "name",
            "visibility",
            "default_branch",
            "ci_required",
            "provisioning",
        }
        if set(payload) - allowed:
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "unsupported GitHub repository request fields",
                "invalid_request",
            )

        owner = payload.get("owner")
        name = payload.get("name")
        if not isinstance(owner, str) or not owner.strip() or "/" in owner or "\\" in owner:
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub repository owner must be an explicit path segment",
                "invalid_request",
            )
        if not isinstance(name, str) or not name.strip() or "/" in name or "\\" in name:
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub repository name must be a single path segment",
                "invalid_request",
            )

        visibility = str(payload.get("visibility") or "PRIVATE").strip().upper()
        if visibility not in {"PUBLIC", "PRIVATE", "INTERNAL"}:
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub repository visibility is invalid",
                "invalid_request",
            )
        default_branch = str(payload.get("default_branch") or "main").strip()
        if not default_branch:
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub default branch must not be empty",
                "invalid_request",
            )
        provisioning = str(payload.get("provisioning") or "AUTOMATABLE").strip().upper()
        if provisioning != "AUTOMATABLE":
            raise self._error(
                "GITHUB_OWNER_ACTION_REQUIRED",
                "GitHub repository provisioning requires owner action",
                "configuration",
            )

        return RepositoryTarget(
            provider="GITHUB",
            owner=owner.strip(),
            name=name.strip(),
            visibility=visibility,
            url=None,
            default_branch=default_branch,
            ci_required=bool(payload.get("ci_required", True)),
            provisioning=provisioning,
            credential_ref=credential_ref,
        )

    def _resolve(self, target: RepositoryTarget) -> ProviderResponse:
        try:
            repository = self.resolver.resolve(target)
        except RepositoryConflictError as exc:
            raise self._error(
                "GITHUB_REPOSITORY_CONFLICT",
                str(exc),
                "conflict",
            ) from exc
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        return self._response(repository, created=False, recovered=False)

    def _create_or_recover(self, target: RepositoryTarget) -> ProviderResponse:
        try:
            existing = self.resolver.resolve(target)
        except GitHubRepositoryError as exc:
            if exc.code != "GITHUB_NOT_FOUND":
                raise self._provider_error(exc) from exc
        except RepositoryConflictError as exc:
            raise self._error(
                "GITHUB_REPOSITORY_CONFLICT",
                str(exc),
                "conflict",
            ) from exc
        else:
            return self._response(existing, created=False, recovered=True)

        assert target.owner is not None
        assert target.credential_ref is not None
        owner_path = quote(target.owner, safe="")
        try:
            owner = self.client.request_json(
                "GET",
                f"/users/{owner_path}",
                credential_ref=target.credential_ref,
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc

        owner_type = owner.get("type")
        body = {"name": target.name}
        if target.visibility == "INTERNAL":
            body["visibility"] = "internal"
        else:
            body["private"] = target.visibility == "PRIVATE"

        if owner_type == "Organization":
            path = f"/orgs/{owner_path}/repos"
        elif owner_type == "User":
            path = "/user/repos"
        else:
            raise self._error(
                "GITHUB_OWNER_UNSUPPORTED",
                "GitHub repository owner type is unsupported",
                "validation",
            )

        try:
            self.client.request_json(
                "POST",
                path,
                credential_ref=target.credential_ref,
                payload=body,
            )
        except GitHubRepositoryError as exc:
            if exc.retryable:
                recovered = self._recover_after_uncertain_create(target)
                if recovered is not None:
                    return self._response(recovered, created=True, recovered=True)
            raise self._provider_error(exc) from exc

        try:
            repository = self.resolver.resolve(target)
        except RepositoryConflictError as exc:
            raise self._error(
                "GITHUB_REPOSITORY_CONFLICT",
                str(exc),
                "conflict",
            ) from exc
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        return self._response(repository, created=True, recovered=False)

    def _recover_after_uncertain_create(self, target: RepositoryTarget):
        try:
            return self.resolver.resolve(target)
        except GitHubRepositoryError as exc:
            if exc.code == "GITHUB_NOT_FOUND":
                return None
            raise self._provider_error(exc) from exc
        except RepositoryConflictError as exc:
            raise self._error(
                "GITHUB_REPOSITORY_CONFLICT",
                str(exc),
                "conflict",
            ) from exc

    @staticmethod
    def _response(repository, *, created: bool, recovered: bool) -> ProviderResponse:
        return ProviderResponse(
            payload={
                "repository_id": repository.repository_id,
                "locator": repository.locator,
                "default_branch": repository.default_branch,
                "created": created,
            },
            metadata={"recovered": recovered},
        )

    @classmethod
    def _provider_error(cls, error: GitHubRepositoryError) -> ProviderExecutionError:
        return cls._error(
            error.code,
            error.message,
            error.category.lower(),
            retryable=error.retryable,
            provider_code=str(error.status_code) if error.status_code is not None else None,
        )

    @staticmethod
    def _error(
        code: str,
        message: str,
        category: str,
        *,
        retryable: bool = False,
        provider_code: str | None = None,
    ) -> ProviderExecutionError:
        return ProviderExecutionError(
            code,
            message,
            category=category,
            retryable=retryable,
            provider_code=provider_code,
        )
