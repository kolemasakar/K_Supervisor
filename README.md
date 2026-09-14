# K_Supervisor
Система автоматизованого життєвого циклу AI-проєктів поверх модульної мультиагентної платформи.

Status: PRE-ALPHA
Package version: 0.1.0
Repository: `kolemasakar/K_Supervisor`

## Purpose

K_Supervisor combines an AI Project Lifecycle Supervisor with a modular multi-agent platform. It manages approved projects, orchestration, workflows, controlled execution, parallel scheduling, integrations, owner intervention, notifications, policy enforcement, reusable agent creation, release preparation, owner-controlled publication handoff, observability/reliability, packaging and external extension discovery.

K_Supervisor is separate from K-Research & Critic, which remains reference-only.

## Roadmap Status

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0 - Baseline Freeze & Hardening Contract: COMPLETE
v0.3 Phase 1 - Persistence & Resource Hygiene: COMPLETE
Current approved phase: v0.3 Phase 2 - Durable Control State
v0.3 Phase 2: ACTIVE
v0.3 Phase 3-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Runtime Baseline

```text
Core Validation run: 34804141156
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Python: 3.13.15
pytest: 95 passed
branch-aware coverage: 85.66%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

## Implemented Platform Baseline

The completed v0.2 platform includes Project lifecycle/control plane, machine contracts, persistence/registry, Human Intervention and email notifications, dynamic Agent/Capability routing, Supervisor orchestration, Project Factory, Workflow Engine, Agent Runtime, Scheduler, tools/providers/provisioning boundaries, policy/approval, Agent Factory, Release Manager, reference Research-Critic composition, observability/reliability, packaging, CLI/config and extension discovery.

ROADMAP v0.3 Phase 1 additionally hardened persistence with:

- explicit SQLite connection ownership and context-manager support;
- idempotent initialize/close;
- explicit transaction commit/rollback behavior;
- SQLite schema version 2;
- tested v1 -> v2 migration with data preservation;
- fail-closed handling of unsupported schema versions;
- WAL/busy-timeout support and concurrent-writer tests;
- CI enforcement that treats `ResourceWarning` as an error;
- zero known SQLite ResourceWarning leaks;
- preserved restart/recovery and public compatibility.

## Active Phase 2

`v0.3 Phase 2 - Durable Control State` targets:

- durable runtime/command idempotency;
- durable notification/execution deduplication state for standard platform paths;
- approval expiry and revocation;
- richer authoritative recovery reconstruction;
- stronger atomicity between required control state and audit records;
- restart-safe active workflow/project control state.

Phase 2 completion requires phase-specific recovery/replay/approval/atomicity tests plus the full permanent Core Validation suite on the committed implementation baseline.

## Public Baseline

```text
Distribution: k-supervisor==0.1.0
Python facade: ksupervisor
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
- `docs/HARDENING_BASELINE_V0_3.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md`;
- `docs/PERSISTENCE.md`;
- `docs/TEST_MATRIX.md`;
- `docs/CHAT_HANDOFF.md`.

The completed v0.2 roadmap remains archived in `docs/ROADMAP_V0_2_ARCHIVE.md`.
