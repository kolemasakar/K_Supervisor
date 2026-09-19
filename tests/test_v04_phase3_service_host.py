from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from threading import Event, Thread
from time import sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from pydantic import ValidationError

from access import EnvironmentSecretBackend
from ksupervisor.config import PlatformConfig, ServiceClientConfig, ServiceHostConfig
from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from service_api.client import ServiceClientV1
from service_api.host import HostLifecycle, HostState, ServiceHostApplication, create_service_host
from service_api.runtime import build_service_runtime


TOKEN = "phase3-test-token"
TOKEN_ENV = {"KSUP_SECRET__SERVICE_OWNER": TOKEN}


def _config(tmp_path, **host_updates):
    host = {
        "port": 0,
        "workers": 2,
        "socket_timeout_seconds": 2,
        "drain_timeout_seconds": 2,
        "principals": [
            {
                "principal_id": "owner",
                "scopes": ["projects:read"],
                "token_ref": {"uri": "secret://service/owner"},
            }
        ],
        **host_updates,
    }
    return PlatformConfig(
        state_db_path=str(tmp_path / "state.db"),
        service_host=host,
    )


def _get(url, *, token=None):
    headers = {} if token is None else {"Authorization": f"Bearer {token}"}
    request = Request(url, headers=headers)
    with urlopen(request, timeout=3) as response:
        return response.status, json.loads(response.read())


def test_config_is_additive_and_fails_closed_for_exposure():
    legacy = PlatformConfig()
    assert legacy.config_version == "1"
    assert legacy.service_host is None
    assert legacy.service_client is None

    with pytest.raises(ValidationError):
        ServiceHostConfig(bind_host="0.0.0.0")
    with pytest.raises(ValidationError):
        ServiceHostConfig(proxy_mode=True, trusted_proxies=())
    with pytest.raises(ValidationError):
        ServiceClientConfig(base_url="http://example.com:8080")
    with pytest.raises(ValueError):
        ServiceClientV1("http://example.com:8080", TOKEN)
    with pytest.raises(ValidationError):
        PlatformConfig(config_version="2")


def test_runtime_requires_host_auth_and_resolves_token_only_in_memory(tmp_path):
    with pytest.raises(ValueError, match="service_host"):
        build_service_runtime(PlatformConfig(state_db_path=str(tmp_path / "missing.db")))

    config = PlatformConfig(
        state_db_path=str(tmp_path / "missing-token.db"),
        service_host={
            "port": 0,
            "principals": [{
                "principal_id": "owner",
                "scopes": ["projects:read"],
                "token_ref": {"uri": "secret://service/owner"},
            }],
        },
    )
    with pytest.raises(KeyError):
        build_service_runtime(config, secret_backend=EnvironmentSecretBackend({}))
    assert TOKEN not in json.dumps(config.model_dump(mode="json"))


def test_host_health_readiness_authenticated_api_and_sqlite_reopen(tmp_path):
    config = _config(tmp_path)
    runtime = build_service_runtime(config, secret_backend=EnvironmentSecretBackend(TOKEN_ENV))
    host = create_service_host(runtime)
    host.start()
    address, port = host.address
    base = f"http://{address}:{port}"

    try:
        status, body = _get(base + "/healthz")
        assert status == 200
        assert body == {"status": "live"}

        status, body = _get(base + "/readyz")
        assert status == 200
        assert body == {"status": "ready"}

        status, body = _get(base + "/api/v1/projects", token=TOKEN)
        assert status == 200
        assert body["data"]["projects"] == []

        with pytest.raises(HTTPError) as denied:
            _get(base + "/api/v1/projects")
        assert denied.value.code == 401
        denied.value.close()
    finally:
        assert host.stop()
    assert host.state == HostState.STOPPED
    assert not runtime.store.is_initialized

    reopened = SQLitePersistenceStore(config.state_db_path)
    reopened.initialize()
    assert reopened.schema_version == SQLitePersistenceStore.SCHEMA_VERSION
    assert reopened.conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    reopened.close()


def _call_wsgi(app, path, *, remote, forwarded=None):
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "REMOTE_ADDR": remote,
        "wsgi.input": io.BytesIO(),
    }
    if forwarded is not None:
        environ["HTTP_X_FORWARDED_PROTO"] = forwarded
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    payload = b"".join(app(environ, start_response))
    return int(captured["status"].split()[0]), json.loads(payload)


def test_proxy_mode_rejects_untrusted_or_insecure_forwarding(tmp_path):
    config = _config(
        tmp_path,
        bind_host="0.0.0.0",
        proxy_mode=True,
        trusted_proxies=("127.0.0.1/32",),
    )
    runtime = build_service_runtime(config, secret_backend=EnvironmentSecretBackend(TOKEN_ENV))
    lifecycle = HostLifecycle()
    lifecycle.mark_ready()
    app = ServiceHostApplication(runtime, lifecycle, config.service_host)
    try:
        status, _ = _call_wsgi(app, "/api/v1/projects", remote="10.0.0.5", forwarded="https")
        assert status == 403
        status, _ = _call_wsgi(app, "/api/v1/projects", remote="127.0.0.1", forwarded="http")
        assert status == 400
        status, body = _call_wsgi(app, "/readyz", remote="10.0.0.5", forwarded="http")
        assert status == 200
        assert body == {"status": "ready"}
    finally:
        runtime.close()


def test_draining_makes_readiness_and_application_requests_unavailable(tmp_path):
    config = _config(tmp_path)
    runtime = build_service_runtime(config, secret_backend=EnvironmentSecretBackend(TOKEN_ENV))
    lifecycle = HostLifecycle()
    lifecycle.mark_ready()
    app = ServiceHostApplication(runtime, lifecycle, config.service_host)
    lifecycle.begin_draining()
    try:
        status, body = _call_wsgi(app, "/readyz", remote="127.0.0.1")
        assert status == 503
        assert body == {"status": "not-ready"}

        status, body = _call_wsgi(app, "/api/v1/projects", remote="127.0.0.1")
        assert status == 503
        assert body["error"]["code"] == "HOST_REJECTED"
    finally:
        runtime.close()


def test_forwarded_headers_are_ignored_when_proxy_mode_is_disabled(tmp_path):
    config = _config(tmp_path)
    runtime = build_service_runtime(config, secret_backend=EnvironmentSecretBackend(TOKEN_ENV))
    lifecycle = HostLifecycle()
    lifecycle.mark_ready()
    app = ServiceHostApplication(runtime, lifecycle, config.service_host)

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/api/v1/projects",
        "REMOTE_ADDR": "203.0.113.55",
        "HTTP_X_FORWARDED_PROTO": "http",
        "HTTP_X_FORWARDED_USER": "spoofed-owner",
        "HTTP_AUTHORIZATION": f"Bearer {TOKEN}",
        "wsgi.input": io.BytesIO(),
    }
    captured = {}

    def start_response(status, headers):
        captured["status"] = status

    try:
        payload = json.loads(b"".join(app(environ, start_response)))
        assert captured["status"].startswith("200 ")
        assert payload["data"]["projects"] == []
    finally:
        runtime.close()


def _post_raw(url, raw, *, token=TOKEN):
    request = Request(
        url,
        data=raw,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Idempotency-Key": "phase3-raw",
        },
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read())
        finally:
            exc.close()


def test_real_host_rejects_oversized_and_malformed_json_without_internal_leak(tmp_path):
    config = _config(tmp_path)
    runtime = build_service_runtime(config, secret_backend=EnvironmentSecretBackend(TOKEN_ENV))
    host = create_service_host(runtime)
    host.start()
    address, port = host.address
    base = f"http://{address}:{port}"
    try:
        exact_limit = b"{}" + b" " * (64 * 1024 - 2)
        status, body = _post_raw(base + "/api/v1/projects", exact_limit)
        assert status == 403
        assert body["error"]["code"] == "ACCESS_DENIED"

        status, body = _post_raw(base + "/api/v1/projects", b"x" * (64 * 1024 + 1))
        assert status == 400
        assert body["error"]["code"] == "INVALID_REQUEST"
        assert "too large" in body["error"]["message"]

        status, body = _post_raw(base + "/api/v1/projects", b"\xff")
        assert status == 400
        assert body["error"]["code"] == "INVALID_REQUEST"
        assert "UTF-8 JSON" in body["error"]["message"]

        status, body = _post_raw(base + "/api/v1/projects", b"{")
        assert status == 400
        assert body["error"]["code"] == "INVALID_REQUEST"
        assert "UTF-8 JSON" in body["error"]["message"]

        serialized = json.dumps(body)
        assert "Traceback" not in serialized
        assert TOKEN not in serialized
    finally:
        assert host.stop()


def _registration_body(project_id="P3_RESTART"):
    return {
        "project_id": project_id,
        "onboarding": {
            "name": "Phase Three Restart",
            "short_name": "phase-three-restart",
            "purpose": "Verify durable service restart semantics.",
            "problem_statement": "HTTP restart must not duplicate material work.",
            "project_type": "AI",
            "success_criteria": ["restart replay works"],
            "first_working_criteria": ["service restarts cleanly"],
            "repository": {
                "repository_provider": "FILESYSTEM",
                "repository_name": "phase-three-restart",
                "repository_visibility": "PRIVATE",
            },
            "architecture": {"architecture_style": "MODULAR"},
            "notifications": {"primary_channel": "EMAIL"},
        },
    }


def test_restart_preserves_durable_idempotent_command_receipt(tmp_path):
    principals = [{
        "principal_id": "owner",
        "scopes": ["projects:read", "projects:register"],
        "token_ref": {"uri": "secret://service/owner"},
    }]
    config = _config(tmp_path, principals=principals)
    backend = EnvironmentSecretBackend(TOKEN_ENV)
    body = _registration_body()
    key = "phase3-restart-register"

    runtime = build_service_runtime(config, secret_backend=backend)
    host = create_service_host(runtime)
    host.start()
    address, port = host.address
    client = ServiceClientV1(f"http://{address}:{port}", TOKEN, timeout_seconds=3)
    first = client.request("POST", "/api/v1/projects", body=body, idempotency_key=key)
    assert first.body["meta"]["idempotent_replay"] is False
    assert host.stop()

    runtime2 = build_service_runtime(config, secret_backend=backend)
    host2 = create_service_host(runtime2)
    host2.start()
    address2, port2 = host2.address
    client2 = ServiceClientV1(f"http://{address2}:{port2}", TOKEN, timeout_seconds=3)
    try:
        replay = client2.request("POST", "/api/v1/projects", body=body, idempotency_key=key)
        assert replay.body["meta"]["idempotent_replay"] is True
        listed = client2.request("GET", "/api/v1/projects")
        assert [item["project_id"] for item in listed.body["data"]["projects"]] == ["P3_RESTART"]
    finally:
        assert host2.stop()


def test_sqlite_read_waits_for_inflight_transaction_commit(tmp_path):
    store = SQLitePersistenceStore(tmp_path / "serialized.db")
    store.initialize()
    written = Event()
    release = Event()
    reader_done = Event()
    seen = []
    now = datetime(2026, 9, 19, 15, 0, tzinfo=timezone.utc)
    project = Project(
        project_id="SERIALIZED",
        name="Serialized",
        lifecycle_state=ProjectLifecycleState.BUILDING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=now,
        updated_at=now,
    )

    def writer():
        with store.transaction():
            store.save_project(project)
            written.set()
            assert release.wait(2)

    def reader():
        assert written.wait(2)
        seen.append(store.get_project("SERIALIZED"))
        reader_done.set()

    writer_thread = Thread(target=writer)
    reader_thread = Thread(target=reader)
    writer_thread.start()
    reader_thread.start()
    assert written.wait(2)
    sleep(0.05)
    assert not reader_done.is_set()
    release.set()
    writer_thread.join(2)
    reader_thread.join(2)
    try:
        assert reader_done.is_set()
        assert seen[0] is not None
        assert seen[0].project_id == "SERIALIZED"
    finally:
        store.close()


def test_configured_extensions_use_governance_and_strict_mode(tmp_path, monkeypatch):
    import ksupervisor.extensions as extensions

    seen = []

    def fake_activate(kind, name, context, governance):
        seen.append((kind, name, context, governance))
        raise extensions.ExtensionActivationError("blocked by trust policy")

    monkeypatch.setattr(extensions, "activate_extension", fake_activate)
    strict = _config(
        tmp_path,
        extensions=({"kind": "agent", "name": "demo"},),
    )
    with pytest.raises(extensions.ExtensionActivationError, match="trust policy"):
        build_service_runtime(strict, secret_backend=EnvironmentSecretBackend(TOKEN_ENV))
    assert seen
    assert isinstance(seen[0][3], extensions.ExtensionGovernance)

    relaxed = strict.model_copy(update={"strict_extensions": False})
    runtime = build_service_runtime(
        relaxed,
        secret_backend=EnvironmentSecretBackend(TOKEN_ENV),
    )
    runtime.close()


def test_probe_methods_and_config_bounds_fail_closed(tmp_path):
    with pytest.raises(ValidationError):
        ServiceHostConfig(port=65536)
    with pytest.raises(ValidationError):
        ServiceHostConfig(workers=0)
    with pytest.raises(ValidationError):
        ServiceHostConfig(socket_timeout_seconds=0)
    with pytest.raises(ValidationError):
        ServiceHostConfig(drain_timeout_seconds=301)

    config = _config(tmp_path)
    runtime = build_service_runtime(config, secret_backend=EnvironmentSecretBackend(TOKEN_ENV))
    lifecycle = HostLifecycle()
    lifecycle.mark_ready()
    app = ServiceHostApplication(runtime, lifecycle, config.service_host)
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/healthz",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": io.BytesIO(),
    }
    captured = {}
    try:
        payload = b"".join(app(environ, lambda status, headers: captured.update(status=status)))
        assert captured["status"].startswith("405 ")
        assert json.loads(payload)["error"]["code"] == "HOST_REJECTED"
    finally:
        runtime.close()
