# TEST_MATRIX
Матриця regression-перевірок K_Supervisor для завершеного ROADMAP v0.2 та активного ROADMAP v0.3.

Version: 1.5
Status: ACTIVE
Roadmap baseline: v0.2 COMPLETE + v0.3 ACTIVE
Current phase: v0.3 Phase 2

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
| 2 | durable idempotency, command replay, approval lifecycle, restart recovery, aggregate reconstruction | ACTIVE |
| 3 | centralized Tool Gateway policy paths, protected references, repeated invocation handling, normalized audit | PLANNED |
| 4 | unresponsive worker, cancellation escalation, timeout, crash isolation, bounded termination | PLANNED |
| 5 | API contracts, access control, invalid transitions, idempotent mutations, restart continuity | PLANNED |
| 6 | correlation, persisted telemetry, timeline reconstruction, exporter contracts, health/readiness, redaction | PLANNED |
| 7 | extension compatibility/trust state, disabled extension behavior, entry-point regression, CI governance | PLANNED |
| 8 | deployment, complete lifecycle qualification, failure injection, backup/restore, migration, parallel-project isolation | PLANNED |

## Phase 1 Evidence

Authoritative implementation baseline:

```text
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Core Validation run: 34804141156
Python: 3.13.15
pytest: 95 passed
branch-aware coverage: 85.66%
coverage gate: PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public interface smoke: PASS
```

Phase 1 hardening tests:

```text
tests/test_v03_phase1_persistence_hardening.py
```

Verified behaviors:

- context-manager connection ownership;
- idempotent initialize/close;
- deterministic v1 -> v2 migration with data preservation;
- fail-closed unsupported schema handling;
- transaction rollback;
- independent concurrent SQLite writers under the supported local boundary;
- zero SQLite ResourceWarning leakage;
- predecessor restart/recovery compatibility.

Completion record: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md`.

## Phase 2 Required Verification

Phase 2 implementation must prove:

- idempotency state survives process/store restart;
- replay of the same supported command returns/reuses the authoritative outcome rather than creating an unintended duplicate operation;
- notification/execution deduplication state is durable where required by standard platform paths;
- approval expiry is deterministic and time-aware;
- approval revocation is persisted, enforced and audited;
- interrupted workflow/project control state can be reconstructed after restart;
- richer recovery aggregation uses authoritative persistence rather than hidden process memory;
- required control-state/audit writes respect the defined atomicity boundary;
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
Core Validation run: 34804141156
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Python: 3.13.15
pytest: 95 passed
branch-aware coverage: 85.66%
coverage gate: PASS
ResourceWarning gate: PASS
wheel build/install: PASS
public interface smoke: PASS
```

## CI Rule

`Core Validation` remains the authoritative automated regression workflow. No runtime implementation phase may claim completion without a successful full suite on its committed implementation baseline.
