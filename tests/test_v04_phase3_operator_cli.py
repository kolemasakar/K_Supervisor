from __future__ import annotations

import ast
import json
from pathlib import Path

from access import EnvironmentSecretBackend
from ksupervisor import cli
from ksupervisor.config import PlatformConfig
from service_api.client import ServiceClientV1
from service_api.host import create_service_host
from service_api.runtime import build_service_runtime


TOKEN = "phase3-cli-token"
ENV_KEY = "KSUP_SECRET__SERVICE_OWNER"


def _onboarding():
    return {
        "name": "Phase Three CLI",
        "short_name": "phase-three-cli",
        "purpose": "Operate Service/API over HTTP.",
        "problem_statement": "Operator commands need one supported network boundary.",
        "project_type": "AI",
        "success_criteria": ["cli parity"],
        "first_working_criteria": ["http service works"],
        "repository": {
            "repository_provider": "FILESYSTEM",
            "repository_name": "phase-three-cli",
            "repository_visibility": "PRIVATE",
        },
        "architecture": {"architecture_style": "MODULAR"},
        "notifications": {"primary_channel": "EMAIL"},
    }


def _host_config(tmp_path):
    return PlatformConfig(
        state_db_path=str(tmp_path / "state.db"),
        service_host={
            "port": 0,
            "workers": 2,
            "principals": [{
                "principal_id": "owner",
                "scopes": ["projects:read", "projects:register"],
                "token_ref": {"uri": "secret://service/owner"},
            }],
        },
    )


def _write_client_config(tmp_path, base_url):
    path = tmp_path / "client.json"
    path.write_text(
        json.dumps({
            "state_db_path": str(tmp_path / "unused.db"),
            "service_client": {
                "base_url": base_url,
                "token_ref": {"uri": "secret://service/owner"},
                "timeout_seconds": 3,
            },
        }),
        encoding="utf-8",
    )
    return path


def test_operator_cli_has_no_direct_control_plane_imports():
    source = Path(cli.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {
        "persistence",
        "registry",
        "supervisor.kernel",
        "workflows.engine",
        "policy.approval",
        "release_manager",
    }
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not any(
        module == prefix or module.startswith(prefix + ".")
        for module in imported
        for prefix in forbidden
    )


def test_cli_http_parity_and_idempotency_key_surface(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(ENV_KEY, TOKEN)
    runtime = build_service_runtime(
        _host_config(tmp_path),
        secret_backend=EnvironmentSecretBackend({ENV_KEY: TOKEN}),
    )
    host = create_service_host(runtime)
    host.start()
    address, port = host.address
    base_url = f"http://{address}:{port}"
    config_path = _write_client_config(tmp_path, base_url)
    body_path = tmp_path / "register.json"
    request_body = {"project_id": "CLI_P3", "onboarding": _onboarding()}
    body_path.write_text(json.dumps(request_body), encoding="utf-8")

    try:
        assert cli.main([
            "projects", "register",
            "--config", str(config_path),
            "--idempotency-key", "phase3-cli-register",
            "--body", str(body_path),
        ]) == 0
        created = json.loads(capsys.readouterr().out)
        assert created["idempotency_key"] == "phase3-cli-register"
        assert created["response"]["data"]["project"]["project_id"] == "CLI_P3"

        assert cli.main(["projects", "list", "--config", str(config_path)]) == 0
        listed = json.loads(capsys.readouterr().out)
        assert [item["project_id"] for item in listed["data"]["projects"]] == ["CLI_P3"]

        direct = ServiceClientV1(base_url, TOKEN, timeout_seconds=3)
        replay = direct.request(
            "POST",
            "/api/v1/projects",
            body=request_body,
            idempotency_key="phase3-cli-register",
        )
        assert replay.body["meta"]["idempotent_replay"] is True
        assert replay.body["data"]["project"]["project_id"] == "CLI_P3"
    finally:
        assert host.stop()


def test_cli_auto_key_is_reported_on_api_error_without_token_leak(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv(ENV_KEY, TOKEN)
    runtime = build_service_runtime(
        _host_config(tmp_path),
        secret_backend=EnvironmentSecretBackend({ENV_KEY: TOKEN}),
    )
    host = create_service_host(runtime)
    host.start()
    address, port = host.address
    config_path = _write_client_config(tmp_path, f"http://{address}:{port}")
    body_path = tmp_path / "lifecycle.json"
    body_path.write_text(
        json.dumps({
            "to_state": "BUILDING",
            "reason": "test denied scope",
            "trigger": "CLI",
        }),
        encoding="utf-8",
    )
    try:
        code = cli.main([
            "projects", "lifecycle", "MISSING",
            "--config", str(config_path),
            "--body", str(body_path),
        ])
        assert code == 2
        captured = capsys.readouterr()
        error = json.loads(captured.err)
        assert error["error"]["code"] == "ACCESS_DENIED"
        assert error["idempotency_key"].startswith("CLI_")
        assert TOKEN not in captured.err
        assert "Traceback" not in captured.err
    finally:
        assert host.stop()


def test_cli_reports_generated_key_on_transport_uncertainty(tmp_path, monkeypatch, capsys):
    body_path = tmp_path / "register.json"
    body_path.write_text(
        json.dumps({"project_id": "UNCERTAIN", "onboarding": _onboarding()}),
        encoding="utf-8",
    )

    class TimeoutClient:
        def request(self, *args, **kwargs):
            from service_api.client import ServiceClientError
            raise ServiceClientError(
                "TRANSPORT_TIMEOUT",
                "service request timed out; mutation outcome may be uncertain",
                retryable=True,
            )

    monkeypatch.setattr(cli, "_client", lambda config_path: TimeoutClient())
    code = cli.main([
        "projects", "register",
        "--config", str(tmp_path / "unused.json"),
        "--body", str(body_path),
    ])
    assert code == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert payload["error"]["code"] == "TRANSPORT_TIMEOUT"
    assert payload["idempotency_key"].startswith("CLI_")
    assert "uncertain" in payload["error"]["message"]
    assert "Traceback" not in captured.err
