# TEST_MATRIX
Матриця regression-перевірок K_Supervisor для завершеного ROADMAP v0.2 та активного ROADMAP v0.3.

Version: 1.3
Status: ACTIVE
Roadmap baseline: v0.2 COMPLETE + v0.3 ACTIVE
Current phase: v0.3 Phase 0

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

v0.2 Phase 0 remains architecture/documentation acceptance covered by later contract and integration tests.

## ROADMAP v0.3 Verification Plan

| v0.3 Phase | Required verification |
| --- | --- |
| 0 | predecessor baseline traceability, compatibility review, full v0.2 regression, documentation consistency |
| 1 | storage lifecycle, close/reopen, migration, rollback, concurrency, resource warnings |
| 2 | durable idempotency, command replay, approval expiry/revocation, restart recovery, aggregate reconstruction |
| 3 | centralized Tool Gateway policy paths, protected references, duplicate invocation handling, normalized audit |
| 4 | hung worker, cancellation escalation, timeout, crash isolation, bounded termination, Supervisor responsiveness |
| 5 | API contracts, access control, invalid transitions, idempotent mutation replay, restart continuity, control-plane integrity |
| 6 | correlation/tracing, persisted telemetry, timeline reconstruction, exporter contracts, health/readiness, data redaction |
| 7 | extension trust/compatibility state, disabled extension behavior, invalid registration, entry-point regression, CI governance |
| 8 | clean deployment, complete project lifecycle qualification, failure injection, backup/restore, migration, parallel project isolation |

Exact v0.3 test filenames may be introduced during implementation. The behaviors above are mandatory phase evidence.

## Permanent Quality Gates

```text
structured audit        -> project, intervention, notification, routing, release and side-effect records
integration             -> Supervisor + registries + runtime + persistence + policy + Tool Gateway boundaries
failure injection       -> deterministic transport/runtime/storage/provider failures
recovery                -> authoritative state reconstruction after supported restart/reopen boundaries
referential integrity   -> ReliabilityValidator or an explicitly approved successor boundary
metrics/telemetry       -> project/agent metrics plus v0.3 operational telemetry where implemented
performance             -> existing v0.2 baseline remains unless explicitly superseded
coverage                -> branch-aware total coverage >= 80%
syntax                  -> compileall including examples
packaging               -> isolated wheel build
installation            -> wheel install outside source checkout
public interface smoke  -> k-supervisor version + import ksupervisor outside checkout
compatibility           -> v0.2 public package/CLI/config/entry-point regression
```

## Current Authoritative Runtime Baseline

Until a v0.3 implementation checkpoint explicitly replaces it:

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

## v0.3 Phase 0 Gate

v0.3 Phase 0 is documentation/baseline hardening work and does not itself change runtime behavior.

Phase 0 completion requires:

- archived and traceable v0.2 roadmap/baseline;
- synchronized canonical status documents;
- explicit technical-debt mapping to v0.3 phases;
- compatibility and migration rules identified;
- full v0.2 Core Validation still PASS on the runtime predecessor baseline;
- no regression to public package, CLI, config or extension surfaces.

## CI Rule

`Core Validation` remains the authoritative automated regression workflow until an explicitly approved successor workflow replaces or extends it.

Any v0.3 runtime phase must not claim completion without a successful full cumulative suite on the committed implementation baseline.

The ROADMAP v0.2 quality baseline remains the minimum compatibility/regression floor for ROADMAP v0.3 unless an explicit approved change states otherwise.

## Completion Evidence Rule

For every completed v0.3 runtime phase, canonical evidence records at minimum:

- committed implementation SHA;
- authoritative CI/run identifier;
- test count/result;
- coverage result;
- phase-specific verification evidence;
- synchronized ROADMAP, PROJECT_STATE, TEST_MATRIX, DOCS_INDEX and checkpoint status.
