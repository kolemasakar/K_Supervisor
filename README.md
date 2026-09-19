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
v0.4 Phase 1: COMPLETE
v0.4 Phase 2: COMPLETE
v0.4 Phase 3: COMPLETE
v0.4 Phase 4: PLANNED — AUDIT COMPLETE / ACTIVATION PENDING
v0.4 Phase 5-7: PLANNED / INACTIVE
Runtime implementation phase: NONE
v0.3 Phase 9: NOT DEFINED
```

## Current Continuation State

ROADMAP v0.4 is approved; Phases 0-3 are complete. Phase 4 pre-implementation audit is complete and defines the governed GitHub repository/VCS boundary, but Phase 4 remains inactive pending explicit owner approval and a separate protected activation checkpoint. No Phase 4 runtime code is authorized. The zero-cost development policy remains permanent.

## Current Runtime Baseline

```text
Phase 3 implementation PR: #29
Final PR head: c73e4c5f24f958ebb1473d4c8d23f28244c9f799
Final PR tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Final exact-head Core Validation: 35453258878 — PASS
Merged main: a1791b607496edfaf84593d753f7d1d7662eede1
Merged-main Core Validation: 35453297160 — PASS
Full regression: 229 passed
branch-aware coverage: 82.06%
installed-wheel Phase 3 service/CLI smoke: PASS
Phase 3 completion: PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_COMPLETE.md

Previous Phase 2 implementation PR: #24
Validated code/test head: f9f7284c407734fc2a3286f755c6827229142514
Validated code/test tree: abf48bbbfc2fe5e69c08fb7f6c8f3e9faee1b7ea
Code/test Core Validation: 35443690831 — PASS
Final PR head: 067828dfb6618ab412dfdfc64045cff9e8ea9cef
Final exact-head Core Validation: 35443735846 — PASS
Merged main: 9b532e4dd7c3aaaaaab2beaea97a3b017b7fff56
Merged-main Core Validation: 35443778180 — PASS
Full regression: 214 passed
branch-aware coverage: 83.21%
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
Phase 2 completion: PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_COMPLETE.md
```

## Development Resource Policy

All project development, testing, CI, validation, smoke testing and qualification must use resources available at no additional project-attributable cost. Paid providers may remain supported production/operator options, but paid-only access cannot be required for development or phase completion.

Canonical policy: `docs/DEVELOPMENT_RESOURCE_POLICY.md`.

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

- `docs/V0_4_PHASE4_PREIMPLEMENTATION_AUDIT.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_COMPLETE.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_IMPLEMENTED.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_ACTIVATED.md`;
- `docs/PROJECT_HANDOFF_2026_09_19_V0_4_PHASE3_ACTIVATION.md`;
- `docs/PROJECT_STATE.md`;
- `docs/DEVELOPMENT_RESOURCE_POLICY.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_FREE_RESOURCE_AMENDMENT.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_COMPLETE.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_COMPLETE.md`;
- `docs/V0_4_PHASE3_PREIMPLEMENTATION_AUDIT.md`;
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
