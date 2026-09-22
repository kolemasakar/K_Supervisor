from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from access import AccessReference, SecretBackend

from .contracts import ManagedRepository, RepositoryTarget
from .errors import GitHubRepositoryError, RepositoryConflictError

GITHUB_API_ROOT = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_ACCEPT = "application/vnd.github+json"
GITHUB_USER_AGENT = "k-supervisor/0.1"


@dataclass(frozen=True)
class GitHubHttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes = b""


class GitHubTransportError(RuntimeError):
    """Transport-level failure with no provider response."""

    def __init__(self, message: str = "GitHub transport failed") -> None:
        super().__init__(message)


class GitHubTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_seconds: float,
    ) -> GitHubHttpResponse: ...


class UrllibGitHubTransport:
    """Minimal stdlib transport used by the production GitHub REST client."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_seconds: float,
    ) -> GitHubHttpResponse:
        request = Request(url, data=body, method=method, headers=dict(headers))
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return GitHubHttpResponse(
                    status=int(response.status),
                    headers={str(key): str(value) for key, value in response.headers.items()},
                    body=response.read(),
                )
        except HTTPError as exc:
            try:
                payload = exc.read()
            finally:
                exc.close()
            return GitHubHttpResponse(
                status=int(exc.code),
                headers={str(key): str(value) for key, value in exc.headers.items()},
                body=payload,
            )
        except (URLError, TimeoutError, socket.timeout, OSError) as exc:
            raise GitHubTransportError() from exc


class GitHubRestClient:
    """Credential-safe, versioned GitHub REST client with injectable transport."""

    def __init__(
        self,
        secret_backend: SecretBackend,
        *,
        transport: GitHubTransport | None = None,
        api_root: str = GITHUB_API_ROOT,
        api_version: str = GITHUB_API_VERSION,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not api_root.startswith("https://"):
            raise ValueError("GitHub API root must use HTTPS")
        if timeout_seconds <= 0:
            raise ValueError("GitHub timeout must be positive")
        self.secret_backend = secret_backend
        self.transport = transport or UrllibGitHubTransport()
        self.api_root = api_root.rstrip("/")
        self.api_version = api_version
        self.timeout_seconds = timeout_seconds

    def request_json(
        self,
        method: str,
        path: str,
        *,
        credential_ref: AccessReference,
        payload: dict | None = None,
    ) -> dict | list:
        if not path.startswith("/"):
            raise ValueError("GitHub REST path must be absolute")

        try:
            token = self.secret_backend.resolve(credential_ref).reveal()
        except Exception as exc:
            raise GitHubRepositoryError(
                "GITHUB_CREDENTIAL_UNAVAILABLE",
                "GitHub credential is unavailable",
                category="AUTHENTICATION",
                retryable=False,
            ) from exc
        if not token:
            raise GitHubRepositoryError(
                "GITHUB_CREDENTIAL_UNAVAILABLE",
                "GitHub credential is unavailable",
                category="AUTHENTICATION",
                retryable=False,
            )

        headers = {
            "Accept": GITHUB_ACCEPT,
            "Authorization": f"Bearer {token}",
            "User-Agent": GITHUB_USER_AGENT,
            "X-GitHub-Api-Version": self.api_version,
        }
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

        try:
            response = self.transport.request(
                method.upper(),
                self.api_root + path,
                headers=headers,
                body=body,
                timeout_seconds=self.timeout_seconds,
            )
        except GitHubTransportError as exc:
            raise GitHubRepositoryError(
                "GITHUB_NETWORK_ERROR",
                "GitHub request failed before a provider response was received",
                category="NETWORK",
                retryable=True,
            ) from exc

        if not 200 <= response.status < 300:
            self._raise_response_error(response)

        if not response.body:
            return {}
        try:
            decoded = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubRepositoryError(
                "GITHUB_RESPONSE_INVALID",
                "GitHub returned an invalid response",
                category="PROVIDER_UNAVAILABLE",
                retryable=False,
                status_code=response.status,
            ) from exc
        if not isinstance(decoded, (dict, list)):
            raise GitHubRepositoryError(
                "GITHUB_RESPONSE_INVALID",
                "GitHub returned an invalid response",
                category="PROVIDER_UNAVAILABLE",
                retryable=False,
                status_code=response.status,
            )
        return decoded

    @staticmethod
    def _header_map(headers: Mapping[str, str]) -> dict[str, str]:
        return {str(key).lower(): str(value) for key, value in headers.items()}

    @classmethod
    def _raise_response_error(cls, response: GitHubHttpResponse) -> None:
        headers = cls._header_map(response.headers)
        retry_after = cls._safe_int(headers.get("retry-after"))
        rate_limit_reset = cls._safe_int(headers.get("x-ratelimit-reset"))
        remaining = headers.get("x-ratelimit-remaining")

        if response.status == 401:
            raise GitHubRepositoryError(
                "GITHUB_AUTHENTICATION_FAILED",
                "GitHub authentication failed",
                category="AUTHENTICATION",
                status_code=response.status,
            )

        if response.status in {403, 429} and (
            response.status == 429 or remaining == "0" or retry_after is not None
        ):
            raise GitHubRepositoryError(
                "GITHUB_RATE_LIMITED",
                "GitHub rate limit blocked the request",
                category="RATE_LIMIT",
                retryable=True,
                status_code=response.status,
                retry_after_seconds=retry_after,
                rate_limit_reset=rate_limit_reset,
            )

        if response.status == 403:
            raise GitHubRepositoryError(
                "GITHUB_PERMISSION_DENIED",
                "GitHub permission denied the request",
                category="PERMISSION",
                status_code=response.status,
            )
        if response.status == 404:
            raise GitHubRepositoryError(
                "GITHUB_NOT_FOUND",
                "GitHub resource was not found",
                category="NOT_FOUND",
                status_code=response.status,
            )
        if response.status == 409:
            raise GitHubRepositoryError(
                "GITHUB_CONFLICT",
                "GitHub reported a resource conflict",
                category="CONFLICT",
                status_code=response.status,
            )
        if response.status == 422:
            raise GitHubRepositoryError(
                "GITHUB_VALIDATION_FAILED",
                "GitHub rejected the request",
                category="VALIDATION",
                status_code=response.status,
            )
        if response.status >= 500:
            raise GitHubRepositoryError(
                "GITHUB_PROVIDER_UNAVAILABLE",
                "GitHub provider is temporarily unavailable",
                category="PROVIDER_UNAVAILABLE",
                retryable=True,
                status_code=response.status,
            )
        raise GitHubRepositoryError(
            "GITHUB_PROVIDER_ERROR",
            "GitHub request failed",
            category="PROVIDER_ERROR",
            retryable=False,
            status_code=response.status,
        )

    @staticmethod
    def _safe_int(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None


class GitHubRepositoryResolver:
    """Read-only repository resolver used before material GitHub writes are enabled."""

    def __init__(self, client: GitHubRestClient) -> None:
        self.client = client

    def resolve(self, target: RepositoryTarget) -> ManagedRepository:
        if target.provider != "GITHUB":
            raise ValueError("GitHub resolver requires a GITHUB repository target")
        if target.owner is None:
            raise ValueError("GitHub repository target requires explicit repository_owner")
        if target.credential_ref is None:
            raise GitHubRepositoryError(
                "GITHUB_CREDENTIAL_REQUIRED",
                "GitHub repository target requires a protected credential reference",
                category="AUTHENTICATION",
            )

        owner = quote(target.owner, safe="")
        name = quote(target.name, safe="")
        data = self.client.request_json(
            "GET",
            f"/repos/{owner}/{name}",
            credential_ref=target.credential_ref,
        )

        full_name = str(data.get("full_name") or "")
        expected = f"{target.owner}/{target.name}"
        if full_name.casefold() != expected.casefold():
            raise RepositoryConflictError("resolved GitHub repository identity conflicts with target")

        if bool(data.get("archived")):
            raise RepositoryConflictError("resolved GitHub repository is archived")
        if bool(data.get("disabled")):
            raise RepositoryConflictError("resolved GitHub repository is disabled")

        visibility = str(
            data.get("visibility")
            or ("PRIVATE" if bool(data.get("private")) else "PUBLIC")
        ).upper()
        if visibility != target.visibility:
            raise RepositoryConflictError("resolved GitHub repository visibility conflicts with target")

        default_branch = str(data.get("default_branch") or "")
        if default_branch != target.default_branch:
            raise RepositoryConflictError("resolved GitHub repository default branch conflicts with target")

        repository_id = data.get("id")
        if repository_id is None:
            raise GitHubRepositoryError(
                "GITHUB_RESPONSE_INVALID",
                "GitHub repository response is missing repository identity",
                category="PROVIDER_UNAVAILABLE",
                status_code=200,
            )

        locator = str(data.get("html_url") or f"https://github.com/{expected}")
        return ManagedRepository(
            provider="GITHUB",
            repository_id=f"github:{repository_id}",
            locator=locator,
            default_branch=default_branch,
            created=False,
        )
