# PLATFORM_INTERFACES
Публічні межі встановлення, CLI, конфігурації, extension discovery та Service/API для K_Supervisor.

Version: 1.1
Status: ACTIVE
Baseline: v0.3 Phase 5
Date: 2026-09-16

## 1. Public Package Boundary

The installable distribution is `k-supervisor`. The stable public Python facade is `ksupervisor`.

Existing internal top-level packages remain available for the current 0.x baseline, but new external integrations should prefer `ksupervisor`, `ksupervisor.service` and explicitly documented contract/registry/adapter modules rather than Supervisor implementation details.

## 2. CLI

Installation creates the `k-supervisor` console command.

Supported commands remain:

```text
k-supervisor version
k-supervisor validate-config PATH
k-supervisor extensions [--kind agent|capability|project_template|adapter]
```

Phase 5 does not replace or remove the CLI.

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

`ServiceApiV1` is transport-neutral. `WsgiServiceAppV1` is a thin HTTP/WSGI adapter and is not a production hosting stack.

Authentication is injected. The baseline Bearer adapter is `StaticBearerAuthenticator`; tokens are host-owned and are not persisted by the API.

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

Baseline fields remain:

```text
config_version
state_db_path
extension_groups
strict_extensions
```

JSON and TOML are supported by `load_config()`. Secrets are not configuration values; protected credentials continue to use `secret://...` references and secret backends.

Phase 5 does not add persisted API credentials to `PlatformConfig`.

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

Core Validation builds and installs a wheel, changes outside the repository checkout, and verifies the CLI and `import ksupervisor`.

## 8. Compatibility Boundary

The service API is additive to the existing package/CLI/config/extension baseline. `/api/v1` request/response meanings and documented scope names are now public compatibility surfaces subject to `COMPATIBILITY_POLICY.md`.

## 9. Validation Baseline

```text
Implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Core Validation run: 35103131762
pytest: 129 passed
branch-aware coverage: 85.34%
Core Validation: PASS
```
