# COMPATIBILITY_POLICY
Політика сумісності публічних контрактів, пакетів, Service/API та extension surfaces K_Supervisor.

Version: 1.1
Status: ACTIVE
Baseline: v0.3 Phase 5
Date: 2026-09-16

## 1. Scope

This policy covers machine contracts, the installable package, the `ksupervisor` public facade, documented Service/API contracts, CLI commands, configuration, adapter protocols and extension entry-point groups.

K_Supervisor remains PRE-ALPHA at package version `0.1.0`; this policy defines change discipline rather than production-grade long-term support.

## 2. Machine Contract Versions

Existing Agent/Capability/Project/Workflow machine contracts retain their explicit version semantics. Consumers must reject contract versions they cannot safely interpret.

Backward-compatible additions may occur when defaults preserve prior behavior. Removing required fields, changing meaning or weakening validation requires an incompatible contract version.

## 3. Python Package Versioning

The distribution follows semantic-versioning intent:

```text
PATCH - compatible fixes and documentation/quality changes
MINOR - backward-compatible public features
MAJOR - incompatible public API/contract changes after 1.0
```

During `0.x`, incompatible changes are possible, but they must be documented and covered by compatibility review/tests before release.

## 4. Service/API Compatibility

The Phase 5 public service line is:

```text
/api/v1
```

Within `v1`, additive response metadata or new routes may be compatible when existing clients can safely ignore them. Removing routes/fields, changing the meaning of existing fields/status codes, weakening authentication/scope requirements, or changing idempotency semantics requires explicit compatibility review and normally a new API version.

Documented scope names are part of the v1 access contract:

```text
projects:read
projects:lifecycle:write
projects:operational:write
```

The public Python service facade is `ksupervisor.service`. Internal implementation helpers under `service_api` are not independently guaranteed unless documented in `SERVICE_API.md` or exported through the facade.

## 5. Stable Extension Groups

The following entry-point names remain the extension compatibility boundary:

```text
k_supervisor.agents
k_supervisor.capabilities
k_supervisor.project_templates
k_supervisor.adapters
```

Renaming or removing one is an incompatible extension-interface change.

## 6. Public vs Internal Python Surface

Preferred public imports begin with `ksupervisor` or use explicitly documented contract/registry/adapter modules.

Undocumented implementation helpers, SQLite physical layout, test support files and private methods are not compatibility promises.

## 7. CLI Compatibility

The baseline commands remain:

```text
k-supervisor version
k-supervisor validate-config PATH
k-supervisor extensions
```

Adding commands/options is compatible. Removing commands, changing exit semantics or changing machine-readable output fields requires explicit compatibility review.

## 8. Configuration Compatibility

`PlatformConfig.config_version` remains the configuration compatibility discriminator. Unknown configuration fields fail validation so configuration drift is explicit.

A change that cannot safely interpret an existing configuration requires a new `config_version` and migration guidance.

## 9. Deprecation Rule

Where practical, a public surface should be deprecated before removal. Deprecation documentation must identify the replacement and earliest removal line.

Security or data-integrity defects may require immediate incompatible changes; such changes must be documented explicitly.

## 10. Extension Responsibility

External extensions must declare the K_Supervisor versions/contracts they support and test against those ranges. Extensions must not assume undocumented implementation modules are stable.
