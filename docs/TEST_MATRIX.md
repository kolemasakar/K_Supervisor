# TEST_MATRIX
Матриця regression-перевірок K_Supervisor за roadmap-фазами та reliability-категоріями.

Version: 1.1
Status: ACTIVE
Updated through: Phase 16

## Matrix

| Phase | Primary verification | Test family |
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
| 11 | policy deny/allow/approval and durable audit | `test_phase11_*` |
| 12 | scaffolding, reference agents, provider interchangeability | `test_phase12_*` |
| 13 | release readiness, publication gate, release recovery | `test_phase13_*` |
| 14 | profile gate, research-review loop, bounded revision, legacy isolation | `test_phase14_*` |
| 15 | structured audit, routing records, metrics, failure injection, recovery, performance | `test_phase15_*` |
| 16 | public config/CLI, extension discovery/activation, examples, package build/install | `test_phase16_*` + CI package smoke |

Phase 0 is documentation/architecture acceptance and is covered by subsequent contract and integration tests rather than a dedicated runtime test family.

## Reliability and Quality Gates

```text
structured audit        -> project, intervention, notification, routing, release tests
integration             -> Supervisor + registries + runtime + SQLite boundaries
failure injection       -> deterministic notification transport failure
recovery                -> SQLite close/reopen with durable records
referential integrity   -> ReliabilityValidator
metrics                 -> project and per-agent derived metrics
performance             -> 10,000 provider selections < 3 seconds
coverage                -> branch-aware total coverage >= 80%
syntax                  -> compileall, including Phase 16 examples
packaging               -> isolated wheel build
installation            -> wheel install outside source checkout
public interface smoke  -> k-supervisor version + import ksupervisor outside checkout
```

## Phase 16 Extension Matrix

```text
agent extension group            -> discovery + activation test
capability extension group       -> discovery + activation test
project-template extension group -> discovery + activation + example registration test
adapter extension group          -> discovery + activation test
configuration                    -> JSON/TOML load tests
CLI                              -> version + validate-config tests
example workflow                 -> WorkflowDefinition validation test
```

## Current Baseline

```text
Core Validation run: 34793901147
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: PASS
wheel build/install: PASS
public interface smoke: PASS
```

## CI Rule

`Core Validation` is the authoritative automated regression workflow. A phase completion checkpoint must not claim PASS unless the full suite completes successfully on the committed implementation baseline.

Quality thresholds are baselines, not permanent ceilings. They must not be silently weakened without updating this document and the relevant checkpoint/compatibility documentation.
