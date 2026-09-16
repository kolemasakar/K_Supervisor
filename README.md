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
ROADMAP v0.3: ACTIVE
v0.3 Phase 0 - Baseline Freeze & Hardening Contract: COMPLETE
v0.3 Phase 1 - Persistence & Resource Hygiene: COMPLETE
v0.3 Phase 2 - Durable Control State: COMPLETE
v0.3 Phase 3 - Centralized Side-Effect Enforcement: COMPLETE
v0.3 Phase 4 - Runtime Isolation & Cancellation: COMPLETE
v0.3 Phase 5 - Service/API Boundary: COMPLETE
v0.3 Phase 6-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Continuation State

Phase 5 is complete. `docs/PROJECT_HANDOFF_2026_09_16_PHASE_6.md` is the current new-chat transition handoff. Earlier Phase 3/5 handoffs are historical startup checkpoints. Phase 6 remains PLANNED / NOT STARTED and is not activated by preparing the handoff.

## Current Runtime Baseline

```text
Core Validation run: 35103131762
Implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Python workflow: 3.13
pytest: 129 passed
branch-aware coverage: 85.34%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples/service_api: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Documentation-only closure commits after this implementation SHA do not replace the validated runtime baseline.

## Completed v0.3 Hardening

- Phase 1: explicit SQLite lifecycle ownership, schema migration, rollback/concurrency/resource-hygiene gates.
- Phase 2: durable runtime idempotency, notification deduplication, approval lifecycle, richer restart recovery and atomic control-state writes.
- Phase 3: centralized SideEffectGateway with policy/permission/protected-reference enforcement, idempotency and durable attempt/outcome audit.
- Phase 4: process-isolated runtime option with parent-owned timeout/cancellation escalation, worker-crash containment and bounded cleanup.
- Phase 5: versioned `/api/v1` Project read/lifecycle service boundary with injected authentication, independent scopes, normalized errors and durable restart-safe mutation idempotency.

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
- `docs/PROJECT_HANDOFF_2026_09_16_PHASE_6.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_5_COMPLETE.md`;
- `docs/PHASE5_PREIMPLEMENTATION_AUDIT.md`;
- `docs/SERVICE_API.md`;
- `docs/HARDENING_BASELINE_V0_3.md`;
- `docs/PERSISTENCE.md`;
- `docs/COMPATIBILITY_POLICY.md`;
- `docs/CHAT_HANDOFF.md`.

The completed v0.2 roadmap remains archived in `docs/ROADMAP_V0_2_ARCHIVE.md`.
