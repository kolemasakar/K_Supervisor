# COMPATIBILITY_POLICY
Політика сумісності публічних контрактів, пакетів та extension surfaces K_Supervisor.

Version: 1.0
Status: ACTIVE
Baseline Phase: 16

## 1. Scope

This policy covers machine contracts, the installable package, the `ksupervisor` public facade, CLI commands, documented adapter protocols and extension entry-point groups.

K_Supervisor remains PRE-ALPHA at package version `0.1.0`; therefore this policy defines intent and change discipline rather than claiming production-grade long-term support.

## 2. Machine Contract Versions

Existing Agent/Capability/Project/Workflow machine contracts retain their explicit version semantics. A consumer must reject contract versions it cannot interpret safely.

Backward-compatible additions may occur within a compatible contract line when defaults preserve prior behavior. Removing required fields, changing meaning, or weakening validation requires a new incompatible contract version.

## 3. Python Package Versioning

The distribution follows semantic-versioning intent:

```text
PATCH - compatible fixes and documentation/quality changes
MINOR - backward-compatible public features
MAJOR - incompatible public API/contract changes after 1.0
```

During `0.x`, incompatible changes are possible, but they must be documented in the changelog/release notes and reflected in compatibility tests before release.

## 4. Stable Phase 16 Extension Groups

The following entry-point names are the Phase 16 compatibility boundary:

```text
k_supervisor.agents
k_supervisor.capabilities
k_supervisor.project_templates
k_supervisor.adapters
```

Renaming or removing one of these groups is an incompatible extension-interface change.

## 5. Public vs Internal Python Surface

Preferred public imports begin with `ksupervisor` or use explicitly documented contract/registry/adapter modules.

Undocumented implementation helpers, SQLite physical layout, test support files and private methods are not compatibility promises.

## 6. CLI Compatibility

The baseline commands are:

```text
k-supervisor version
k-supervisor validate-config PATH
k-supervisor extensions
```

Adding commands/options is compatible. Removing commands, changing exit semantics, or changing machine-readable output fields requires explicit compatibility review.

## 7. Configuration Compatibility

`PlatformConfig.config_version` is the configuration compatibility discriminator. Unknown configuration fields fail validation so configuration drift is explicit.

A change that cannot safely interpret an existing configuration requires a new `config_version` and migration guidance.

## 8. Deprecation Rule

Where practical, a public surface should be deprecated before removal. Deprecation documentation must identify the replacement and the first release in which removal may occur.

Security or data-integrity defects may require immediate incompatible changes; such changes must be documented explicitly.

## 9. Extension Responsibility

External extensions must declare the K_Supervisor versions/contracts they support and test against those ranges. Extensions must not assume that internal implementation modules are stable unless those modules are explicitly listed as public in platform documentation.
