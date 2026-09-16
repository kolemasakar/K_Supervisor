# INTEGRATIONS
Контракти інструментів, провайдерів, provisioning та захищених посилань доступу K_Supervisor.

Version: 1.1
Status: ACTIVE
Baseline: v0.3 Phase 3 implementation

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

Phase 11 defines permissions, risk classes, approval policy and least-privilege authorization. v0.3 Phase 3 centralizes enforcement of those decisions at the standard Tool/Provider side-effect invocation boundary.

## 2. Tool Contract

`ToolDescriptor` declares:

```text
tool_id
version
operations
dependencies
metadata
```

`ToolRequest` contains project context, operation, input, protected access references, and optional request/agent/capability/idempotency correlation. Raw credentials are not part of the request contract. Existing callers remain compatible because the added correlation fields are optional.

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

`ProviderRequest` carries only `AccessReference` values when protected access is required and can carry the same optional request/agent/capability/idempotency correlation used by the centralized gateway.

`ProviderRegistry` supports versioned registration and resolution independently of vendor implementation.

## 4. Centralized Side-Effect Gateway

The standard Agent/Workflow path for material Tool/Provider side effects is now:

```text
Agent / Workflow
    -> Supervisor + PolicyEngine
    -> SideEffectGateway
    -> ToolRegistry / ProviderRegistry
    -> replaceable Tool / Provider adapter
```

`SideEffectGateway` re-evaluates policy immediately before the external adapter boundary, requires `ALLOW`, enforces requested tool operations and protected references against the resolved least-privilege context, and only then resolves/invokes the adapter. `DENY` and `REQUIRE_APPROVAL` return a normalized blocked result and never call the adapter.

The gateway propagates project/request/agent/capability correlation and idempotency keys into Tool/Provider requests. Allowed attempts are durably claimed before invocation and completed with normalized success/failure state plus structured audit. Supported repeated invocation with the same semantic idempotency key and signature reuses the authoritative prior record without calling the adapter again.

Concrete Tool/Provider implementations remain replaceable. Low-level adapter contracts are retained for backward compatibility but are not the standard production authorization boundary for Agent/Workflow side effects.

## 5. Dependencies and Availability

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

## 6. Protected Access References

The canonical logical reference is:

```text
secret://<scope>/<name>
```

`AccessReference` validates this form. `ProtectedSecret` renders as redacted text and exposes plaintext only through an explicit `reveal()` call at the adapter boundary.

The initial `EnvironmentSecretBackend` maps references to runtime environment keys. K_Supervisor therefore stores the reference, not the plaintext secret, in normal project state.

This backend is intentionally replaceable. Phase 10 does not claim durable encrypted secret storage inside the application database.

## 7. ProjectSpec Guard

Credential-like fields in `ProjectSpec.repository`, `integrations`, `notifications`, and `release` are rejected when they contain plaintext values.

Sensitive nested values must use `secret://...` references. This is a persistence/document boundary guard, not a substitute for Phase 11 authorization policy.

## 8. Provisioning

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

## 9. Provider-Independent Model Selection

MODEL providers may expose `ModelProfile` entries. `model_candidates()` projects registered available model providers into vendor-neutral candidate records.

`ModelSelectionHook` is replaceable and receives only candidate records plus requirements. No Supervisor code needs to import a specific model vendor.

## 10. Security Boundary

Normal documentation, ProjectSpec persisted configuration, notification events, tool/provider request metadata, and provisioning configuration must use access references rather than resolved secrets.

Resolved secret values exist only transiently at a concrete adapter boundary.

## 11. Validation

Phase 10 integration coverage verifies:

- secret reference parsing and environment resolution;
- redacted secret representation;
- raw and nested credential rejection in ProjectSpec;
- versioned ToolRegistry and ProviderRegistry behavior;
- dependency availability;
- unavailable model-provider filtering;
- repository provisioning through the existing repository adapter;
- provider-backed database/service provisioning with access references only.

Committed Phase 10 baseline:

```text
Python 3.13.15
59 tests PASS
```

Authoritative v0.3 Phase 3 gateway baseline:

```text
Implementation SHA: 6868d595b66a6ada91a2e6f2f62866721d0f3560
Core Validation run: 35086116020
Python: 3.13.15
pytest: 111 passed
branch-aware coverage: 85.45%
ResourceWarning / compileall / wheel build-install / CLI-import smoke: PASS
```

Completion evidence: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_3_COMPLETE.md`.

## 12. Historical Phase 10 Deferrals

The original Phase 10 integration baseline intentionally deferred side-effect authorization, per-agent tool permissions, capability risk classes, approval policy, permission expansion review, least-privilege execution context and policy decision audit to Phase 11. Those policy primitives are now implemented and v0.3 Phase 3 centralizes their standard Tool/Provider invocation enforcement.

Remaining limits include provider-specific authorization administration, universal encrypted secret storage and universal exactly-once external delivery.
