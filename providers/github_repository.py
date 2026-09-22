from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.parse import quote, urlencode

from access import AccessReference
from factory.contracts import RepositoryTarget
from factory.errors import GitHubRepositoryError, RepositoryConflictError
from factory.github import GitHubRepositoryResolver, GitHubRestClient
from integrations import AvailabilityReport, AvailabilityState

from .contracts import ProviderDescriptor, ProviderRequest, ProviderResponse
from .errors import ProviderExecutionError


class GitHubRepositoryProvider:
    """Provider-layer GitHub repository/VCS operations for governed gateway use."""

    PROVIDER_ID = "github.repository"
    VERSION = "1.0"
    OPERATIONS = (
        "resolve_repository",
        "create_repository",
        "bootstrap_files",
        "list_files",
        "read_file",
        "handoff_pull_request",
        "create_tag",
    )

    _COMMON_FIELDS = frozenset(
        {
            "owner",
            "name",
            "visibility",
            "default_branch",
            "ci_required",
            "provisioning",
        }
    )

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

        target = self._target(
            request.payload,
            request.access_refs[0],
            operation=request.operation,
        )
        if request.operation == "resolve_repository":
            return self._resolve(target)
        if request.operation == "create_repository":
            return self._create_or_recover(target)
        if request.operation == "bootstrap_files":
            return self._bootstrap_files(target, request.payload)
        if request.operation == "list_files":
            return self._list_files(target)
        if request.operation == "read_file":
            return self._read_file_operation(target, request.payload)
        if request.operation == "handoff_pull_request":
            return self._handoff_pull_request(target, request)
        return self._create_tag(target, request.payload)

    def _target(
        self,
        payload: dict,
        credential_ref: AccessReference,
        *,
        operation: str,
    ) -> RepositoryTarget:
        allowed = set(self._COMMON_FIELDS)
        if operation == "bootstrap_files":
            allowed.update({"files", "commit_message"})
        elif operation == "read_file":
            allowed.update({"path"})
        elif operation == "handoff_pull_request":
            allowed.update({"files", "commit_message", "pull_request_title", "pull_request_body"})
        elif operation == "create_tag":
            allowed.update({"tag", "commit_sha"})
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
        repository = self._resolve_managed(target)
        return self._response(repository, created=False, recovered=False)

    def _create_or_recover(self, target: RepositoryTarget) -> ProviderResponse:
        try:
            existing = self.resolver.resolve(target)
        except GitHubRepositoryError as exc:
            if exc.code != "GITHUB_NOT_FOUND":
                raise self._provider_error(exc) from exc
        except RepositoryConflictError as exc:
            raise self._conflict(exc) from exc
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
        if not isinstance(owner, dict):
            raise self._malformed("GitHub owner response is invalid")

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

        repository = self._resolve_managed(target)
        return self._response(repository, created=True, recovered=False)

    def _bootstrap_files(self, target: RepositoryTarget, payload: dict) -> ProviderResponse:
        repository = self._resolve_managed(target)
        files = self._files(payload.get("files"))
        message = self._message(payload.get("commit_message"), "Bootstrap repository")
        commit_sha, created_files, noop = self._apply_files(
            target,
            target.default_branch,
            files,
            commit_message=message,
            allow_initialize_empty=True,
        )
        return ProviderResponse(
            payload={
                "repository_id": repository.repository_id,
                "locator": repository.locator,
                "default_branch": target.default_branch,
                "commit_sha": commit_sha,
                "files": [path for path, _ in files],
                "created_files": list(created_files),
                "noop": noop,
            },
            metadata={"conflict_safe": True},
        )

    def _list_files(self, target: RepositoryTarget) -> ProviderResponse:
        self._resolve_managed(target)
        branch_sha = self._get_ref(target, "heads", target.default_branch)
        if branch_sha is None:
            return ProviderResponse(payload={"files": []}, metadata={"recursive": True})
        tree_sha = self._get_commit_tree(target, branch_sha)
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        try:
            data = self.client.request_json(
                "GET",
                f"{repo}/git/trees/{quote(tree_sha, safe='')}?recursive=1",
                credential_ref=target.credential_ref,
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        if not isinstance(data, dict):
            raise self._malformed("GitHub tree response is invalid")
        tree = data.get("tree")
        if not isinstance(tree, list):
            raise self._malformed("GitHub tree response is missing entries")
        files = []
        for item in tree:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "blob":
                continue
            path = item.get("path")
            if isinstance(path, str) and path:
                files.append(path)
        return ProviderResponse(
            payload={"files": sorted(set(files))},
            metadata={"recursive": True},
        )

    def _handoff_pull_request(
        self,
        target: RepositoryTarget,
        request: ProviderRequest,
    ) -> ProviderResponse:
        self._resolve_managed(target)
        files = self._files(request.payload.get("files"))
        message = self._message(request.payload.get("commit_message"), "K_Supervisor governed update")
        title = self._message(request.payload.get("pull_request_title"), "K_Supervisor governed update")
        body = request.payload.get("pull_request_body")
        if body is not None and not isinstance(body, str):
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "pull request body must be text",
                "invalid_request",
            )
        if not request.idempotency_key:
            raise self._error(
                "GITHUB_IDEMPOTENCY_REQUIRED",
                "governed pull-request handoff requires an idempotency key",
                "invalid_request",
            )

        base_branch = target.default_branch
        branch = self._branch_for_key(request.idempotency_key)
        base_sha = self._get_ref(target, "heads", base_branch)
        if base_sha is None:
            raise self._error(
                "GITHUB_BASE_BRANCH_MISSING",
                "GitHub default branch is missing",
                "conflict",
            )

        branch_sha = self._get_ref(target, "heads", branch)
        if branch_sha is None:
            self._create_ref(target, "heads", branch, base_sha)
            branch_sha = base_sha
        elif branch_sha != base_sha:
            states = [self._read_file(target, branch, path) for path, _ in files]
            if any(current is None or current != desired for current, (_, desired) in zip(states, files)):
                raise self._error(
                    "GITHUB_BRANCH_CONFLICT",
                    "existing governed handoff branch diverges from the intended payload",
                    "conflict",
                )

        commit_sha, _, _ = self._apply_files(
            target,
            branch,
            files,
            commit_message=message,
            allow_initialize_empty=False,
        )

        existing = self._find_open_pull_request(target, branch, base_branch)
        if existing is not None:
            return self._pull_response(branch, commit_sha, existing, recovered=True)

        assert target.credential_ref is not None
        repo = self._repo_path(target)
        try:
            created = self.client.request_json(
                "POST",
                f"{repo}/pulls",
                credential_ref=target.credential_ref,
                payload={
                    "title": title,
                    "head": branch,
                    "base": base_branch,
                    "body": body or "",
                },
            )
        except GitHubRepositoryError as exc:
            if exc.retryable:
                recovered = self._find_open_pull_request(target, branch, base_branch)
                if recovered is not None:
                    return self._pull_response(branch, commit_sha, recovered, recovered=True)
            raise self._provider_error(exc) from exc
        if not isinstance(created, dict):
            raise self._malformed("GitHub pull-request response is invalid")
        return self._pull_response(branch, commit_sha, created, recovered=False)

    def _read_file_operation(
        self,
        target: RepositoryTarget,
        payload: dict,
    ) -> ProviderResponse:
        path = payload.get("path")
        if not isinstance(path, str):
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub read-file operation requires a text path",
                "invalid_request",
            )
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or path in {"", "."}:
            raise self._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub read-file path must be relative and safe",
                "invalid_request",
            )
        canonical = pure.as_posix()
        content = self._read_file(target, target.default_branch, canonical)
        return ProviderResponse(
            payload={
                "path": canonical,
                "found": content is not None,
                "content": content,
            },
            metadata={},
        )

    def _create_tag(self, target: RepositoryTarget, payload: dict) -> ProviderResponse:
        self._resolve_managed(target)
        tag = payload.get("tag")
        commit_sha = payload.get("commit_sha")
        if not isinstance(tag, str) or not self._valid_ref_name(tag):
            raise self._error("GITHUB_INVALID_REQUEST", "GitHub tag name is invalid", "invalid_request")
        if not isinstance(commit_sha, str) or not self._valid_sha(commit_sha):
            raise self._error("GITHUB_INVALID_REQUEST", "GitHub tag commit SHA is invalid", "invalid_request")

        existing = self._get_ref(target, "tags", tag)
        if existing is not None:
            if existing != commit_sha:
                raise self._error(
                    "GITHUB_TAG_CONFLICT",
                    "existing GitHub tag points to a different commit",
                    "conflict",
                )
            return ProviderResponse(
                payload={"tag": tag, "commit_sha": commit_sha, "created": False},
                metadata={"recovered": True},
            )

        self._create_ref(target, "tags", tag, commit_sha)
        return ProviderResponse(
            payload={"tag": tag, "commit_sha": commit_sha, "created": True},
            metadata={"recovered": False},
        )

    def _apply_files(
        self,
        target: RepositoryTarget,
        branch: str,
        files: tuple[tuple[str, str], ...],
        *,
        commit_message: str,
        allow_initialize_empty: bool,
    ) -> tuple[str, tuple[str, ...], bool]:
        current_sha = self._get_ref(target, "heads", branch)
        remaining = list(files)
        created: list[str] = []

        if current_sha is None:
            if not allow_initialize_empty:
                raise self._error(
                    "GITHUB_BRANCH_MISSING",
                    "GitHub target branch is missing",
                    "conflict",
                )
            first_index = next(
                (index for index, (path, _) in enumerate(remaining) if path == "README.md"),
                0,
            )
            first_path, first_content = remaining.pop(first_index)
            self._create_initial_file(target, first_path, first_content, commit_message)
            created.append(first_path)
            current_sha = self._get_ref(target, "heads", branch)
            if current_sha is None:
                raise self._malformed("GitHub repository initialization did not create the default branch")

        missing: list[tuple[str, str]] = []
        for path, content in remaining:
            existing = self._read_file(target, branch, path)
            if existing is None:
                missing.append((path, content))
            elif existing != content:
                raise self._error(
                    "GITHUB_REPOSITORY_CONFLICT",
                    f"existing GitHub file conflicts with generated content: {path}",
                    "conflict",
                )

        if not missing:
            return current_sha, tuple(created), not created

        tree_sha = self._get_commit_tree(target, current_sha)
        entries = []
        for path, content in missing:
            blob_sha = self._create_blob(target, content)
            entries.append(
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                }
            )
        new_tree = self._create_tree(target, tree_sha, entries)
        new_commit = self._create_commit(target, new_tree, current_sha, commit_message)
        self._update_ref(target, branch, new_commit)
        created.extend(path for path, _ in missing)
        return new_commit, tuple(created), False

    def _create_initial_file(
        self,
        target: RepositoryTarget,
        path: str,
        content: str,
        message: str,
    ) -> None:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        encoded_path = self._encode_path(path)
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        }
        try:
            result = self.client.request_json(
                "PUT",
                f"{repo}/contents/{encoded_path}",
                credential_ref=target.credential_ref,
                payload=payload,
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        if not isinstance(result, dict):
            raise self._malformed("GitHub initial file response is invalid")

    def _read_file(self, target: RepositoryTarget, branch: str, path: str) -> str | None:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        encoded_path = self._encode_path(path)
        query = urlencode({"ref": branch})
        try:
            data = self.client.request_json(
                "GET",
                f"{repo}/contents/{encoded_path}?{query}",
                credential_ref=target.credential_ref,
            )
        except GitHubRepositoryError as exc:
            if exc.code == "GITHUB_NOT_FOUND":
                return None
            raise self._provider_error(exc) from exc
        if not isinstance(data, dict) or data.get("type") not in {None, "file"}:
            raise self._error(
                "GITHUB_REPOSITORY_CONFLICT",
                f"GitHub path is not a regular file: {path}",
                "conflict",
            )
        if data.get("encoding") != "base64" or not isinstance(data.get("content"), str):
            raise self._malformed("GitHub file content response is invalid")
        try:
            raw = base64.b64decode(data["content"], validate=False)
            return raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise self._malformed("GitHub file content is not valid UTF-8") from exc

    def _get_ref(self, target: RepositoryTarget, namespace: str, name: str) -> str | None:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        ref = f"{namespace}/{quote(name, safe='/')}"
        try:
            data = self.client.request_json(
                "GET",
                f"{repo}/git/ref/{ref}",
                credential_ref=target.credential_ref,
            )
        except GitHubRepositoryError as exc:
            if exc.code in {"GITHUB_NOT_FOUND", "GITHUB_CONFLICT"}:
                return None
            raise self._provider_error(exc) from exc
        if not isinstance(data, dict):
            raise self._malformed("GitHub reference response is invalid")
        obj = data.get("object")
        sha = obj.get("sha") if isinstance(obj, dict) else None
        if not isinstance(sha, str) or not sha:
            raise self._malformed("GitHub reference response is missing commit identity")
        return sha

    def _create_ref(
        self,
        target: RepositoryTarget,
        namespace: str,
        name: str,
        sha: str,
    ) -> None:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        try:
            result = self.client.request_json(
                "POST",
                f"{repo}/git/refs",
                credential_ref=target.credential_ref,
                payload={"ref": f"refs/{namespace}/{name}", "sha": sha},
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        if not isinstance(result, dict):
            raise self._malformed("GitHub create-reference response is invalid")

    def _update_ref(self, target: RepositoryTarget, branch: str, sha: str) -> None:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        encoded = quote(branch, safe="/")
        try:
            result = self.client.request_json(
                "PATCH",
                f"{repo}/git/refs/heads/{encoded}",
                credential_ref=target.credential_ref,
                payload={"sha": sha, "force": False},
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        if not isinstance(result, dict):
            raise self._malformed("GitHub update-reference response is invalid")

    def _get_commit_tree(self, target: RepositoryTarget, commit_sha: str) -> str:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        try:
            data = self.client.request_json(
                "GET",
                f"{repo}/git/commits/{quote(commit_sha, safe='')}",
                credential_ref=target.credential_ref,
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        if not isinstance(data, dict):
            raise self._malformed("GitHub commit response is invalid")
        tree = data.get("tree")
        tree_sha = tree.get("sha") if isinstance(tree, dict) else None
        if not isinstance(tree_sha, str) or not tree_sha:
            raise self._malformed("GitHub commit response is missing tree identity")
        return tree_sha

    def _create_blob(self, target: RepositoryTarget, content: str) -> str:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        try:
            data = self.client.request_json(
                "POST",
                f"{repo}/git/blobs",
                credential_ref=target.credential_ref,
                payload={"content": content, "encoding": "utf-8"},
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        return self._response_sha(data, "GitHub blob response is invalid")

    def _create_tree(self, target: RepositoryTarget, base_tree: str, entries: list[dict]) -> str:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        try:
            data = self.client.request_json(
                "POST",
                f"{repo}/git/trees",
                credential_ref=target.credential_ref,
                payload={"base_tree": base_tree, "tree": entries},
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        return self._response_sha(data, "GitHub tree response is invalid")

    def _create_commit(
        self,
        target: RepositoryTarget,
        tree_sha: str,
        parent_sha: str,
        message: str,
    ) -> str:
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        try:
            data = self.client.request_json(
                "POST",
                f"{repo}/git/commits",
                credential_ref=target.credential_ref,
                payload={"message": message, "tree": tree_sha, "parents": [parent_sha]},
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        return self._response_sha(data, "GitHub commit creation response is invalid")

    def _find_open_pull_request(
        self,
        target: RepositoryTarget,
        branch: str,
        base_branch: str,
    ) -> dict | None:
        assert target.owner is not None
        assert target.credential_ref is not None
        repo = self._repo_path(target)
        query = urlencode(
            {
                "state": "open",
                "head": f"{target.owner}:{branch}",
                "base": base_branch,
            }
        )
        try:
            data = self.client.request_json(
                "GET",
                f"{repo}/pulls?{query}",
                credential_ref=target.credential_ref,
            )
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc
        if not isinstance(data, list):
            raise self._malformed("GitHub pull-request list response is invalid")
        if not data:
            return None
        item = data[0]
        if not isinstance(item, dict):
            raise self._malformed("GitHub pull-request list entry is invalid")
        return item

    def _resolve_managed(self, target: RepositoryTarget):
        try:
            return self.resolver.resolve(target)
        except RepositoryConflictError as exc:
            raise self._conflict(exc) from exc
        except GitHubRepositoryError as exc:
            raise self._provider_error(exc) from exc

    def _recover_after_uncertain_create(self, target: RepositoryTarget):
        try:
            return self.resolver.resolve(target)
        except GitHubRepositoryError as exc:
            if exc.code == "GITHUB_NOT_FOUND":
                return None
            raise self._provider_error(exc) from exc
        except RepositoryConflictError as exc:
            raise self._conflict(exc) from exc

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

    @staticmethod
    def _pull_response(
        branch: str,
        commit_sha: str,
        data: dict,
        *,
        recovered: bool,
    ) -> ProviderResponse:
        number = data.get("number")
        html_url = data.get("html_url")
        state = data.get("state")
        if not isinstance(number, int) or not isinstance(html_url, str):
            raise GitHubRepositoryProvider._malformed("GitHub pull-request response is invalid")
        return ProviderResponse(
            payload={
                "branch": branch,
                "commit_sha": commit_sha,
                "pull_request_number": number,
                "pull_request_url": html_url,
                "pull_request_state": state if isinstance(state, str) else "open",
            },
            metadata={"recovered": recovered},
        )

    @staticmethod
    def _files(raw) -> tuple[tuple[str, str], ...]:
        if not isinstance(raw, list) or not raw:
            raise GitHubRepositoryProvider._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub file operation requires a non-empty files list",
                "invalid_request",
            )
        normalized: list[tuple[str, str]] = []
        seen: set[str] = set()
        for item in raw:
            if not isinstance(item, dict):
                raise GitHubRepositoryProvider._error(
                    "GITHUB_INVALID_REQUEST",
                    "GitHub file entry is invalid",
                    "invalid_request",
                )
            path = item.get("path")
            content = item.get("content")
            if not isinstance(path, str) or not isinstance(content, str):
                raise GitHubRepositoryProvider._error(
                    "GITHUB_INVALID_REQUEST",
                    "GitHub file entry requires text path and content",
                    "invalid_request",
                )
            pure = PurePosixPath(path)
            if pure.is_absolute() or ".." in pure.parts or path in {"", "."}:
                raise GitHubRepositoryProvider._error(
                    "GITHUB_INVALID_REQUEST",
                    "GitHub file path must be relative and safe",
                    "invalid_request",
                )
            canonical = pure.as_posix()
            if canonical in seen:
                raise GitHubRepositoryProvider._error(
                    "GITHUB_INVALID_REQUEST",
                    "GitHub file operation contains duplicate paths",
                    "invalid_request",
                )
            if len(content.encode("utf-8")) > 1024 * 1024:
                raise GitHubRepositoryProvider._error(
                    "GITHUB_INVALID_REQUEST",
                    "GitHub file content exceeds the Phase 4 per-file limit",
                    "invalid_request",
                )
            seen.add(canonical)
            normalized.append((canonical, content))
        return tuple(sorted(normalized))

    @staticmethod
    def _message(value, default: str) -> str:
        if value is None:
            return default
        if not isinstance(value, str) or not value.strip() or len(value) > 512:
            raise GitHubRepositoryProvider._error(
                "GITHUB_INVALID_REQUEST",
                "GitHub commit or pull-request title is invalid",
                "invalid_request",
            )
        return value.strip()

    @staticmethod
    def _branch_for_key(key: str) -> str:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return f"k-supervisor/{digest}"

    @staticmethod
    def _valid_ref_name(value: str) -> bool:
        if not value or value.startswith("/") or value.endswith("/"):
            return False
        forbidden = {" ", "~", "^", ":", "?", "*", "[", "\\"}
        return ".." not in value and not any(char in value for char in forbidden)

    @staticmethod
    def _valid_sha(value: str) -> bool:
        return len(value) in {40, 64} and all(char in "0123456789abcdefABCDEF" for char in value)

    @staticmethod
    def _repo_path(target: RepositoryTarget) -> str:
        assert target.owner is not None
        return f"/repos/{quote(target.owner, safe='')}/{quote(target.name, safe='')}"

    @staticmethod
    def _encode_path(path: str) -> str:
        return "/".join(quote(part, safe="") for part in PurePosixPath(path).parts)

    @staticmethod
    def _response_sha(data, message: str) -> str:
        if not isinstance(data, dict):
            raise GitHubRepositoryProvider._malformed(message)
        sha = data.get("sha")
        if not isinstance(sha, str) or not sha:
            raise GitHubRepositoryProvider._malformed(message)
        return sha

    @classmethod
    def _provider_error(cls, error: GitHubRepositoryError) -> ProviderExecutionError:
        return cls._error(
            error.code,
            error.message,
            error.category.lower(),
            retryable=error.retryable,
            provider_code=str(error.status_code) if error.status_code is not None else None,
        )

    @classmethod
    def _conflict(cls, error: Exception) -> ProviderExecutionError:
        return cls._error(
            "GITHUB_REPOSITORY_CONFLICT",
            str(error),
            "conflict",
        )

    @staticmethod
    def _malformed(message: str) -> ProviderExecutionError:
        return GitHubRepositoryProvider._error(
            "GITHUB_MALFORMED_RESPONSE",
            message,
            "malformed_response",
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
