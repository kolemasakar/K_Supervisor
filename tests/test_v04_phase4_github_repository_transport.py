from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from access import EnvironmentSecretBackend
from factory import (
    GITHUB_API_VERSION,
    GitHubHttpResponse,
    GitHubRepositoryError,
    GitHubRepositoryResolver,
    GitHubRestClient,
    GitHubTransportError,
    RepositoryConflictError,
    RepositoryTarget,
)
from models.project import ProjectSpec
from tests.phase6_support import make_spec


TOKEN = "phase4-secret-token"
TOKEN_ENV = {"KSUP_SECRET__PROJECT_P4_GITHUB": TOKEN}


class FakeTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, *, headers, body, timeout_seconds):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        if not self.responses:
            raise AssertionError("unexpected GitHub transport call")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def response(status=200, body=None, headers=None):
    payload = b"" if body is None else json.dumps(body).encode("utf-8")
    return GitHubHttpResponse(status=status, headers=headers or {}, body=payload)


def github_spec(**repository_updates) -> ProjectSpec:
    base = make_spec(provider="GITHUB", project_id="P4", spec_id="PS4")
    repository = {
        **base.repository,
        "repository_owner": " ExampleOrg ",
        "repository_name": " demo-repo ",
        "repository_visibility": "PRIVATE",
        "default_branch": "main",
        "provisioning": "AUTOMATABLE",
        "repository_credential_ref": "secret://project/P4/github",
        **repository_updates,
    }
    for key in ("repository_credential_ref", "credential_ref"):
        if repository.get(key) is None:
            repository.pop(key, None)
    data = base.model_dump(mode="python")
    data["repository"] = repository
    return ProjectSpec.model_validate(data)


def client(transport):
    return GitHubRestClient(
        EnvironmentSecretBackend(TOKEN_ENV),
        transport=transport,
        timeout_seconds=3,
    )


def test_github_target_canonicalizes_identity_and_protected_credential_reference():
    target = RepositoryTarget.from_spec(github_spec())

    assert target.provider == "GITHUB"
    assert target.owner == "ExampleOrg"
    assert target.name == "demo-repo"
    assert target.visibility == "PRIVATE"
    assert target.default_branch == "main"
    assert target.provisioning == "AUTOMATABLE"
    assert target.credential_ref.uri == "secret://project/P4/github"
    assert TOKEN not in repr(target)


def test_automatable_github_target_requires_explicit_owner():
    spec = github_spec(repository_owner=None, owner=None)
    with pytest.raises(ValueError, match="explicit repository_owner"):
        RepositoryTarget.from_spec(spec)


def test_project_spec_rejects_plaintext_repository_credential():
    base = make_spec(provider="GITHUB", project_id="P4", spec_id="PS4")
    data = base.model_dump(mode="python")
    data["repository"] = {
        **base.repository,
        "repository_owner": "ExampleOrg",
        "repository_credential_ref": "plaintext-token",
    }
    with pytest.raises(ValidationError, match="raw access data is prohibited"):
        ProjectSpec.model_validate(data)


def test_versioned_rest_headers_and_secret_resolution_are_transport_only():
    transport = FakeTransport(response(body={"ok": True}))
    result = client(transport).request_json(
        "GET",
        "/repos/ExampleOrg/demo-repo",
        credential_ref=RepositoryTarget.from_spec(github_spec()).credential_ref,
    )

    assert result == {"ok": True}
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["method"] == "GET"
    assert call["headers"]["X-GitHub-Api-Version"] == GITHUB_API_VERSION
    assert call["headers"]["Accept"] == "application/vnd.github+json"
    assert call["headers"]["Authorization"] == f"Bearer {TOKEN}"
    assert call["body"] is None


@pytest.mark.parametrize(
    ("status", "headers", "code", "category", "retryable"),
    [
        (401, {}, "GITHUB_AUTHENTICATION_FAILED", "AUTHENTICATION", False),
        (403, {}, "GITHUB_PERMISSION_DENIED", "PERMISSION", False),
        (
            403,
            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1790000000"},
            "GITHUB_RATE_LIMITED",
            "RATE_LIMIT",
            True,
        ),
        (
            429,
            {"Retry-After": "60"},
            "GITHUB_RATE_LIMITED",
            "RATE_LIMIT",
            True,
        ),
        (404, {}, "GITHUB_NOT_FOUND", "NOT_FOUND", False),
        (409, {}, "GITHUB_CONFLICT", "CONFLICT", False),
        (422, {}, "GITHUB_VALIDATION_FAILED", "VALIDATION", False),
        (503, {}, "GITHUB_PROVIDER_UNAVAILABLE", "PROVIDER_UNAVAILABLE", True),
    ],
)
def test_rest_errors_are_safely_normalized(status, headers, code, category, retryable):
    transport = FakeTransport(
        GitHubHttpResponse(
            status=status,
            headers=headers,
            body=b'{"message":"provider detail that is not persisted"}',
        )
    )
    target = RepositoryTarget.from_spec(github_spec())

    with pytest.raises(GitHubRepositoryError) as raised:
        client(transport).request_json(
            "GET",
            "/repos/ExampleOrg/demo-repo",
            credential_ref=target.credential_ref,
        )

    error = raised.value
    assert error.code == code
    assert error.category == category
    assert error.retryable is retryable
    assert error.status_code == status
    assert TOKEN not in str(error)
    assert "provider detail" not in str(error)

    if status == 429:
        assert error.retry_after_seconds == 60
    if status == 403 and headers:
        assert error.rate_limit_reset == 1790000000


def test_transport_failure_is_retryable_and_does_not_leak_secret():
    transport = FakeTransport(GitHubTransportError("low-level network detail"))
    target = RepositoryTarget.from_spec(github_spec())

    with pytest.raises(GitHubRepositoryError) as raised:
        client(transport).request_json(
            "GET",
            "/repos/ExampleOrg/demo-repo",
            credential_ref=target.credential_ref,
        )

    assert raised.value.code == "GITHUB_NETWORK_ERROR"
    assert raised.value.category == "NETWORK"
    assert raised.value.retryable is True
    assert TOKEN not in str(raised.value)
    assert "low-level network detail" not in str(raised.value)


def test_read_only_resolver_returns_exact_existing_repository():
    transport = FakeTransport(
        response(
            body={
                "id": 12345,
                "full_name": "ExampleOrg/demo-repo",
                "visibility": "private",
                "private": True,
                "default_branch": "main",
                "archived": False,
                "disabled": False,
                "html_url": "https://github.com/ExampleOrg/demo-repo",
            }
        )
    )
    target = RepositoryTarget.from_spec(github_spec())

    repository = GitHubRepositoryResolver(client(transport)).resolve(target)

    assert repository.provider == "GITHUB"
    assert repository.repository_id == "github:12345"
    assert repository.locator == "https://github.com/ExampleOrg/demo-repo"
    assert repository.default_branch == "main"
    assert repository.created is False
    assert transport.calls[0]["url"].endswith("/repos/ExampleOrg/demo-repo")


@pytest.mark.parametrize(
    ("repository_updates", "remote_updates", "message"),
    [
        ({"repository_visibility": "PUBLIC"}, {}, "visibility"),
        ({}, {"default_branch": "develop"}, "default branch"),
        ({}, {"archived": True}, "archived"),
        ({}, {"disabled": True}, "disabled"),
        ({}, {"full_name": "OtherOrg/demo-repo"}, "identity"),
    ],
)
def test_read_only_resolver_rejects_conflicting_repository_state(
    repository_updates,
    remote_updates,
    message,
):
    payload = {
        "id": 12345,
        "full_name": "ExampleOrg/demo-repo",
        "visibility": "private",
        "private": True,
        "default_branch": "main",
        "archived": False,
        "disabled": False,
        "html_url": "https://github.com/ExampleOrg/demo-repo",
        **remote_updates,
    }
    transport = FakeTransport(response(body=payload))
    target = RepositoryTarget.from_spec(github_spec(**repository_updates))

    with pytest.raises(RepositoryConflictError, match=message):
        GitHubRepositoryResolver(client(transport)).resolve(target)


def test_resolver_requires_protected_credential_before_transport():
    transport = FakeTransport()
    target = RepositoryTarget.from_spec(
        github_spec(repository_credential_ref=None, credential_ref=None)
    )

    with pytest.raises(GitHubRepositoryError) as raised:
        GitHubRepositoryResolver(client(transport)).resolve(target)

    assert raised.value.code == "GITHUB_CREDENTIAL_REQUIRED"
    assert transport.calls == []


def test_invalid_provider_response_is_normalized_without_raw_body():
    transport = FakeTransport(
        GitHubHttpResponse(
            status=200,
            headers={},
            body=b"not-json-provider-body",
        )
    )
    target = RepositoryTarget.from_spec(github_spec())

    with pytest.raises(GitHubRepositoryError) as raised:
        GitHubRepositoryResolver(client(transport)).resolve(target)

    assert raised.value.code == "GITHUB_RESPONSE_INVALID"
    assert "not-json-provider-body" not in str(raised.value)
