# ROADMAP
K_Supervisor active development roadmap.

Version: 0.3
Status: ACTIVE
Approved: 2026-09-14
Roadmap start: 2026-09-14
Predecessor: ROADMAP v0.2 COMPLETE
Current phase: v0.3 Phase 4 COMPLETE; v0.3 Phase 5 PLANNED
Phase 4 implementation completed: 2026-09-16
Phase 5 transition handoff prepared: 2026-09-16
Phase 5 activation: NO

## Program Objective

Move K_Supervisor from the completed PRE-ALPHA functional baseline to a hardened autonomous platform foundation while preserving the approved architecture and public compatibility baseline.

ROADMAP v0.3 uses revision-local numbering. It defines `v0.3 Phase 0` through `v0.3 Phase 8` and does not define Phase 17.

## Phase Status

| Phase | Name | Status |
| --- | --- | --- |
| v0.3 Phase 0 | Baseline Freeze & Hardening Contract | COMPLETE |
| v0.3 Phase 1 | Persistence & Resource Hygiene | COMPLETE |
| v0.3 Phase 2 | Durable Control State | COMPLETE |
| v0.3 Phase 3 | Centralized Side-Effect Enforcement | COMPLETE |
| v0.3 Phase 4 | Runtime Isolation & Cancellation | COMPLETE |
| v0.3 Phase 5 | Service/API Boundary | PLANNED |
| v0.3 Phase 6 | Production Observability | PLANNED |
| v0.3 Phase 7 | Extension Trust & Platform Governance | PLANNED |
| v0.3 Phase 8 | Operational Readiness & Autonomous Lifecycle Qualification | PLANNED |

Phase 4 is COMPLETE on the validated implementation baseline. Phase 5 remains PLANNED / NOT STARTED.

## Completed Phase 0

Phase 0 froze the predecessor implementation and validation baseline, classified technical debt and established cumulative hardening/compatibility rules.

Evidence:

- `HARDENING_BASELINE_V0_3.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md`.

## Completed Phase 1

Phase 1 hardened persistence/resource ownership and schema evolution.

Validated baseline:

```text
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Core Validation run: 34804141156
pytest: 95 passed
branch-aware coverage: 85.66%
ResourceWarning gate: PASS
```

Evidence: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md`.

## Completed Phase 2

Phase 2 moved critical control state onto durable, restart-safe platform boundaries.

Validated baseline:

```text
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Core Validation run: 34808287772
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Delivered durable runtime idempotency, restart-safe notification deduplication, approval expiry/revocation, richer recovery aggregation, restart/resume verification and atomic state+audit persistence for core Project/Human Intervention/Approval control writes.

Evidence:

- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`;
- `PERSISTENCE.md`;
- `AGENT_RUNTIME.md`;
- `POLICY_AND_PERMISSIONS.md`.

## Completed Phase 3 - Centralized Side-Effect Enforcement

Goal: establish one standard platform boundary for material external side effects so policy, permissions, protected references, idempotency and audit are enforced before invocation rather than relying on each caller to compose them correctly.

Implementation state:

```text
Authorized: YES
Pre-implementation audit: COMPLETE
Runtime implementation: COMPLETE
Implementation SHA: 6868d595b66a6ada91a2e6f2f62866721d0f3560
Core Validation run: 35086116020
Python: 3.13.15
pytest: 111 passed
branch-aware coverage: 85.45%
Core Validation: PASS
```

Pre-implementation evidence: `PHASE3_PREIMPLEMENTATION_AUDIT.md`. Completion evidence: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_3_COMPLETE.md`.

Required deliverables:

- centralized Tool Gateway / side-effect execution gateway for standard platform paths;
- normalized side-effect invocation/result contract;
- mandatory policy and permission validation before gateway execution;
- protected-reference authorization before resolution/use;
- propagation of project/request/agent/capability correlation and idempotency keys;
- normalized durable side-effect attempt/outcome audit;
- deterministic denied/approval-required behavior with no external invocation;
- adapter boundary that keeps concrete tools/providers replaceable.

Required tests:

- ALLOW path invokes the adapter once through the gateway;
- DENY path never invokes the adapter;
- REQUIRE_APPROVAL path never invokes the adapter until approved;
- tool-operation permission enforcement;
- protected-reference authorization enforcement;
- repeated invocation/idempotency behavior;
- provider/tool failure normalization and audit;
- correlation/audit persistence;
- full completed v0.2 + v0.3 regression suite.

Exit criteria:

- standard production-composition material side effects have a centralized enforceable gateway path;
- policy/permission/protected-reference checks occur before external invocation;
- denied or approval-required requests cannot reach the external adapter through the standard path;
- side-effect correlation, idempotency and durable audit are explicit and tested;
- concrete adapters remain replaceable without Supervisor-core rewrites;
- Core Validation PASS on the committed Phase 3 implementation baseline.

Deferred from Phase 3: arbitrary third-party Python sandboxing, distributed transaction guarantees and universal exactly-once semantics across external systems.

Successor Phase 4 is now complete. Phase 5 remains PLANNED / NOT STARTED and is not activated by Phase 4 completion.

## Completed Phase 4 - Runtime Isolation & Cancellation

Goal: replace cooperative-only runtime termination as the sole hardened path with an isolated worker boundary that the parent can terminate within bounded intervals.

Validated baseline:

```text
Implementation SHA: 34049f601fc8116aa12ee15023f1dc20bc25901a
Core Validation run: 35092932820
Python: 3.13.15
pytest: 117 passed
branch-aware coverage: 85.13%
Core Validation: PASS
```

Delivered a replaceable `ProcessRuntimeAdapter`, parent-enforced timeout/cancellation escalation, bounded worker cleanup, worker-crash containment and normalized cross-process runtime errors while preserving the in-process compatibility adapter and existing Supervisor/Workflow contracts.

Required Phase 4 tests cover isolated execution, unresponsive timeout, cancellation escalation, abnormal worker exit, runtime-limit normalization and recovery on the next run. Full predecessor regressions remain green.

Evidence:

- `PHASE4_PREIMPLEMENTATION_AUDIT.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_4_COMPLETE.md`;
- `AGENT_RUNTIME.md`;
- `TEST_MATRIX.md`.

Phase 4 does not claim universal sandboxing for arbitrary untrusted Python, distributed worker clusters, container orchestration or remote execution. Those remain outside this phase.

Next roadmap phase: `v0.3 Phase 5 - Service/API Boundary`, status `PLANNED / NOT STARTED`. The new-chat handoff is prepared in `PROJECT_HANDOFF_2026_09_16_PHASE_5.md`; handoff preparation does not activate Phase 5.

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
