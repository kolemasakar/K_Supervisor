# TEST_MATRIX
Матриця regression-перевірок K_Supervisor для завершеного ROADMAP v0.2 та активного ROADMAP v0.3.

Version: 1.7
Status: ACTIVE
Roadmap baseline: v0.2 COMPLETE + v0.3 ACTIVE
Current phase: v0.3 Phase 3
Handoff state: Phase 3 authorized; runtime implementation NOT STARTED as of 2026-09-14

## v0.2 Regression Matrix

The completed ROADMAP v0.2 test families remain the minimum regression floor for all v0.3 work.

| v0.2 Phase | Primary verification | Test family |
| --- | --- | --- |
| 1 | contracts, schemas, invalid transitions | `test_phase1_*` |
| 2 | restart recovery, isolation, immutable ProjectSpec | `test_phase2_*` |
| 3 | intervention, notifications, SMTP adapter, idempotency | `test_phase3_*` |
| 4 | registries, version compatibility, provider availability | `test_phase4_*` |
| 5 | dynamic routing, dispatch, retry, task state | `test_phase5_*` |
| 6 | repository bootstrap, owner boundary, conflict protection | `test_phase6_*` |
| 7 | workflow graph, conditions, bounded loops, approvals | `test_phase7_*` |
| 8 | runtime errors, timeout, cancellation, limits, health | `test_phase8_*` |
| 9 | parallel projects, priorities, locks, budgets, concurrency | `test_phase9_*` |
| 10 | access references, registries, provisioning, model selection | `test_phase10_*` |
| 11 | policy allow/deny/approval and durable audit | `test_phase11_*` |
| 12 | scaffolding, reference agents, provider interchangeability | `test_phase12_*` |
| 13 | release readiness, publication gate, release recovery | `test_phase13_*` |
| 14 | profile gate, research-review loop, bounded revision, legacy isolation | `test_phase14_*` |
| 15 | structured audit, routing records, metrics, failure injection, recovery, performance | `test_phase15_*` |
| 16 | public config/CLI, extension discovery/activation, examples, package build/install | `test_phase16_*` + CI package smoke |

## v0.3 Phase Status

| Phase | Required verification | Status |
| --- | --- | --- |
| 0 | predecessor traceability, compatibility review, full v0.2 regression evidence, documentation consistency | COMPLETE |
| 1 | storage lifecycle, reopen/restart, migration, rollback, supported concurrency, ResourceWarning cleanup | COMPLETE |
| 2 | durable idempotency, command replay, approval lifecycle, restart recovery, aggregate reconstruction | COMPLETE |
| 3 | centralized Tool Gateway policy paths, protected references, repeated invocation handling, normalized audit | ACTIVE / NOT STARTED AT HANDOFF |
| 4 | unresponsive worker, cancellation escalation, timeout, crash isolation, bounded termination | PLANNED |
| 5 | API contracts, access control, invalid transitions, idempotent mutations, restart continuity | PLANNED |
| 6 | correlation, persisted telemetry, timeline reconstruction, exporter contracts, health/readiness, redaction | PLANNED |
| 7 | extension compatibility/trust state, disabled extension behavior, entry-point regression, CI governance | PLANNED |
| 8 | deployment, complete lifecycle qualification, failure injection, backup/restore, migration, parallel-project isolation | PLANNED |

## Phase 1 Evidence

```text
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Core Validation run: 34804141156
pytest: 95 passed
branch-aware coverage: 85.66%
ResourceWarning gate: PASS
```

Primary Phase 1 tests: `tests/test_v03_phase1_persistence_hardening.py`.

## Phase 2 Evidence

Authoritative implementation baseline:

```text
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Core Validation run: 34808287772
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
coverage gate: PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public interface smoke: PASS
```

Phase 2 hardening tests:

```text
tests/test_v03_phase2_durable_control_state.py
tests/test_v03_phase2_restart_resume.py
```

Verified behaviors:

- persistence-backed runtime idempotency survives restart;
- command replay reuses the prior authoritative successful result without invoking the handler again;
- idempotency scope is isolated by project;
- notification SENT duplicate suppression survives restart;
- approval expiry is deterministic and persisted;
- approval revocation is persisted and rejected by subsequent policy evaluation;
- expiry/revocation lifecycle changes are durably audited;
- richer ProjectRecoverySnapshot reconstructs Human Intervention, notification/delivery, approval, runtime-idempotency, policy, audit, routing and release-validation state;
- interrupted Task/WorkflowRun + WAITING_FOR_OWNER state reconstructs after restart and resumes through Human Intervention;
- injected audit failure rolls back matching Project transition + Project snapshot;
- all predecessor regression tests remain green.

Completion record: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`.

## Phase 3 Start Gate

Before any Phase 3 runtime code is changed in the new chat:

- read `PROJECT_HANDOFF_2026_09_16.md` and the current canonical roadmap/state documents;
- verify current `main` against implementation SHA `573cbe433ece8ffae45d83a30fd3287fac40d820`;
- confirm that any commits after that SHA are documentation-only unless a later explicit implementation checkpoint exists;
- audit all standard production paths capable of material external side effects;
- identify current policy, tool-permission, protected-reference, idempotency and audit insertion points;
- preserve all completed v0.2 + v0.3 Phase 0-2 tests as cumulative regression requirements.

## Phase 3 Required Verification

Phase 3 implementation must prove:

- standard material side effects execute through the centralized gateway path;
- ALLOW permits one normalized adapter invocation;
- DENY prevents adapter invocation;
- REQUIRE_APPROVAL prevents adapter invocation until permission is approved;
- requested tool/operation permissions are checked before invocation;
- protected references are authorized before resolution/use;
- project/request/agent/capability correlation reaches the side-effect record;
- idempotency is propagated and repeated invocation does not create an unintended duplicate through the supported path;
- tool/provider failures are normalized and durably audited;
- concrete adapters remain replaceable behind the gateway contract;
- all completed v0.2 + v0.3 regression tests remain green.

## Permanent Quality Gates

```text
structured audit        -> material project/control records
integration             -> Supervisor + registries + runtime + persistence + policy boundaries
failure injection       -> deterministic transport/runtime/storage/provider failures
recovery                -> authoritative state reconstruction after supported restart/reopen boundaries
referential integrity   -> ReliabilityValidator or approved successor boundary
metrics/telemetry       -> phase-appropriate project/agent/operational metrics
performance             -> existing v0.2 baseline remains unless explicitly superseded
coverage                -> branch-aware total coverage >= 80%
resource hygiene        -> ResourceWarning is a CI error
syntax                  -> compileall including examples
packaging               -> isolated wheel build
installation            -> wheel install outside source checkout
public interface smoke  -> k-supervisor version + import ksupervisor outside checkout
compatibility           -> v0.2 public package/CLI/config/entry-point regression
```

## Current Authoritative Runtime Baseline

```text
Core Validation run: 34808287772
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
coverage gate: PASS
ResourceWarning gate: PASS
wheel build/install: PASS
public interface smoke: PASS
```

## CI Rule

`Core Validation` remains the authoritative automated regression workflow. No runtime implementation phase may claim completion without a successful full suite on its committed implementation baseline.