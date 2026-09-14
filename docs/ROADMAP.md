# ROADMAP
K_Supervisor active development roadmap.

Version: 0.3
Status: ACTIVE
Approved: 2026-09-14
Roadmap start: 2026-09-14
Predecessor: ROADMAP v0.2 COMPLETE
Current phase: v0.3 Phase 2

## Program Objective

Move K_Supervisor from the completed PRE-ALPHA functional baseline to a hardened autonomous platform foundation while preserving the approved architecture and public compatibility baseline.

ROADMAP v0.3 uses revision-local numbering. It defines `v0.3 Phase 0` through `v0.3 Phase 8` and does not define Phase 17.

## Phase Status

| Phase | Name | Status |
| --- | --- | --- |
| v0.3 Phase 0 | Baseline Freeze & Hardening Contract | COMPLETE |
| v0.3 Phase 1 | Persistence & Resource Hygiene | COMPLETE |
| v0.3 Phase 2 | Durable Control State | ACTIVE |
| v0.3 Phase 3 | Centralized Side-Effect Enforcement | PLANNED |
| v0.3 Phase 4 | Runtime Isolation & Cancellation | PLANNED |
| v0.3 Phase 5 | Service/API Boundary | PLANNED |
| v0.3 Phase 6 | Production Observability | PLANNED |
| v0.3 Phase 7 | Extension Trust & Platform Governance | PLANNED |
| v0.3 Phase 8 | Operational Readiness & Autonomous Lifecycle Qualification | PLANNED |

## Completed Phase 0

Phase 0 froze the predecessor implementation and validation baseline, classified technical debt and established cumulative hardening/compatibility rules.

Evidence:

- `HARDENING_BASELINE_V0_3.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md`.

## Completed Phase 1

Phase 1 hardened persistence/resource ownership without changing public/domain contracts.

Validated baseline:

```text
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Core Validation run: 34804141156
Python: 3.13.15
pytest: 95 passed
branch-aware coverage: 85.66%
ResourceWarning gate: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Evidence:

- `PERSISTENCE.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md`.

## Active Phase 2 - Durable Control State

Goal: move critical control decisions out of process-local memory so active work can resume safely after restart.

Required deliverables:

- durable runtime/command idempotency;
- durable notification/execution deduplication state where required by standard platform paths;
- approval expiry and revocation lifecycle;
- richer authoritative recovery snapshot/aggregate reconstruction;
- stronger atomicity between authoritative control state and required audit records;
- durable control records required to resume active workflows/projects.

Required tests:

- restart between state transitions;
- duplicate command replay;
- duplicate execution/notification protection;
- approval expiry and revocation;
- interrupted workflow/project recovery;
- aggregate reconstruction without hidden process memory;
- full Phase 0-1 and v0.2 regression suite.

Exit criteria:

- process restart does not change supported idempotency semantics;
- replay of the same command does not create an unintended duplicate operation through the standard path;
- approval expiry/revocation is enforceable and auditable;
- active project/control state can be reconstructed from authoritative persisted data;
- required authoritative control writes and audit records use the defined atomic boundary;
- Core Validation PASS on the committed Phase 2 implementation baseline.

Deferred from Phase 2: distributed consensus, cross-region event sourcing and universal exactly-once guarantees across arbitrary external systems.

## Validation Rule

Every runtime implementation phase must preserve the permanent regression floor:

```text
Core Validation                PASS
branch-aware coverage          >= 80%
ResourceWarning gate           PASS
compileall including examples  PASS
isolated wheel build           PASS
wheel install outside checkout PASS
public CLI/import smoke         PASS
v0.2 compatibility regression  PASS
```

## Preserved Baseline

Project/Task and Agent/Capability remain separate; ProjectSpec approval remains authoritative for material scope; Supervisor remains the orchestration boundary; platform state remains authoritative and persisted; owner-required actions and publication remain explicit; email remains the primary required notification transport; K-Research & Critic remains reference-only.

Detailed debt ownership and hardening constraints are in `HARDENING_BASELINE_V0_3.md`. Required verification is maintained in `TEST_MATRIX.md`. The completed predecessor roadmap is preserved in `ROADMAP_V0_2_ARCHIVE.md`.
