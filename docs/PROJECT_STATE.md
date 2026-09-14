# PROJECT_STATE
Канонічний поточний знімок K_Supervisor після завершення ROADMAP v0.3 Phase 2.

Version: 2.1
Status: ACTIVE
Date: 2026-09-14

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Package: k-supervisor==0.1.0
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0: COMPLETE
v0.3 Phase 1: COMPLETE
v0.3 Phase 2: COMPLETE
Current approved phase: v0.3 Phase 3
v0.3 Phase 3 status: ACTIVE
v0.3 Phase 4-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Validated Runtime Baseline

```text
Core Validation run: 34808287772
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Documentation-only closure commits after this implementation SHA do not replace the validated runtime baseline unless a later implementation checkpoint explicitly states otherwise.

## Phase 2 Completion

ROADMAP v0.3 Phase 2 completed durable control-state hardening:

- persistence-backed runtime/command idempotency for the standard AgentRuntimeDispatcher path;
- project-scoped idempotency and restart-safe successful-result replay;
- durable notification delivery history used for restart-safe duplicate suppression;
- approval `EXPIRED` and `REVOKED` lifecycle states with policy enforcement;
- durable approval lifecycle audit;
- expanded `ProjectRecoverySnapshot` for Human Intervention, notifications/delivery, approvals, runtime idempotency, policy, audit, routing and release-validation state;
- Project lifecycle/operational changes, ProjectSpec activation, Human Intervention and Approval control writes use atomic state+audit persistence helpers where required;
- interrupted waiting project/task/workflow state reconstructs after restart and can resume through the normal Human Intervention path.

Authoritative records:

- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`;
- `PERSISTENCE.md`;
- `AGENT_RUNTIME.md`;
- `POLICY_AND_PERMISSIONS.md`.

SQLite schema remains version 2 because Phase 2 control records use the existing generic resources/events storage layout.

## Active Phase 3 Scope

`v0.3 Phase 3 - Centralized Side-Effect Enforcement` is authorized for implementation.

Primary scope:

- centralized Tool Gateway / side-effect execution gateway for standard platform paths;
- normalized invocation/result contract;
- policy, tool-permission and protected-reference enforcement before external invocation;
- correlation and idempotency propagation;
- normalized durable side-effect audit;
- deterministic no-invocation semantics for denied or approval-required requests;
- replaceable concrete tool/provider adapters.

Phase 3 may not be marked COMPLETE until its phase-specific tests and the full cumulative regression suite pass on its committed implementation baseline.

## Public Compatibility Baseline

```text
Python facade: ksupervisor
CLI: k-supervisor
Config version: 1
Extension groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

`COMPATIBILITY_POLICY.md` remains authoritative. Phase 2 preserved the distribution/CLI/config/entry-point baseline.

## Preserved Architecture Rules

Project remains the top-level managed unit; Agent and Capability remain separate; workflows remain capability-oriented; Supervisor owns orchestration; authoritative state is platform-owned; Human Intervention and owner publication remain explicit; email remains the primary required owner notification transport; policy/permission checks precede material external actions; K-Research & Critic remains reference-only.

## Remaining Hardening Debt

Completed:

- Phase 1 persistence/resource hygiene;
- Phase 2 durable control state.

Remaining roadmap ownership begins with centralized side-effect enforcement, followed by runtime isolation, service/API boundary, production observability, extension/repository governance and end-to-end operational qualification.

Distributed consensus, cross-region event sourcing and universal provider-level exactly-once guarantees remain explicitly deferred rather than hidden Phase 2 failures.

## Validation Rule

The completed v0.2 regression baseline plus completed v0.3 phase tests are cumulative. Runtime implementation phases require successful Core Validation on their committed implementation SHA before completion.
