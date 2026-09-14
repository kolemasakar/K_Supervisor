# ROADMAP
K_Supervisor active development roadmap.

Version: 0.3
Status: ACTIVE
Approved: 2026-09-14
Roadmap start: 2026-09-14
Predecessor: ROADMAP v0.2 COMPLETE
Current phase: v0.3 Phase 1

## Program Objective

Move K_Supervisor from the completed PRE-ALPHA functional baseline to a hardened autonomous platform foundation while preserving the approved architecture and public compatibility baseline.

ROADMAP v0.3 uses revision-local numbering. It defines `v0.3 Phase 0` through `v0.3 Phase 8` and does not define Phase 17.

## Phase Status

| Phase | Name | Status |
| --- | --- | --- |
| v0.3 Phase 0 | Baseline Freeze & Hardening Contract | COMPLETE |
| v0.3 Phase 1 | Persistence & Resource Hygiene | ACTIVE |
| v0.3 Phase 2 | Durable Control State | PLANNED |
| v0.3 Phase 3 | Centralized Action Gateway | PLANNED |
| v0.3 Phase 4 | Runtime Isolation & Cancellation | PLANNED |
| v0.3 Phase 5 | Service/API Boundary | PLANNED |
| v0.3 Phase 6 | Production Observability | PLANNED |
| v0.3 Phase 7 | Extension and Platform Governance | PLANNED |
| v0.3 Phase 8 | Operational Readiness & Autonomous Lifecycle Qualification | PLANNED |

## Phase 0 Result

Phase 0 is COMPLETE. It froze the predecessor implementation and validation baseline, classified technical debt, defined compatibility and migration rules, and established cumulative validation requirements.

Evidence:

- `HARDENING_BASELINE_V0_3.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md`;
- predecessor implementation SHA `755be348fc3376ad5c09f178a3268b0fb7685107`;
- Core Validation run `34793901147`, PASS.

## Active Phase 1

Goal: make persistence and resource ownership reliable for long-running execution while preserving the storage abstraction.

Required deliverables:

- explicit storage connection lifecycle and ownership;
- transaction-boundary hardening;
- persistent schema version and migration mechanism;
- storage abstractions independent of SQLite physical layout;
- cleanup of known SQLite ResourceWarning leaks;
- deterministic reopen/restart recovery;
- documented storage replacement boundary.

Required tests:

- open/close/reopen;
- restart recovery;
- forward migration;
- rollback behavior;
- supported concurrent access;
- ResourceWarning checks;
- full v0.2 regression suite.

Exit criteria:

- zero known SQLite ResourceWarning leaks attributable to platform/tests;
- deterministic restart recovery;
- unsupported migrations fail safely;
- storage remains replaceable behind the approved persistence boundary;
- Core Validation PASS on the committed Phase 1 implementation baseline.

Deferred from Phase 1: mandatory PostgreSQL deployment, distributed clustering and cross-region replication.

## Validation Rule

Every runtime implementation phase must preserve the permanent regression floor:

```text
Core Validation                PASS
branch-aware coverage          >= 80%
compileall including examples  PASS
isolated wheel build           PASS
wheel install outside checkout PASS
public CLI/import smoke         PASS
v0.2 compatibility regression  PASS
```

## Preserved Baseline

Project/Task and Agent/Capability remain separate; ProjectSpec approval remains authoritative for material scope; Supervisor remains the orchestration boundary; platform state remains authoritative and persisted; owner-required actions and publication remain explicit; email remains the primary required notification transport; K-Research & Critic remains reference-only.

Detailed v0.3 debt ownership and hardening constraints are in `HARDENING_BASELINE_V0_3.md`. Required verification is maintained in `TEST_MATRIX.md`. The completed predecessor roadmap is preserved in `ROADMAP_V0_2_ARCHIVE.md`.
