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
v0.3 Phase 0-8: COMPLETE
Current approved implementation phase: NONE
Phase 9: NOT DEFINED
Phase 17: NOT DEFINED
```

## Current Continuation State

ROADMAP v0.3 is complete. `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` is the final v0.3 checkpoint. No successor implementation phase is currently approved.

## Current Runtime Baseline

```text
Implementation commit: f0c9bc30a5562c83803a861aafe6f669a2ae4730
Implementation tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Validated main SHA: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Protected PR Core Validation: 35134961231 — PASS
Merged-main Core Validation: 35135133947 — PASS
Python workflow: 3.13
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Exact-tree local cumulative verification before merge: `163 passed`, branch-aware coverage `85.82%` on Python 3.12.3. GitHub Actions Python 3.13 is authoritative and passed on PR and merged `main`. Documentation-only closure commits do not replace this runtime baseline.

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
