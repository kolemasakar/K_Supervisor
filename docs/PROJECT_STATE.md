# PROJECT_STATE
Канонічний поточний знімок K_Supervisor після завершення ROADMAP v0.3 Phase 0.

Version: 1.9
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
Current approved phase: v0.3 Phase 1
v0.3 Phase 1 status: ACTIVE
v0.3 Phase 2-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

The runtime implementation remains the validated v0.2 predecessor baseline until Phase 1 produces a new committed implementation checkpoint.

```text
Core Validation run: 34793901147
Implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: >= 80% PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

## Phase 0 Completion

Phase 0 froze the predecessor baseline and hardening contract without runtime changes.

Authoritative records:

- `HARDENING_BASELINE_V0_3.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md`;
- `ROADMAP_V0_2_ARCHIVE.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md`.

All known predecessor technical debt is assigned to a v0.3 phase or explicitly deferred in `HARDENING_BASELINE_V0_3.md`.

## Active Phase 1 Scope

`v0.3 Phase 1 - Persistence & Resource Hygiene` is authorized for implementation.

Primary scope:

- explicit persistence connection lifecycle/ownership;
- transaction-boundary hardening;
- persistent schema version/migration mechanism;
- storage abstractions independent of SQLite physical layout;
- cleanup of known SQLite ResourceWarning leaks;
- deterministic reopen/restart recovery;
- documented storage replacement boundary.

Phase 1 may not be marked COMPLETE until its phase-specific tests and full permanent regression suite pass on the committed implementation baseline.

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

`COMPATIBILITY_POLICY.md` remains authoritative.

## Preserved Architecture Rules

Project remains the top-level managed unit; Agent and Capability remain separate; workflows remain capability-oriented; Supervisor owns orchestration; authoritative state is platform-owned; Human Intervention and owner publication remain explicit; email remains the primary required owner notification transport; policy/permission checks precede material external actions; K-Research & Critic remains reference-only.

## Current Hardening Debt

The frozen debt assignment is maintained in `HARDENING_BASELINE_V0_3.md`.

Phase 1 owns persistence/resource hygiene. Later phases own durable control state, centralized external-action control, runtime isolation, service/API boundary, production observability, extension/repository governance and end-to-end operational qualification.

## Validation Rule

The v0.2 predecessor suite is the minimum regression floor. Runtime implementation phases require successful Core Validation on their committed implementation SHA before completion.
