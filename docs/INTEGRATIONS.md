# INTEGRATIONS
Контракти інструментів, провайдерів, provisioning та захищених посилань доступу K_Supervisor.

Version: 1.0
Status: ACTIVE
Phase: 10

## 1. Purpose

Phase 10 connects projects to external systems through replaceable adapters without coupling Supervisor or workflows to one vendor.

The integration baseline separates:

```text
Tool
Provider
ProvisioningAdapter
AccessReference / SecretBackend
ModelSelectionHook
```

Phase 11 remains responsible for permissions, risk classes, approval policy, and least-privilege authorization before side effects.

## 2. Tool Contract

`ToolDescriptor` declares:

```text
tool_id
version
operations
dependencies
metadata
```

`ToolRequest` contains project context, operation, input, and protected access references. Raw credentials are not part of the request contract.

`Tool` exposes:

```text
check_availability()
invoke(request)
```

`ToolRegistry` supports versioned registration and deterministic version resolution.

## 3. Provider Contract

`ProviderDescriptor` declares:

```text
provider_id
version
provider_type
operations
dependencies
models
metadata
```

`ProviderRequest` carries only `AccessReference` values when protected access is required.

`ProviderRegistry` supports versioned registration and resolution independently of vendor implementation.

## 4. Dependencies and Availability

Dependencies use `DependencyRequirement` with:

```text
kind
component_id
version_constraint
required
```

Availability is normalized as:

```text
AVAILABLE
DEGRADED
UNAVAILABLE
```

Tools and providers own their concrete availability checks. Generic dependency resolution treats `UNAVAILABLE` as unavailable without importing vendor-specific code.

## 5. Protected Access References

The canonical logical reference is:

```text
secret://<scope>/<name>
```

`AccessReference` validates this form. `ProtectedSecret` renders as redacted text and exposes plaintext only through an explicit `reveal()` call at the adapter boundary.

The initial `EnvironmentSecretBackend` maps references to runtime environment keys. K_Supervisor therefore stores the reference, not the plaintext secret, in normal project state.

This backend is intentionally replaceable. Phase 10 does not claim durable encrypted secret storage inside the application database.

## 6. ProjectSpec Guard

Credential-like fields in `ProjectSpec.repository`, `integrations`, `notifications`, and `release` are rejected when they contain plaintext values.

Sensitive nested values must use `secret://...` references. This is a persistence/document boundary guard, not a substitute for Phase 11 authorization policy.

## 7. Provisioning

`ProvisioningAdapter` supports provider-neutral resource kinds:

```text
REPOSITORY
SERVICE
SERVER
DATABASE
CLOUD_RESOURCE
```

`RepositoryProvisioningAdapter` bridges the Phase 6 `RepositoryAdapter` boundary.

`ProviderProvisioningAdapter` maps service/server/database/cloud provisioning to a registered generic Provider operation. Access remains reference-based.

`ProvisioningRegistry` resolves adapters by provider and supported resource kind.

## 8. Provider-Independent Model Selection

MODEL providers may expose `ModelProfile` entries. `model_candidates()` projects registered available model providers into vendor-neutral candidate records.

`ModelSelectionHook` is replaceable and receives only candidate records plus requirements. No Supervisor code needs to import a specific model vendor.

## 9. Security Boundary

Normal documentation, ProjectSpec persisted configuration, notification events, tool/provider request metadata, and provisioning configuration must use access references rather than resolved secrets.

Resolved secret values exist only transiently at a concrete adapter boundary.

## 10. Validation

Phase 10 integration coverage verifies:

- secret reference parsing and environment resolution;
- redacted secret representation;
- raw and nested credential rejection in ProjectSpec;
- versioned ToolRegistry and ProviderRegistry behavior;
- dependency availability;
- unavailable model-provider filtering;
- repository provisioning through the existing repository adapter;
- provider-backed database/service provisioning with access references only.

Committed baseline:

```text
Python 3.13.15
59 tests PASS
```

## 11. Deferred to Phase 11

Not implemented as Phase 10 responsibilities:

- side-effect authorization;
- per-agent tool permissions;
- capability risk classes;
- approval policy;
- permission expansion review;
- least-privilege execution context;
- policy decision audit.
