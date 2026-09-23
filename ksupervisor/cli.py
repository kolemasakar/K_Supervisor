from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path
from threading import Event
from uuid import uuid4

from access import EnvironmentSecretBackend
from service_api.client import ServiceClientError, ServiceClientV1
from service_api.host import create_service_host
from service_api.runtime import build_service_runtime

from . import __version__
from .config import load_config
from .extensions import discover_extensions


def _add_config(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", required=True, help="platform JSON/TOML configuration")


def _add_mutation(parser: argparse.ArgumentParser, *, body: bool = False) -> None:
    _add_config(parser)
    parser.add_argument("--idempotency-key")
    if body:
        parser.add_argument("--body", required=True, help="JSON request file or - for stdin")


def _resource_group(sub, name: str, help_text: str):
    parser = sub.add_parser(name, help=help_text)
    return parser.add_subparsers(dest=f"{name}_command", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="k-supervisor")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print package version")
    config = sub.add_parser("validate-config", help="validate a JSON or TOML configuration file")
    config.add_argument("path")
    extensions = sub.add_parser("extensions", help="list installed K_Supervisor extensions")
    extensions.add_argument("--kind", choices=("agent", "capability", "project_template", "adapter"))

    serve = sub.add_parser("serve", help="run the single-node Service/API host")
    _add_config(serve)

    projects = _resource_group(sub, "projects", "operate Projects through Service/API")
    leaf = projects.add_parser("list"); _add_config(leaf)
    leaf = projects.add_parser("get"); leaf.add_argument("project_id"); _add_config(leaf)
    leaf = projects.add_parser("register"); _add_mutation(leaf, body=True)
    leaf = projects.add_parser("lifecycle"); leaf.add_argument("project_id"); _add_mutation(leaf, body=True)
    leaf = projects.add_parser("operational"); leaf.add_argument("project_id"); _add_mutation(leaf, body=True)

    specs = _resource_group(sub, "specs", "operate ProjectSpecs through Service/API")
    leaf = specs.add_parser("list"); leaf.add_argument("project_id"); _add_config(leaf)
    leaf = specs.add_parser("submit"); leaf.add_argument("project_id"); _add_mutation(leaf, body=True)
    for action in ("approve", "reject", "activate"):
        leaf = specs.add_parser(action); leaf.add_argument("project_id"); leaf.add_argument("spec_id"); _add_mutation(leaf)

    human = _resource_group(sub, "human-actions", "operate Human Actions through Service/API")
    leaf = human.add_parser("list"); leaf.add_argument("project_id"); _add_config(leaf)
    for action in ("verify", "cancel"):
        leaf = human.add_parser(action); leaf.add_argument("project_id"); leaf.add_argument("action_id"); _add_mutation(leaf)

    approvals = _resource_group(sub, "approvals", "operate Policy Approvals through Service/API")
    leaf = approvals.add_parser("list"); leaf.add_argument("project_id"); _add_config(leaf)
    for action in ("approve", "reject"):
        leaf = approvals.add_parser(action); leaf.add_argument("project_id"); leaf.add_argument("approval_id"); _add_mutation(leaf)
    leaf = approvals.add_parser("revoke"); leaf.add_argument("project_id"); leaf.add_argument("approval_id"); _add_mutation(leaf, body=True)

    tasks = _resource_group(sub, "tasks", "operate Tasks through Service/API")
    leaf = tasks.add_parser("list"); leaf.add_argument("project_id"); _add_config(leaf)
    leaf = tasks.add_parser("get"); leaf.add_argument("project_id"); leaf.add_argument("task_id"); _add_config(leaf)
    leaf = tasks.add_parser("start"); leaf.add_argument("project_id"); _add_mutation(leaf, body=True)
    leaf = tasks.add_parser("cancel"); leaf.add_argument("project_id"); leaf.add_argument("task_id"); _add_mutation(leaf)

    workflows = _resource_group(sub, "workflows", "operate Workflows through Service/API")
    leaf = workflows.add_parser("list"); leaf.add_argument("project_id"); _add_config(leaf)
    leaf = workflows.add_parser("get"); leaf.add_argument("project_id"); leaf.add_argument("workflow_id"); _add_config(leaf)
    leaf = workflows.add_parser("start"); leaf.add_argument("project_id"); _add_mutation(leaf, body=True)
    leaf = workflows.add_parser("cancel"); leaf.add_argument("project_id"); leaf.add_argument("workflow_id"); _add_mutation(leaf)

    releases = _resource_group(sub, "releases", "operate Releases through Service/API")
    leaf = releases.add_parser("list"); leaf.add_argument("project_id"); _add_config(leaf)
    leaf = releases.add_parser("get"); leaf.add_argument("project_id"); leaf.add_argument("release_id"); _add_config(leaf)
    leaf = releases.add_parser("prepare"); leaf.add_argument("project_id"); _add_mutation(leaf, body=True)
    leaf = releases.add_parser("confirm-publication")
    leaf.add_argument("project_id"); leaf.add_argument("release_id"); leaf.add_argument("target_type"); _add_mutation(leaf)

    repository = _resource_group(sub, "repository", "operate the governed project repository through Service/API")
    leaf = repository.add_parser("status"); leaf.add_argument("project_id"); _add_config(leaf)
    leaf = repository.add_parser("bootstrap"); leaf.add_argument("project_id"); _add_mutation(leaf)

    recovery = sub.add_parser("recovery-status", help="read durable command recovery status")
    recovery.add_argument("project_id"); _add_config(recovery)
    return parser


def _read_body(source: str) -> object:
    if source == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(source).read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("request body must be valid JSON") from exc


def _client(config_path: str) -> ServiceClientV1:
    config = load_config(config_path)
    client = config.service_client
    if client is None:
        raise ValueError("service_client configuration is required")
    if client.token_ref is None:
        raise ValueError("service_client.token_ref is required")
    token = EnvironmentSecretBackend().resolve(client.token_ref).reveal()
    if not token:
        raise ValueError("resolved service client bearer token must not be empty")
    return ServiceClientV1(
        client.base_url,
        token,
        timeout_seconds=client.timeout_seconds,
    )


def _key(args) -> str:
    value = getattr(args, "idempotency_key", None)
    return value or f"CLI_{uuid4().hex}"


def _emit(value) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _call_read(args, path: str) -> int:
    response = _client(args.config).request("GET", path)
    _emit(response.body)
    return 0


def _call_mutation(args, path: str, *, body=None) -> int:
    key = _key(args)
    try:
        response = _client(args.config).request(
            "POST",
            path,
            body=body,
            idempotency_key=key,
        )
    except ServiceClientError as exc:
        _emit_error(exc, idempotency_key=key)
        return 2
    _emit({"idempotency_key": key, "response": response.body})
    return 0


def _emit_error(exc: Exception, *, idempotency_key: str | None = None) -> None:
    payload = {
        "error": {
            "code": getattr(exc, "code", type(exc).__name__),
            "message": str(exc),
        }
    }
    status = getattr(exc, "status_code", None)
    if status is not None:
        payload["error"]["status_code"] = status
    details = getattr(exc, "details", None)
    if details:
        payload["error"]["details"] = details
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), file=sys.stderr)


def _serve(config_path: str) -> int:
    config = load_config(config_path)
    runtime = build_service_runtime(config)
    host = None
    stop_event = Event()

    def request_stop(signum, frame):
        stop_event.set()

    previous = {}
    try:
        host = create_service_host(runtime)
        host.start()
        for name in ("SIGINT", "SIGTERM"):
            sig = getattr(signal, name, None)
            if sig is not None:
                previous[sig] = signal.signal(sig, request_stop)
        address, port = host.address
        _emit({"service": "k-supervisor", "state": host.state.value, "bind": address, "port": port})
        stop_event.wait()
        return 0 if host.stop() else 3
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if host is None:
            runtime.close()
        elif host.state.value not in {"STOPPED", "DRAINING"}:
            host.stop()


def _dispatch_operator(args) -> int:
    command = args.command
    action = getattr(args, f"{command}_command", None)

    if command == "projects":
        if action == "list":
            return _call_read(args, "/api/v1/projects")
        if action == "get":
            return _call_read(args, f"/api/v1/projects/{args.project_id}")
        if action == "register":
            return _call_mutation(args, "/api/v1/projects", body=_read_body(args.body))
        if action == "lifecycle":
            return _call_mutation(
                args, f"/api/v1/projects/{args.project_id}/lifecycle-transitions",
                body=_read_body(args.body),
            )
        if action == "operational":
            return _call_mutation(
                args, f"/api/v1/projects/{args.project_id}/operational-transitions",
                body=_read_body(args.body),
            )

    if command == "specs":
        base = f"/api/v1/projects/{args.project_id}/specs"
        if action == "list":
            return _call_read(args, base)
        if action == "submit":
            return _call_mutation(args, base, body=_read_body(args.body))
        return _call_mutation(args, f"{base}/{args.spec_id}/{action}")


    if command == "human-actions":
        base = f"/api/v1/projects/{args.project_id}/human-actions"
        if action == "list":
            return _call_read(args, base)
        return _call_mutation(args, f"{base}/{args.action_id}/{action}")

    if command == "approvals":
        base = f"/api/v1/projects/{args.project_id}/approvals"
        if action == "list":
            return _call_read(args, base)
        body = _read_body(args.body) if action == "revoke" else None
        return _call_mutation(args, f"{base}/{args.approval_id}/{action}", body=body)

    if command == "tasks":
        base = f"/api/v1/projects/{args.project_id}/tasks"
        if action == "list":
            return _call_read(args, base)
        if action == "get":
            return _call_read(args, f"{base}/{args.task_id}")
        if action == "start":
            return _call_mutation(args, base, body=_read_body(args.body))
        return _call_mutation(args, f"{base}/{args.task_id}/cancel")

    if command == "workflows":
        base = f"/api/v1/projects/{args.project_id}/workflows"
        if action == "list":
            return _call_read(args, base)
        if action == "get":
            return _call_read(args, f"{base}/{args.workflow_id}")
        if action == "start":
            return _call_mutation(args, base, body=_read_body(args.body))
        return _call_mutation(args, f"{base}/{args.workflow_id}/cancel")

    if command == "releases":
        base = f"/api/v1/projects/{args.project_id}/releases"
        if action == "list":
            return _call_read(args, base)
        if action == "get":
            return _call_read(args, f"{base}/{args.release_id}")
        if action == "prepare":
            return _call_mutation(args, base, body=_read_body(args.body))
        return _call_mutation(
            args,
            f"{base}/{args.release_id}/targets/{args.target_type}/confirm-publication",
        )

    if command == "repository":
        base = f"/api/v1/projects/{args.project_id}/repository"
        if action == "status":
            return _call_read(args, base)
        return _call_mutation(args, f"{base}/bootstrap")

    if command == "recovery-status":
        return _call_read(args, f"/api/v1/projects/{args.project_id}/recovery-status")
    raise RuntimeError(f"unsupported operator command: {command} {action}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "version":
            print(__version__)
            return 0
        if args.command == "validate-config":
            config = load_config(args.path)
            _emit(config.model_dump(mode="json"))
            return 0
        if args.command == "extensions":
            items = discover_extensions(args.kind)
            _emit([item.__dict__ for item in items])
            return 0
        if args.command == "serve":
            return _serve(args.config)
        return _dispatch_operator(args)
    except ServiceClientError as exc:
        _emit_error(exc)
        return 2
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        _emit_error(exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
