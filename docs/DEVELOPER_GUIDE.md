# DEVELOPER_GUIDE
Практичний посібник для розширення K_Supervisor без змін Supervisor core.

Version: 1.0
Status: ACTIVE
Baseline Phase: 16

## 1. Extension Rule

An extension should depend on contracts and registries, not on private orchestration internals. The normal path is:

```text
external package
  -> Python entry point
  -> ksupervisor discovery
  -> register(context)
  -> existing registry or host contribution registry
  -> Supervisor resolves by capability/contract
```

## 2. Add an Agent and Capability

Use the Phase 12 AgentFactory contracts to define an AgentBlueprint and CapabilityBlueprint. Register generated CapabilityDescriptor values in CapabilityRegistry before registering the AgentDescriptor in AgentRegistry. Bind the handler through the Agent Runtime adapter.

An external distribution can expose its registrar under `k_supervisor.agents` or `k_supervisor.capabilities`. The registrar receives ExtensionContext and requests only the registries it needs.

No SupervisorKernel source change is required because task routing remains capability-based.

## 3. Add a Project Template

Expose a callable or object through `k_supervisor.project_templates`. A registrar can place the template into a host-owned `NamedExtensionRegistry` service named `project_templates`.

`examples/extension_project_template.py` demonstrates this registration pattern.

A template should return or generate platform bootstrap contracts rather than writing arbitrary global files directly. Repository effects remain adapter-owned.

## 4. Add an Adapter

Expose an adapter registrar under `k_supervisor.adapters`. Prefer an existing stable adapter protocol where one exists:

```text
RepositoryAdapter
RuntimeAdapter
EmailProvider
Tool
Provider
ProvisioningAdapter
SecretBackend
```

For new adapter categories, define a narrow Protocol/contract first and keep vendor-specific behavior behind it.

## 5. Add a Workflow

Construct a WorkflowDefinition from capability requirements. Workflow nodes must not embed concrete agent IDs. The Supervisor resolves providers dynamically.

`examples/workflow_definition.py` is the minimal two-capability reference.

## 6. Package Entry Points

An external package can declare entry points in its own `pyproject.toml`, for example:

```toml
[project.entry-points."k_supervisor.project_templates"]
minimal = "my_extension.template:register"

[project.entry-points."k_supervisor.adapters"]
my_adapter = "my_extension.adapter:register"
```

The same pattern applies to `k_supervisor.agents` and `k_supervisor.capabilities`.

## 7. Validation Expectations

A compliant extension should test:

- descriptor/model validation;
- duplicate/conflict behavior;
- supported contract versions;
- registration without Supervisor-core edits;
- deterministic failure behavior;
- no raw credential persistence or logging;
- policy/permission boundaries for side effects.

Run the repository Core Validation before submitting platform changes. External packages should run their own tests against the supported K_Supervisor compatibility range.

## 8. What Not to Depend On

Do not depend on hidden chain-of-thought, process-local object identity, undocumented SQLite table details, concrete Supervisor private methods, or raw secrets in ProjectSpec/notifications/audit events.

The stable extension surfaces are documented contracts, registries, adapter protocols, the `ksupervisor` facade and declared entry-point groups.
