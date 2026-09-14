# PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED
Контрольна точка затвердження нового циклу розвитку K_Supervisor.

Version: 1.0
Status: APPROVED
Roadmap: v0.3
Date: 2026-09-14
Current phase: v0.3 Phase 0

## Decision

ROADMAP v0.3 — Production Hardening & Service Boundary is approved.

The roadmap uses revision-local numbering `v0.3 Phase 0` through `v0.3 Phase 8` and does not create or imply a Phase 17.

## Program Objective

Transition K_Supervisor from the completed PRE-ALPHA functional platform baseline into a hardened autonomous platform foundation capable of reliable long-running managed project execution.

The v0.3 program hardens the existing architecture. It must not replace approved v0.2 control boundaries with parallel control paths.

## Approved Phase Sequence

```text
v0.3 Phase 0  Baseline Freeze & Hardening Contract
v0.3 Phase 1  Persistence & Resource Hygiene
v0.3 Phase 2  Durable Control State
v0.3 Phase 3  Centralized Side-Effect Enforcement
v0.3 Phase 4  Runtime Isolation & Cancellation
v0.3 Phase 5  Service/API Boundary
v0.3 Phase 6  Production Observability
v0.3 Phase 7  Extension Trust & Platform Governance
v0.3 Phase 8  Operational Readiness & Autonomous Lifecycle Qualification
```

## Predecessor Baseline

ROADMAP v0.2 remains COMPLETE.

```text
Validated implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Core Validation run: 34793901147
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: >= 80% PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

The full predecessor roadmap is archived in `docs/ROADMAP_V0_2_ARCHIVE.md`.

## Preserved Architecture Boundaries

- Project != Task.
- Agent != Capability.
- ProjectSpec approval gates material scope.
- workflows remain capability-oriented.
- Supervisor owns orchestration/routing boundaries.
- platform persistence is authoritative; hidden conversational memory is not.
- Human Intervention remains explicit and resumable.
- notification delivery != owner action completion.
- email remains the primary required owner notification transport.
- secrets remain protected references.
- policy/permission checks occur before side effects.
- RELEASE_READY != publication.
- publication remains owner-controlled.
- K-Research & Critic remains reference-only.

## Compatibility Baseline

The existing public package, CLI, config and extension interfaces remain governed by `COMPATIBILITY_POLICY.md`.

The Phase 16 entry-point groups remain stable:

```text
k_supervisor.agents
k_supervisor.capabilities
k_supervisor.project_templates
k_supervisor.adapters
```

## Validation Baseline

The completed v0.2 Core Validation and TEST_MATRIX remain the minimum regression floor. v0.3 tests are cumulative.

A v0.3 phase may be marked COMPLETE only after required validation passes on the committed implementation baseline and canonical documentation/checkpoint records are synchronized.

## Current Authorization

`v0.3 Phase 0` is approved and ACTIVE for documentation/baseline/hardening-contract work.

Runtime hardening implementation begins only under the appropriate active v0.3 phase after its predecessor exit criteria are satisfied.
