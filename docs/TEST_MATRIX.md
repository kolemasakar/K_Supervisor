# TEST_MATRIX
Матриця regression-перевірок K_Supervisor для завершеного ROADMAP v0.2 та активного ROADMAP v0.3.

Version: 1.4
Status: ACTIVE
Roadmap baseline: v0.2 COMPLETE + v0.3 ACTIVE
Current phase: v0.3 Phase 1

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
| 1 | storage lifecycle, reopen/restart, migration, rollback, supported concurrency, ResourceWarning cleanup | ACTIVE |
| 2 | durable idempotency, command replay, approval lifecycle, restart recovery, aggregate reconstruction | PLANNED |
| 3 | centralized Tool Gateway policy paths, protected references, repeated invocation handling, normalized audit | PLANNED |
| 4 | unresponsive worker, cancellation escalation, timeout, crash isolation, bounded termination | PLANNED |
| 5 | API contracts, access control, invalid transitions, idempotent mutations, restart continuity | PLANNED |
| 6 | correlation, persisted telemetry, timeline reconstruction, exporter contracts, health/readiness, redaction | PLANNED |
| 7 | extension compatibility/trust state, disabled extension behavior, entry-point regression, CI governance | PLANNED |
| 8 | deployment, complete lifecycle qualification, failure injection, backup/restore, migration, parallel-project isolation | PLANNED |

## Phase 0 Evidence

```text
Implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Core Validation run: 34793901147
pytest: 88 passed
branch-aware coverage: 85.46%
compileall: PASS
wheel build/install: PASS
public interface smoke: PASS
runtime changes during Phase 0: none
```

Phase 0 completion records:

- `HARDENING_BASELINE_V0_3.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md`.

## Phase 1 Required Verification

Phase 1 implementation must add or extend tests proving:

- deterministic connection ownership/cleanup;
- explicit close/reopen behavior;
- restart recovery remains correct;
- persistent schema versions are recognized;
- supported forward migrations work;
- unsupported migrations fail safely;
- failed authoritative writes do not leave partially accepted state;
- supported concurrent access remains deterministic;
- known SQLite ResourceWarning leaks are eliminated;
- all v0.2 regression tests remain green.

Exact filenames may be introduced during implementation. The behaviors above are mandatory completion evidence.

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
syntax                  -> compileall including examples
packaging               -> isolated wheel build
installation            -> wheel install outside source checkout
public interface smoke  -> k-supervisor version + import ksupervisor outside checkout
compatibility           -> v0.2 public package/CLI/config/entry-point regression
```

## Current Authoritative Runtime Baseline

Until Phase 1 produces a new validated implementation checkpoint:

```text
Core Validation run: 34793901147
Implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: PASS
wheel build/install: PASS
public interface smoke: PASS
```

## CI Rule

`Core Validation` remains the authoritative automated regression workflow. No runtime implementation phase may claim completion without a successful full suite on its committed implementation baseline.
