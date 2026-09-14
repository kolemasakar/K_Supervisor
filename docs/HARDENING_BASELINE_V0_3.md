# HARDENING_BASELINE_V0_3
Frozen hardening contract, predecessor baseline and technical-debt assignment for ROADMAP v0.3.

Version: 1.0
Status: FROZEN
Roadmap: v0.3
Phase: 0
Date: 2026-09-14

## 1. Purpose

This document freezes the starting contract for ROADMAP v0.3. It does not replace the completed v0.2 runtime architecture. It records the validated predecessor baseline, compatibility surfaces, debt assignment, migration/rollback expectations, hardening invariants and validation rules that later v0.3 phases must preserve.

## 2. Frozen Predecessor Runtime Baseline

```text
Repository: kolemasakar/K_Supervisor
Predecessor roadmap: v0.2 COMPLETE
Package: k-supervisor==0.1.0
Implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Core Validation run: 34793901147
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: >= 80% PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

The completed `docs/ROADMAP_V0_2_ARCHIVE.md`, `docs/PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` and `docs/ROADMAP_IMPLEMENTATION_AUDIT.md` are the historical predecessor records.

Documentation commits after the implementation SHA do not replace this runtime baseline unless a later implementation checkpoint explicitly states otherwise.

## 3. Phase 0 Validation Basis

The authoritative `Core Validation` workflow passed on the frozen implementation SHA. The workflow covers runtime/package/test paths and intentionally does not trigger for documentation-only changes.

The v0.3 roadmap-activation changes between the frozen implementation SHA and the Phase 0 documentation baseline are documentation/README changes only. Therefore Phase 0 uses:

- the successful predecessor Core Validation run as runtime evidence;
- repository compare evidence showing no runtime implementation changes after the frozen SHA;
- direct compatibility review of package, CLI and extension surfaces;
- documentation consistency review for the active v0.3 state.

Any Phase 1+ runtime implementation change must obtain a new successful Core Validation run on its committed implementation baseline before that implementation phase may be marked COMPLETE.

## 4. Preserved Public Compatibility Surfaces

The following are public compatibility boundaries governed by `COMPATIBILITY_POLICY.md`:

```text
Distribution: k-supervisor
Python facade: ksupervisor
CLI entry point: k-supervisor
CLI baseline commands:
  k-supervisor version
  k-supervisor validate-config PATH
  k-supervisor extensions
Config compatibility discriminator: PlatformConfig.config_version
Current config version: 1
Extension groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
Versioned machine contracts and documented adapter protocols
```

Removing, renaming, weakening or incompatibly reinterpreting these surfaces requires explicit compatibility handling and, where applicable, a new contract/config version and migration guidance.

## 5. Internal / Non-Promised Surfaces

The following are implementation details unless separately documented as public:

- SQLite physical schema/layout;
- private helper methods and test support modules;
- in-process executor internals;
- internal registry storage structures;
- concrete observability storage/export implementation;
- concrete Tool Gateway implementation introduced in v0.3;
- service/API implementation internals behind its versioned public contract;
- worker/process implementation details behind the runtime contract.

Hardening may refactor these internals while preserving authoritative state semantics and public contracts.

## 6. Technical Debt Assignment

### v0.3 Phase 1 - Persistence & Resource Hygiene

Assigned:

- SQLite connection/resource ownership cleanup;
- 14 known visible SQLite `ResourceWarning` warnings;
- transaction boundary hardening;
- persistent schema version/migration mechanism;
- explicit storage replacement boundary;
- reopen/restart persistence invariants.

### v0.3 Phase 2 - Durable Control State

Assigned:

- process-local runtime idempotency;
- durable duplicate suppression/control replay semantics;
- approval expiry/revocation;
- incomplete aggregate recovery coverage;
- stronger atomic relationship between authoritative state changes and required audit records;
- durable control-state reconstruction after restart.

### v0.3 Phase 3 - Centralized Side-Effect Enforcement

Assigned:

- absence of a universal centralized Tool Gateway;
- normalized side-effect invocation contract;
- mandatory policy/permission/protected-reference checks on standard platform side-effect paths;
- idempotency propagation and normalized side-effect audit.

Best-effort remote-provider delivery semantics may remain provider-limited, but platform duplicate-prevention and authoritative attempt state must be explicit.

### v0.3 Phase 4 - Runtime Isolation & Cancellation

Assigned:

- cooperative in-process cancellation as the only execution mode;
- stronger execution isolation;
- bounded termination;
- worker/process crash containment and normalized runtime failure handling.

### v0.3 Phase 5 - Service/API Boundary

Assigned:

- no HTTP/RPC service boundary;
- controlled lifecycle operations through a versioned API without bypassing the existing control plane.

### v0.3 Phase 6 - Production Observability

Assigned:

- derived metric snapshots rather than persisted operational telemetry;
- no distributed tracing/correlation boundary;
- no OpenTelemetry/Prometheus-compatible exporter boundary;
- no SLO/health-readiness foundation suitable for long-running service operation.

### v0.3 Phase 7 - Extension Trust & Platform Governance

Assigned:

- trusted Python extension execution without explicit trust/signature policy;
- non-durable `NamedExtensionRegistry` metadata where durability is required;
- extension provenance/compatibility activation policy;
- unprotected `main` and absent required status-check governance;
- current GitHub Actions action-runtime deprecation warnings.

### v0.3 Phase 8 - Operational Readiness & Autonomous Lifecycle Qualification

Assigned:

- no automated package-index publication workflow;
- deployment/runbook/backup/restore/upgrade qualification;
- release-readiness evidence still partly supplied explicitly rather than fully operationally integrated;
- full real-project lifecycle qualification from approved ProjectSpec to RELEASE_READY;
- concurrent-project qualification under restart/recovery and owner-intervention conditions.

## 7. Explicitly Deferred Beyond v0.3 Unless Reapproved

The following are not required to complete ROADMAP v0.3:

- WhatsApp, Viber or other non-email owner transports;
- automatic GPT Store/external publication that bypasses the owner-publication boundary;
- distributed execution clusters;
- remote-agent federation;
- event-bus architecture as a mandatory platform dependency;
- multi-tenant SaaS isolation/billing;
- advanced autonomous planning beyond the approved ProjectSpec/roadmap boundaries;
- richer scheduling features not needed for v0.3 qualification;
- production-grade domain intelligence for every reference agent;
- universal sandboxing guarantee for arbitrary untrusted Python code.

These items require a later explicit roadmap decision if they become implementation scope.

## 8. Migration and Rollback Contract

- Persistent schema changes must be versioned and tested.
- Unsupported schema/config/contract versions must fail safely rather than being guessed or silently coerced.
- Backward-compatible public additions are preferred.
- Incompatible public changes require explicit versioning and migration guidance.
- Data-changing migrations must define backup/precondition and failure behavior before execution.
- A failed authoritative migration must not leave a partially accepted platform state.
- Rollback expectations must be documented per migration; rollback must not assume an older binary can interpret a newer incompatible schema.
- Phase checkpoints must record the implementation SHA and validation evidence for any migration-bearing change.

## 9. Hardening Invariants

Throughout v0.3:

- Project != Task.
- Agent != Capability.
- ProjectSpec approval gates material scope.
- Supervisor remains the orchestration/routing owner.
- workflows remain capability-oriented rather than concrete-agent coupled where practical.
- lifecycle state remains distinct from operational state.
- authoritative platform state is persisted; hidden conversational memory is not authoritative.
- policy/permissions precede side effects.
- Human Intervention remains explicit and resumable.
- notification delivery does not equal completion of an owner action.
- email remains the primary notification transport for this roadmap.
- secrets remain protected references.
- RELEASE_READY does not equal publication.
- publication remains an owner action.
- K-Research & Critic remains reference-only.

No v0.3 component may create a parallel control path that bypasses ProjectSpec, Supervisor, policy/approval, authoritative persistence or the release/publication boundary.

## 10. Phase Completion Rule

For every implementation phase:

```text
approved phase scope
+ implementation
+ phase-specific tests
+ full permanent regression suite
+ successful Core Validation on committed implementation SHA
+ completion checkpoint
= eligible for COMPLETE
```

Coverage remains branch-aware `>= 80%` unless an explicit approved roadmap change replaces that threshold.

## 11. Phase 0 Result

All known predecessor debt is now assigned to v0.3 phases or explicitly deferred. Public/internal compatibility surfaces, migration/rollback expectations, hardening invariants and validation rules are explicit. No runtime implementation change is part of Phase 0.
