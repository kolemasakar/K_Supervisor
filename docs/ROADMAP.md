# ROADMAP
K_Supervisor active development roadmap.

Version: 0.3
Status: ACTIVE
Approved: 2026-09-14
Roadmap start: 2026-09-14
Predecessor: ROADMAP v0.2 COMPLETE
Current phase: v0.3 Phase 8 IN PROGRESS
Phase 6 implementation completed: 2026-09-16
Phase 7 implementation validated: 2026-09-16
Phase 7 completed: 2026-09-16
Phase 8 activation: YES

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
| v0.3 Phase 5 | Service/API Boundary | COMPLETE |
| v0.3 Phase 6 | Production Observability | COMPLETE |
| v0.3 Phase 7 | Extension Trust & Platform Governance | COMPLETE |
| v0.3 Phase 8 | Operational Readiness & Autonomous Lifecycle Qualification | IN PROGRESS |

Phase 0-7 are COMPLETE. Phase 8 is IN PROGRESS following `PHASE8_PREIMPLEMENTATION_AUDIT.md`; implementation is limited to the approved operational-readiness and lifecycle-qualification scope.

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

Successor Phases 4-7 are complete. Phase 8 is now IN PROGRESS under `PHASE8_PREIMPLEMENTATION_AUDIT.md`.

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

Phase 4 remains complete. Phases 5-7 are also complete; `PROJECT_HANDOFF_2026_09_16_PHASE_7.md` is preserved as historical Phase 7 start context. Phase 8 is now IN PROGRESS under its pre-implementation audit.

## Completed Phase 5 - Service/API Boundary

Goal: introduce a controlled versioned Service/API boundary for Project lifecycle operations without bypassing the existing control plane.

Validated baseline:

```text
Implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Core Validation run: 35103131762
Python workflow: 3.13
pytest: 129 passed
branch-aware coverage: 85.34%
Core Validation: PASS
```

Delivered `ServiceApiV1`, a thin WSGI adapter, `/api/v1` Project read/lifecycle routes, injected authentication, independent read/write scopes, normalized errors and durable restart-safe `ServiceMutationRecord` idempotency. Mutations delegate to existing `ProjectRegistry` transition methods, and transition/audit/service-receipt persistence is atomic on the supported SQLite path.

Required Phase 5 tests cover API contracts, access control, invalid transitions, idempotent mutations, restart continuity and persistence-failure rollback. Full predecessor regressions remain green.

Evidence:

- `PHASE5_PREIMPLEMENTATION_AUDIT.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_5_COMPLETE.md`;
- `SERVICE_API.md`;
- `PLATFORM_INTERFACES.md`;
- `PERSISTENCE.md`;
- `TEST_MATRIX.md`.

Phase 5 does not claim production hosting/TLS, external identity-provider integration, health/readiness/SLO telemetry, distributed tracing, extension trust governance or distributed persistence. Those remain outside Phase 5.

Current roadmap boundary: Phase 7 is `COMPLETE`; v0.3 Phase 8 is `IN PROGRESS`.

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

## Completed Phase 6 - Production Observability

Goal: establish persisted operational telemetry, correlation, exporter boundaries, redaction and service health/readiness foundations without changing Project lifecycle semantics.

Validated baseline:

```text
Implementation SHA: 8f3d9a85abd68e1ab83dbf7ca87f3dadfe549883
Core Validation run: 35110298258
Python workflow: 3.13
pytest: 136 passed
branch-aware coverage: 85.52%
Core Validation: PASS
```

Delivered durable `TelemetryRecord` events, deterministic telemetry timeline reconstruction, recursive pre-persistence/export redaction, optional Runtime and Service/API instrumentation, SDK-neutral Prometheus/OpenTelemetry projection contracts, and component-based service health/readiness evaluation. Telemetry is included in `ProjectRecoverySnapshot`; SQLite physical schema remains `2`.

Evidence:

- `PHASE6_PREIMPLEMENTATION_AUDIT.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_6_COMPLETE.md`;
- `OBSERVABILITY_AND_RELIABILITY.md`;
- `PERSISTENCE.md`;
- `TEST_MATRIX.md`.

Phase 6 does not add third-party telemetry SDK dependencies, remote collectors, production hosting, deployment qualification or extension trust governance.

Current roadmap boundary: Phase 7 is `COMPLETE`; v0.3 Phase 8 is `IN PROGRESS`.

## Completed Phase 7 - Extension Trust & Platform Governance

Pre-implementation audit: `PHASE7_PREIMPLEMENTATION_AUDIT.md`.

Validated implementation evidence:

```text
Implementation SHA: 64c84ad6e6633c047416aca270d979e4ba5d36a0
Core Validation run: 35121930140
Core Validation: PASS
```

Implemented: fail-closed installed-extension authorization before import, exact identity/provenance/version compatibility binding, durable trust/enable/signature state, identity-change invalidation, PR-triggered Core Validation, and current GitHub Actions runtimes.

Repository governance completion evidence: active ruleset `main-core-validation` (id `23556478`) targets `~DEFAULT_BRANCH`, requires pull requests, requires GitHub Actions status check `Core Validation`, blocks deletion and non-fast-forward pushes, has no bypass actors, and uses non-strict required-status policy. Phase 7 exit criteria are satisfied. Completion record: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_7_COMPLETE.md`.

## OpenAI Custom GPT -> Plugin Compatibility Amendment

Current validated `main` additionally includes a backward-compatible ChatGPT release-target correction:

```text
Implementation SHA: 97f454a11d1b5e5afb1334fb06d54d5abffdf004
Core Validation run: 35124348659
Python: 3.13.15
pytest: 149 passed
branch-aware coverage: 85.63%
Core Validation: PASS
```

New ChatGPT-facing projects prefer `CHATGPT_PLUGIN`; `GPT_STORE` remains a legacy compatibility/migration target. Custom Actions are not treated as automatically migrated, selected-model coupling is not introduced, and external sharing/publication remains owner/workspace controlled. Evidence: `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md`.

This amendment remains part of the Phase 8 baseline; Phase 8 is now activated separately by `PHASE8_PREIMPLEMENTATION_AUDIT.md`.

## Phase 8 - Operational Readiness & Autonomous Lifecycle Qualification — IN PROGRESS

Pre-implementation audit: `PHASE8_PREIMPLEMENTATION_AUDIT.md`.

Approved implementation scope is limited to owner-controlled package-index workflow; deployment/runbook/backup/restore/upgrade qualification; operational release-readiness evidence; full approved ProjectSpec -> `RELEASE_READY` qualification; and concurrent-project restart/recovery/owner-intervention qualification.

Phase 8 does not authorize automatic external publication, distributed execution/federation, non-email owner transports, multi-tenant SaaS scope or universal arbitrary-Python sandboxing.
