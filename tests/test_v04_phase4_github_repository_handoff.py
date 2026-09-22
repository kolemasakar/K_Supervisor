from __future__ import annotations

import base64
import json

import pytest

from access import AccessReference, EnvironmentSecretBackend, environment_key
from factory import GitHubHttpResponse, GitHubRestClient
from providers import GitHubRepositoryProvider, ProviderExecutionError, ProviderRequest


CREDENTIAL = AccessReference(uri="secret://project/P4/github")
TOKEN = "phase4-handoff-secret"


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
        item = self.responses.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def response(status=200, body=None, headers=None):
    if isinstance(body, (dict, list)):
        raw = json.dumps(body).encode("utf-8")
    elif body is None:
        raw = b""
    else:
        raw = body
    return GitHubHttpResponse(status=status, headers=headers or {}, body=raw)


def repo_body():
    return {
        "id": 9001,
        "full_name": "ExampleOrg/demo-repo",
        "visibility": "private",
        "private": True,
        "default_branch": "main",
        "archived": False,
        "disabled": False,
        "html_url": "https://github.com/ExampleOrg/demo-repo",
    }


def ref_body(sha):
    return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": sha}}


def file_body(content):
    return {
        "type": "file",
        "encoding": "base64",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }


def provider(transport):
    backend = EnvironmentSecretBackend({environment_key(CREDENTIAL): TOKEN})
    return GitHubRepositoryProvider(
        GitHubRestClient(backend, transport=transport, timeout_seconds=3)
    )


def request(operation, payload, *, key="handoff-key"):
    return ProviderRequest(
        project_id="P4",
        operation=operation,
        payload={
            "owner": "ExampleOrg",
            "name": "demo-repo",
            "visibility": "PRIVATE",
            "default_branch": "main",
            "provisioning": "AUTOMATABLE",
            **payload,
        },
        access_refs=(CREDENTIAL,),
        request_id="REQ_PHASE4_HANDOFF",
        agent_id="agent.policy",
        capability_id="policy.test",
        capability_version="1.0.0",
        idempotency_key=key,
    )


def test_empty_repository_bootstrap_initializes_then_commits_remaining_files():
    files = [
        {"path": "README.md", "content": "# Demo\n"},
        {"path": "docs/VISION.md", "content": "# Vision\n"},
    ]
    transport = FakeTransport(
        response(body=repo_body()),
        response(404, body={"message": "missing ref"}),
        response(201, body={"commit": {"sha": "c1"}}),
        response(body=ref_body("c1")),
        response(404, body={"message": "missing file"}),
        response(body={"tree": {"sha": "t1"}}),
        response(201, body={"sha": "b2"}),
        response(201, body={"sha": "t2"}),
        response(201, body={"sha": "c2"}),
        response(body=ref_body("c2")),
    )

    result = provider(transport).execute(
        request(
            "bootstrap_files",
            {"files": files, "commit_message": "Bootstrap demo"},
        )
    )

    assert result.payload["commit_sha"] == "c2"
    assert result.payload["created_files"] == ["README.md", "docs/VISION.md"]
    assert result.payload["noop"] is False
    methods = [item["method"] for item in transport.calls]
    assert methods == ["GET", "GET", "PUT", "GET", "GET", "GET", "POST", "POST", "POST", "PATCH"]
    patch = json.loads(transport.calls[-1]["body"])
    assert patch == {"force": False, "sha": "c2"}
    assert TOKEN not in repr(result.model_dump())


def test_identical_bootstrap_replay_is_noop_without_writes():
    files = [
        {"path": "README.md", "content": "# Demo\n"},
        {"path": "docs/VISION.md", "content": "# Vision\n"},
    ]
    transport = FakeTransport(
        response(body=repo_body()),
        response(body=ref_body("c2")),
        response(body=file_body("# Demo\n")),
        response(body=file_body("# Vision\n")),
    )

    result = provider(transport).execute(request("bootstrap_files", {"files": files}))

    assert result.payload["commit_sha"] == "c2"
    assert result.payload["created_files"] == []
    assert result.payload["noop"] is True
    assert [item["method"] for item in transport.calls] == ["GET", "GET", "GET", "GET"]


def test_bootstrap_conflict_never_overwrites_owner_content():
    transport = FakeTransport(
        response(body=repo_body()),
        response(body=ref_body("base")),
        response(body=file_body("owner-authored\n")),
    )

    with pytest.raises(ProviderExecutionError) as raised:
        provider(transport).execute(
            request(
                "bootstrap_files",
                {"files": [{"path": "README.md", "content": "generated\n"}]},
            )
        )

    assert raised.value.code == "GITHUB_REPOSITORY_CONFLICT"
    assert raised.value.category == "conflict"
    assert [item["method"] for item in transport.calls] == ["GET", "GET", "GET"]


def test_handoff_creates_deterministic_branch_commit_and_pull_request():
    transport = FakeTransport(
        response(body=repo_body()),
        response(body=ref_body("base0")),
        response(404, body={"message": "missing work ref"}),
        response(201, body=ref_body("base0")),
        response(body=ref_body("base0")),
        response(404, body={"message": "missing file"}),
        response(body={"tree": {"sha": "tree0"}}),
        response(201, body={"sha": "blob1"}),
        response(201, body={"sha": "tree1"}),
        response(201, body={"sha": "commit1"}),
        response(body=ref_body("commit1")),
        response(body=[]),
        response(
            201,
            body={
                "number": 17,
                "html_url": "https://github.com/ExampleOrg/demo-repo/pull/17",
                "state": "open",
            },
        ),
    )

    result = provider(transport).execute(
        request(
            "handoff_pull_request",
            {
                "files": [{"path": "docs/CHANGE.md", "content": "governed\n"}],
                "commit_message": "Prepare governed change",
                "pull_request_title": "Governed change",
            },
            key="logical-handoff-17",
        )
    )

    assert result.payload["branch"].startswith("k-supervisor/")
    assert result.payload["commit_sha"] == "commit1"
    assert result.payload["pull_request_number"] == 17
    assert result.metadata["recovered"] is False
    assert transport.calls[3]["method"] == "POST"
    assert "/git/refs" in transport.calls[3]["url"]
    assert json.loads(transport.calls[10]["body"]) == {"force": False, "sha": "commit1"}
    assert transport.calls[-1]["method"] == "POST"
    assert transport.calls[-1]["url"].endswith("/pulls")


def test_existing_divergent_handoff_branch_is_conflict_not_overwrite():
    transport = FakeTransport(
        response(body=repo_body()),
        response(body=ref_body("base0")),
        response(body=ref_body("other-head")),
        response(body=file_body("different\n")),
    )

    with pytest.raises(ProviderExecutionError) as raised:
        provider(transport).execute(
            request(
                "handoff_pull_request",
                {"files": [{"path": "docs/CHANGE.md", "content": "intended\n"}]},
                key="same-logical-operation",
            )
        )

    assert raised.value.code == "GITHUB_BRANCH_CONFLICT"
    assert [item["method"] for item in transport.calls] == ["GET", "GET", "GET", "GET"]


def test_tag_create_replay_and_divergence_are_safe():
    commit_sha = "a" * 40

    create_transport = FakeTransport(
        response(body=repo_body()),
        response(404, body={"message": "missing tag"}),
        response(201, body={"ref": "refs/tags/v1.0.0", "object": {"sha": commit_sha}}),
    )
    created = provider(create_transport).execute(
        request("create_tag", {"tag": "v1.0.0", "commit_sha": commit_sha})
    )
    assert created.payload == {"tag": "v1.0.0", "commit_sha": commit_sha, "created": True}

    replay_transport = FakeTransport(
        response(body=repo_body()),
        response(body={"ref": "refs/tags/v1.0.0", "object": {"sha": commit_sha}}),
    )
    replay = provider(replay_transport).execute(
        request("create_tag", {"tag": "v1.0.0", "commit_sha": commit_sha})
    )
    assert replay.payload["created"] is False
    assert replay.metadata["recovered"] is True

    conflict_transport = FakeTransport(
        response(body=repo_body()),
        response(body={"ref": "refs/tags/v1.0.0", "object": {"sha": "b" * 40}}),
    )
    with pytest.raises(ProviderExecutionError) as raised:
        provider(conflict_transport).execute(
            request("create_tag", {"tag": "v1.0.0", "commit_sha": commit_sha})
        )
    assert raised.value.code == "GITHUB_TAG_CONFLICT"


def test_file_operation_rejects_unsafe_paths_before_material_write():
    transport = FakeTransport(response(body=repo_body()))

    with pytest.raises(ProviderExecutionError) as raised:
        provider(transport).execute(
            request(
                "bootstrap_files",
                {"files": [{"path": "../escape.txt", "content": "bad"}]},
            )
        )

    assert raised.value.code == "GITHUB_INVALID_REQUEST"
    assert len(transport.calls) == 1
