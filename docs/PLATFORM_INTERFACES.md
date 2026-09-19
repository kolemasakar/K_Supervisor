# PLATFORM_INTERFACES
Публічні межі встановлення, CLI, конфігурації, extension discovery та Service/API для K_Supervisor.

Version: 1.2
Status: ACTIVE
Baseline: v0.4 Phase 3 implementation candidate
Date: 2026-09-19

## 1. Public Package Boundary

The installable distribution is `k-supervisor`. The stable public Python facade is `ksupervisor`.

Existing internal top-level packages remain available for the current 0.x baseline, but new external integrations should prefer `ksupervisor`, `ksupervisor.service` and explicitly documented contract/registry/adapter modules rather than Supervisor implementation details.

## 2. CLI

Installation creates the `k-supervisor` console command.

Legacy commands remain backward-compatible:

```text
k-supervisor version
k-supervisor validate-config PATH
k-supervisor extensions [--kind agent|capability|project_template|adapter]
```

Phase 3 adds `k-supervisor serve --config CONFIG` and HTTP-only operator groups for Projects, ProjectSpecs, Human Actions, Policy Approvals, Tasks, Workflows, Releases and recovery status. Operator mutations require or auto-generate an idempotency key; generated keys are surfaced in machine-readable output. Bearer-token contents are never accepted as command-line arguments.

## 3. Service/API Boundary

Phase 5 adds the public Python facade `ksupervisor.service` and versioned API base path:

```text
/api/v1
```

Supported v1 routes:

```text
GET  /api/v1/projects
GET  /api/v1/projects/{project_id}
POST /api/v1/projects/{project_id}/lifecycle-transitions
POST /api/v1/projects/{project_id}/operational-transitions
```

`ServiceApiV1` remains transport-neutral and authoritative for business semantics. `WsgiServiceAppV1` remains the thin application adapter. Phase 3 adds `ServiceRuntime`, bounded `ServiceHost`, `ServiceClientV1`, unauthenticated minimal `/healthz` and `/readyz`, graceful drain/shutdown, and trusted-proxy enforcement without changing `/api/v1` semantics.

Authentication is injected. `StaticBearerAuthenticator` resolves host-supplied in-memory Bearer mappings; persisted configuration contains only `secret://...` references and resolved token contents are never persisted by the API or CLI.

Required scopes are:

```text
projects:read
projects:lifecycle:write
projects:operational:write
```

All mutation routes require `Idempotency-Key` and use durable service mutation receipts. Lifecycle rules remain owned by `ProjectRegistry` and the existing state models.

Detailed contract: `SERVICE_API.md`.

## 4. Configuration Model

`ksupervisor.config.PlatformConfig` is frozen and rejects unknown fields.

Baseline fields remain and old configuration files stay valid:

```text
config_version
state_db_path
extension_groups
strict_extensions
```

Phase 3 adds optional `service_host` and `service_client` sections while retaining `config_version = "1"`. Host configuration bounds bind/port, workers, socket/drain timeouts, trusted proxies, protected principal token references, and optional governed extension activations. Client configuration accepts only HTTPS for non-loopback endpoints and may use HTTP only for loopback.

JSON and TOML are supported by `load_config()`. Secrets are not configuration values; only opaque `secret://...` references may persist.

## 5. Extension Discovery

K_Supervisor uses standard Python package entry points:

```text
k_supervisor.agents
k_supervisor.capabilities
k_supervisor.project_templates
k_supervisor.adapters
```

`discover_extensions()` returns deterministic descriptors without importing extension code. `activate_extension()` loads exactly one named entry point and invokes the loaded callable or its `register(context)` method.

## 6. Extension Context

`ExtensionContext` exposes named host services. An extension must request a service explicitly with `context.require(name)` rather than reaching into global process state.

Phase 5 does not change extension activation/trust semantics.

## 7. Packaging

`pyproject.toml` defines Python >= 3.13, Pydantic v2, setuptools build backend, explicit package discovery and the console script. Phase 5 adds `service_api*` to the packaged modules and public `ksupervisor.service` exports.

Core Validation builds and installs a wheel, changes outside the repository checkout, verifies the public CLI/import surface, starts the installed Phase 3 host on an ephemeral loopback port, checks health/readiness, performs an authenticated CLI-over-HTTP request, shuts down cleanly, and verifies SQLite integrity.

## 8. Compatibility Boundary

The service host/client/CLI layer is additive to the existing package/config/extension and `/api/v1` compatibility baseline. Host transport policy does not create a second control plane. `/api/v1` request/response meanings, documented scope names, 64 KiB request-body floor, idempotency semantics, and owner publication boundary remain public compatibility surfaces subject to `COMPATIBILITY_POLICY.md`.

## 9. Validation Baseline

```text
Implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Core Validation run: 35103131762
pytest: 129 passed
branch-aware coverage: 85.34%
Core Validation: PASS
```
