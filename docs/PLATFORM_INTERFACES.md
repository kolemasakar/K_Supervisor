# PLATFORM_INTERFACES
Публічні межі встановлення, CLI, конфігурації та extension discovery для K_Supervisor.

Version: 1.0
Status: ACTIVE
Baseline Phase: 16

## 1. Public Package Boundary

The installable distribution is `k-supervisor`. The stable public facade introduced in Phase 16 is the `ksupervisor` Python package.

Existing internal top-level packages remain available for the current 0.x baseline, but new external integrations should enter through `ksupervisor` plus the documented contract/registry modules rather than importing Supervisor implementation details.

## 2. CLI

Installation creates the `k-supervisor` console command.

Supported baseline commands:

```text
k-supervisor version
k-supervisor validate-config PATH
k-supervisor extensions [--kind agent|capability|project_template|adapter]
```

The CLI is intentionally small. It is a stable control/interface boundary, not a replacement for the Project Control Plane.

## 3. Configuration Model

`ksupervisor.config.PlatformConfig` is frozen and rejects unknown fields.

Baseline fields:

```text
config_version
state_db_path
extension_groups
strict_extensions
```

JSON and TOML are supported by `load_config()`. `examples/platform.toml` is the canonical minimal example.

Secrets are not configuration values. Protected credentials continue to use Phase 10 `secret://...` access references and secret backends.

## 4. Extension Discovery

K_Supervisor uses standard Python package entry points. Phase 16 defines four groups:

```text
k_supervisor.agents
k_supervisor.capabilities
k_supervisor.project_templates
k_supervisor.adapters
```

`discover_extensions()` returns deterministic descriptors without importing extension code. `activate_extension()` loads exactly one named entry point and invokes either the loaded callable or its `register(context)` method.

This keeps discovery separate from activation and avoids hard-coded Supervisor imports.

## 5. Extension Context

`ExtensionContext` exposes named host services. An extension must request a service explicitly with `context.require(name)` rather than reaching into global process state.

Typical services are existing registries such as AgentRegistry/CapabilityRegistry or host-owned `NamedExtensionRegistry` instances for project templates and adapters.

The external extension owns construction of its descriptor/adapter object; K_Supervisor owns validation and registration through the target registry contract.

## 6. Packaging

`pyproject.toml` now defines:

- setuptools build backend;
- Python >= 3.13;
- runtime dependency on Pydantic v2;
- dev build/test dependencies;
- explicit package discovery;
- `k-supervisor` console script.

Core Validation builds a wheel, installs that wheel, changes outside the repository checkout, and verifies both the console command and `import ksupervisor`.

## 7. Examples

Phase 16 includes:

```text
examples/platform.toml
examples/extension_project_template.py
examples/workflow_definition.py
```

The examples are syntax-checked by CI and have direct tests for valid workflow construction and template registration.

## 8. Boundary

Phase 16 does not add a web server or remote API. The ROADMAP requires CLI and/or API; this baseline chooses a CLI plus Python extension interface. A future HTTP/RPC surface can wrap the same contracts without changing Supervisor core behavior.
