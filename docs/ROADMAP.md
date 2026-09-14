# ROADMAP
План розвитку K_Supervisor для переходу від PRE-ALPHA functional platform baseline до hardened autonomous platform foundation.

Version: 0.3
Status: ACTIVE
Approved: 2026-09-14
Roadmap start: 2026-09-14
Predecessor: ROADMAP v0.2 COMPLETE
Current phase: v0.3 Phase 0

## 1. Roadmap Rule

ROADMAP v0.3 uses revision-local phase numbering.

```text
v0.3 Phase 0
v0.3 Phase 1
...
v0.3 Phase 8
```

This is not a continuation of v0.2 numbering and does not create or imply a Phase 17.

Each phase must define:

- Goal;
- Scope / Deliverables;
- Tests;
- Exit Criteria;
- Deferred Work.

No phase may be marked COMPLETE without successful authoritative validation on the committed implementation baseline.

The completed ROADMAP v0.2 and its Core Validation remain the minimum compatibility/regression floor unless an explicitly approved change states otherwise.

## 2. Program Objective

Move K_Supervisor from:

```text
PRE-ALPHA functional platform
```

to:

```text
hardened autonomous platform foundation
```

The program must harden the existing architecture rather than replace it with parallel control paths.

## 3. Overall Exit Criterion

ROADMAP v0.3 succeeds when K_Supervisor can reliably execute a long-running managed lifecycle for a real AI project through durable state, centralized side-effect control, isolated execution, a service/API boundary and production-grade observability while preserving the approved v0.2 architecture contracts.

A qualification project must progress from approved ProjectSpec to RELEASE_READY, survive restart/recovery, preserve owner-control boundaries and run concurrently with another independent project without Supervisor-core rewrites.

## 4. Preserved Architecture Invariants

The following remain mandatory throughout v0.3:

- Project is the top-level managed unit; Project != Task.
- Agent != Capability.
- ProjectSpec approval gates material project scope.
- workflows bind capabilities rather than concrete agent implementations where practical.
- Supervisor owns orchestration/routing boundaries.
- lifecycle state and operational state remain separate.
- persistence is platform-owned; hidden conversational memory is not authoritative state.
- Human Intervention represents owner-required actions explicitly.
- notification delivery does not equal owner action completion.
- email remains the first and primary owner notification transport.
- secrets remain protected references and are not embedded in normal documentation, notifications or audit payloads.
- policy/permission enforcement occurs before side effects.
- RELEASE_READY remains separate from publication.
- external publication remains owner-controlled unless a future explicit roadmap changes that boundary.
- K-Research & Critic v1.0.0 remains reference-only, not a runtime dependency.
- existing public package/CLI/config/entry-point compatibility rules remain governed by `COMPATIBILITY_POLICY.md`.

## v0.3 Phase 0 - Baseline Freeze & Hardening Contract

Status: ACTIVE

### Goal

Freeze the exact v0.2 predecessor baseline, classify technical debt and define hardening/migration rules before runtime changes.

### Scope / Deliverables

- preserve the completed v0.2 roadmap as an archived historical snapshot;
- record the v0.2 validated implementation baseline as the predecessor runtime baseline;
- classify known debt by v0.3 phase;
- define public vs internal compatibility surfaces;
- define migration and rollback expectations;
- define hardening invariants and prohibited parallel control paths;
- synchronize PROJECT_STATE, TEST_MATRIX, DOCS_INDEX, CHAT_HANDOFF and roadmap audit references;
- establish v0.3 phase completion and validation rules.

### Tests

- full v0.2 Core Validation remains PASS;
- contract compatibility review;
- package/CLI/public import smoke;
- extension entry-point regression review;
- documentation consistency review.

### Exit Criteria

- v0.2 predecessor baseline is immutable and traceable;
- all current technical-debt items are assigned, explicitly deferred or retired;
- every subsequent v0.3 phase has measurable deliverables/tests/exit criteria;
- no architecture-breaking ambiguity remains before Phase 1;
- v0.2 regression baseline passes unchanged.

### Deferred Work

Runtime hardening implementation belongs to Phase 1 and later.

## v0.3 Phase 1 - Persistence & Resource Hygiene

### Goal

Make persistence/resource ownership reliable for long-running execution while preserving the storage abstraction.

### Scope / Deliverables

- explicit storage connection lifecycle and ownership;
- transaction boundary hardening;
- migration/version mechanism for persistent schema evolution;
- storage repository abstractions that do not expose SQLite physical layout as a public contract;
- resource cleanup for temporary/test SQLite connections;
- recovery invariants for reopen/restart;
- documented storage replacement boundary.

### Tests

- open/close/reopen lifecycle;
- crash/restart recovery;
- forward migration tests;
- rollback on failed authoritative writes;
- concurrent access within supported limits;
- resource-leak/ResourceWarning checks.

### Exit Criteria

- Core Validation reports zero known SQLite ResourceWarning leaks attributable to platform/tests;
- restart recovery remains deterministic;
- invalid/unsupported migrations fail safely;
- storage backend remains replaceable behind the approved persistence boundary;
- all v0.2 regression tests pass.

### Deferred Work

- mandatory PostgreSQL deployment;
- distributed database clustering;
- cross-region replication.

## v0.3 Phase 2 - Durable Control State

### Goal

Move critical control decisions out of process-local memory so execution can resume safely after restart.

### Scope / Deliverables

- durable runtime/command idempotency;
- durable notification/execution deduplication state;
- approval expiry and revocation lifecycle;
- richer authoritative recovery snapshot/aggregate reconstruction;
- stronger atomicity between authoritative state and required audit records;
- durable control records required to resume active workflows/projects.

### Tests

- restart between state transitions;
- duplicate command replay;
- duplicate external invocation protection;
- duplicate notification delivery attempt protection;
- approval expiry/revocation;
- interrupted workflow recovery;
- recovery without hidden in-memory state.

### Exit Criteria

- process restart does not change idempotency semantics;
- replay of the same command cannot create an unintended duplicate side effect through the standard path;
- approval expiry/revocation is enforceable and auditable;
- active project state can be reconstructed from authoritative persisted data;
- all prior regression gates pass.

### Deferred Work

- cross-region consensus;
- distributed event sourcing;
- global exactly-once guarantees across arbitrary third-party systems.

## v0.3 Phase 3 - Centralized Side-Effect Enforcement

### Goal

Create one mandatory platform-controlled path for material external side effects.

### Scope / Deliverables

- centralized Tool Gateway / execution gateway;
- normalized tool invocation contract;
- policy/risk/permission enforcement before invocation;
- approval enforcement before approval-gated invocation;
- protected access-reference resolution at execution time;
- idempotency key propagation where supported;
- normalized audit/telemetry of invocation decisions and outcomes;
- explicit prohibition of standard-path bypass around the gateway.

### Tests

- denied operation never executes;
- approval-required operation blocks before execution;
- revoked/expired approval blocks execution;
- missing/invalid protected reference blocks execution;
- duplicate invocation handling;
- provider/tool failure normalization;
- attempted unauthorized bypass is rejected by platform interfaces.

### Exit Criteria

- standard platform external side effects cannot execute without policy/permission enforcement;
- material permission expansion still requires explicit approval;
- protected secrets are not emitted into ordinary state/audit/notification payloads;
- side-effect decisions and results are reconstructable from authoritative records;
- all prior regression gates pass.

### Deferred Work

- universal sandbox for arbitrary third-party code;
- public tool marketplace.

## v0.3 Phase 4 - Runtime Isolation & Cancellation

### Goal

Strengthen execution isolation so a failed or non-cooperative agent cannot compromise the Supervisor process.

### Scope / Deliverables

- hardened runtime backend abstraction;
- isolated worker/process execution option;
- bounded termination path;
- timeout/cancellation escalation;
- worker/resource limit enforcement appropriate to the backend;
- worker health/unavailability state;
- crash/termination normalization through Agent Contract statuses;
- preserve in-process execution only as an explicit trusted/test option.

### Tests

- hung agent;
- ignored cooperative cancellation;
- worker crash;
- timeout escalation;
- repeated worker failures;
- resource limit violation;
- Supervisor remains responsive after worker failure.

### Exit Criteria

- an unresponsive isolated execution cannot indefinitely block the Supervisor process;
- every supported execution mode has a bounded termination/recovery path;
- worker failure is normalized and auditable;
- Agent Contract semantics remain compatible;
- all prior regression gates pass.

### Deferred Work

- Kubernetes requirement;
- remote execution cluster;
- arbitrary container scheduler.

## v0.3 Phase 5 - Service/API Boundary

### Goal

Expose K_Supervisor as a controlled service without creating a second control plane.

### Scope / Deliverables

- versioned HTTP and/or RPC service boundary;
- project create/read/status/control operations;
- ProjectSpec submission and approval operations;
- task/workflow execution/status operations;
- HumanActionRequest read/complete/verify operations where allowed;
- release/readiness/status operations;
- health/readiness endpoints;
- authentication/authorization boundary appropriate to PRE-ALPHA hardening;
- idempotent command semantics for mutating API operations;
- API delegates to existing Supervisor/Control Plane contracts rather than bypassing them.

### Tests

- service contract validation;
- invalid lifecycle transitions;
- authorization boundary;
- idempotent command replay;
- restart continuity;
- API cannot bypass policy/approval/tool gateway;
- CLI/Python/public contract compatibility.

### Exit Criteria

- the primary managed project lifecycle can be controlled through the service API without direct use of internal implementation modules;
- API operations preserve existing ProjectSpec/Supervisor/policy boundaries;
- public v0.2 package/CLI surfaces remain compatible unless an explicit versioned change is approved;
- all prior regression gates pass.

### Deferred Work

- public SaaS UI;
- multi-tenant billing;
- mobile client.

## v0.3 Phase 6 - Production Observability

### Goal

Make long-running autonomous behavior diagnosable from supported telemetry rather than ad-hoc database inspection.

### Scope / Deliverables

- persisted operational telemetry required for incident reconstruction;
- correlation/trace identifiers across Project -> Supervisor -> Runtime -> Tool Gateway;
- structured logging contract;
- metrics export boundary;
- trace export boundary compatible with common standards;
- health/readiness instrumentation;
- SLO-compatible measurements/foundations;
- sensitive-data redaction rules and tests.

### Tests

- reconstruct a project execution timeline;
- diagnose a failed workflow from supported records;
- correlate Supervisor/runtime/tool events;
- telemetry continuity after restart;
- secret/protected-reference redaction;
- metrics/trace exporter contract tests.

### Exit Criteria

- material execution paths can answer what happened, where, why and what authoritative state remains;
- operational telemetry survives the restart boundaries required by the design;
- telemetry does not expose protected credentials;
- observability does not alter control-plane authority;
- all prior regression gates pass.

### Deferred Work

- mandatory dependency on a specific observability SaaS/vendor;
- full enterprise SLO management suite.

## v0.3 Phase 7 - Extension Trust & Platform Governance

### Goal

Make extensibility and repository operation safer without breaking the Phase 16 public extension baseline.

### Scope / Deliverables

- durable extension metadata where platform operation requires durability;
- explicit extension compatibility/trust state;
- allow/deny activation policy;
- extension provenance metadata;
- signature-verification boundary where feasible;
- extension isolation requirements aligned with Runtime Phase 4;
- preserve stable Phase 16 entry-point group names;
- repository governance policy for `main`;
- required CI/status-check policy where repository capabilities allow it;
- resolve current CI action deprecation warnings where practical.

### Tests

- incompatible extension rejection;
- unknown/untrusted extension handling;
- disabled extension handling;
- invalid/malicious registration behavior;
- extension entry-point regression;
- repository/CI governance validation.

### Exit Criteria

- extension discovery alone never implies automatic trust/activation;
- activation requires explicit compatibility/trust decision;
- existing documented extension entry-point names remain supported;
- repository merge/deployment workflow has documented mandatory validation gates;
- all prior regression gates pass.

### Deferred Work

- universal security guarantee for arbitrary hostile Python packages;
- public third-party marketplace governance.

## v0.3 Phase 8 - Operational Readiness & Autonomous Lifecycle Qualification

### Goal

Qualify K_Supervisor as an integrated hardened system rather than a collection of hardened components.

### Scope / Deliverables

- end-to-end qualification project;
- repeatable deployment/runbook;
- backup and restore procedure;
- upgrade/migration procedure from the predecessor supported baseline;
- package/release pipeline through the owner-controlled publication boundary;
- operational readiness checklist;
- failure/restart recovery qualification;
- concurrent-project qualification;
- Human Intervention + email + resume qualification;
- FIRST_WORKING and RELEASE_READY qualification.

### Tests

The qualification flow must exercise:

```text
Onboarding / ProjectSpec creation
-> owner approval
-> repository/bootstrap
-> provisioning
-> workflow/roadmap execution
-> controlled Tool Gateway side effects
-> HumanActionRequest when required
-> email notification
-> owner action / verification
-> automatic resume where possible
-> FIRST_WORKING
-> validation
-> RELEASE_READY
-> owner publication handoff
```

Additional tests:

- clean deployment;
- restart while a project is active;
- deterministic failure injection;
- backup/restore;
- supported upgrade/migration;
- concurrent second project continues while the first waits for owner action;
- full v0.2 and v0.3 regression suite.

### Exit Criteria

- one real qualification project progresses from approved ProjectSpec to RELEASE_READY through supported platform boundaries;
- restart/recovery does not lose authoritative control state;
- a waiting/blocked project does not block an independent project;
- side effects remain policy-controlled;
- owner action/publication boundaries remain explicit;
- deployment/recovery/upgrade procedures are documented and validated;
- full authoritative regression suite passes on the committed baseline.

### Deferred Work

- automatic GPT Store publication;
- WhatsApp/Viber or other non-email messaging transports unless explicitly promoted into scope;
- distributed execution clusters;
- remote agents as a required baseline;
- event bus architecture;
- multi-tenant SaaS isolation/billing;
- advanced autonomous planning beyond the qualification needs.

## 5. Global Validation Gates

Every runtime implementation phase must preserve at minimum:

```text
Core Validation                PASS
branch-aware coverage          >= 80%
compileall including examples  PASS
isolated wheel build           PASS
wheel install outside checkout PASS
public CLI/import smoke         PASS
v0.2 compatibility regression  PASS
```

Additional v0.3 tests are cumulative unless an approved roadmap amendment states otherwise.

A phase is not COMPLETE merely because its code exists. Completion requires committed evidence, passing required validation and synchronized canonical documentation/checkpoint records.

## 6. Compatibility Rule

`COMPATIBILITY_POLICY.md` remains active.

In particular, the following Phase 16 entry-point groups remain stable compatibility surfaces:

```text
k_supervisor.agents
k_supervisor.capabilities
k_supervisor.project_templates
k_supervisor.adapters
```

Changes that cannot safely interpret existing public configuration must use a new `config_version` with migration guidance.

## 7. Notification and Publication Boundaries

Email remains the primary required notification channel for v0.3.

Non-email transports remain extension/future work unless separately approved.

Release preparation may be automated. External publication remains an explicit per-project owner action.

## 8. Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
Current approved phase: v0.3 Phase 0
v0.3 Phase 0 status: ACTIVE
v0.3 Phase 1-8 status: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

Approval of this roadmap authorizes Phase 0 documentation/baseline work. Runtime implementation proceeds phase-by-phase under the active roadmap and must not skip required exit criteria.

## 9. Historical Record

The full completed predecessor roadmap is preserved in:

- `docs/ROADMAP_V0_2_ARCHIVE.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md`;
- `docs/ROADMAP_IMPLEMENTATION_AUDIT.md`.
