# K_Supervisor
Система автоматизованого життєвого циклу AI-проєктів поверх модульної мультиагентної платформи.

Status: PRE-ALPHA
Package version: 0.1.0
Repository: `kolemasakar/K_Supervisor`

## Purpose

K_Supervisor combines an AI Project Lifecycle Supervisor with a modular multi-agent platform. It manages approved projects, orchestration, workflows, controlled execution, parallel scheduling, integrations, owner intervention, notifications, policy enforcement, reusable agent creation, release preparation, owner-controlled publication handoff, observability/reliability, packaging, external extension discovery and a controlled lifecycle Service/API boundary.

K_Supervisor is separate from K-Research & Critic, which remains reference-only.

## Roadmap Status

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: ACTIVE — IMPLEMENTED / LIVE SMOKE PENDING
v0.4 Phase 2-7: PLANNED
Runtime implementation phase: v0.4 Phase 1
v0.3 Phase 9: NOT DEFINED
```

## Current Continuation State

ROADMAP v0.4 is approved and Phase 0 is complete. Phase 1 — Production Model Provider & AI Execution — is activated and deterministically implemented through PR #14. `docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md` records the current implementation baseline. Phase 1 remains incomplete until the required owner-controlled live OpenAI Responses smoke succeeds; Phase 2 is inactive.

## Current Runtime Baseline

```text
Implementation PR: #14
Implementation head: 0d6a3ed863c687ec9461135a306180014c248312
Implementation tree: 7fabf5220d4370124bb245445c84f9ed77eb2041
Validated main SHA: 8f748e993737cebe45a6e8ebaac74d8c0e10d1b7
Protected PR Core Validation: 35175344558 — PASS
Merged-main Core Validation: 35175392964 — PASS
Python workflow: 3.13
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
Live OpenAI Responses smoke: PENDING
```

Local Phase 1 candidate verification passed `187 tests` with branch-aware coverage `85.02%` on Python 3.12.3 (non-authoritative). GitHub Actions Python 3.13 is authoritative and passed on both PR #14 and merged `main`.

## Completed v0.3 Hardening

- Phase 1: explicit SQLite lifecycle ownership, schema migration, rollback/concurrency/resource-hygiene gates.
- Phase 2: durable runtime idempotency, notification deduplication, approval lifecycle, richer restart recovery and atomic control-state writes.
- Phase 3: centralized SideEffectGateway with policy/permission/protected-reference enforcement, idempotency and durable attempt/outcome audit.
- Phase 4: process-isolated runtime option with parent-owned timeout/cancellation escalation, worker-crash containment and bounded cleanup.
- Phase 5: versioned `/api/v1` Project read/lifecycle service boundary with injected authentication, independent scopes, normalized errors and durable restart-safe mutation idempotency.
- Phase 6: persisted operational telemetry, correlation, redaction, deterministic timeline, exporter projections and service health/readiness foundations.
- Phase 7: fail-closed installed-extension trust/provenance/compatibility governance plus protected-main required-CI governance.
- Phase 8: operational backup/restore/upgrade qualification, deployment/readiness evidence, lifecycle/recovery concurrency qualification, runbook and manual owner-gated package publication workflow.

Phase 5 does not expose ProjectSpec administration, workflow/runtime execution, release/publication mutation, Tool/Provider side effects or secret contents. Those authoritative boundaries remain separate.

## Public Baseline

```text
Distribution: k-supervisor==0.1.0
Python facade: ksupervisor
Service facade: ksupervisor.service
Service API: /api/v1
CLI: k-supervisor
Config version: 1
Extension groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

## Canonical Documents

Start with:

- `docs/PROJECT_STATE.md`;
- `docs/ROADMAP.md`;
- `docs/TEST_MATRIX.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_8_COMPLETE.md`;
- `docs/OPERATIONS_RUNBOOK.md`;
- `docs/OBSERVABILITY_AND_RELIABILITY.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_5_COMPLETE.md`;
- `docs/PHASE5_PREIMPLEMENTATION_AUDIT.md`;
- `docs/SERVICE_API.md`;
- `docs/HARDENING_BASELINE_V0_3.md`;
- `docs/PERSISTENCE.md`;
- `docs/COMPATIBILITY_POLICY.md`;
- `docs/CHAT_HANDOFF.md`.

The completed v0.2 roadmap remains archived in `docs/ROADMAP_V0_2_ARCHIVE.md`.
