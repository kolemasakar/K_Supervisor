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
Current approved phase: v0.3 Phase 1 - Persistence & Resource Hygiene
v0.3 Phase 1: ACTIVE
v0.3 Phase 2-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

Phase 0 froze the predecessor baseline, technical-debt assignment, compatibility/migration rules and cumulative validation gates. Phase 1 is authorized to harden persistence/resource ownership.

## Current Runtime Baseline

Until Phase 1 produces a new validated implementation checkpoint:

```text
Core Validation run: 34793901147
Implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: >= 80% PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
live owner mailbox delivery: PASS
```

## Implemented v0.2 Platform Baseline

- Project lifecycle/control plane and ProjectSpec contracts;
- machine contracts and JSON schemas;
- SQLite persistence and Project Registry;
- Human Intervention and email Notification Broker;
- Agent/Capability registries and capability routing;
- Supervisor orchestration kernel;
- Project Factory and repository bootstrap;
- Workflow Engine;
- Agent Runtime;
- Project Scheduler and parallel project controls;
- Tool/Provider/Provisioning interfaces and protected access references;
- policy/permissions/approval boundaries;
- Agent Factory and reference agents;
- Release Manager and owner publication handoff;
- reference Research-Critic composition;
- observability/reliability/CI baseline;
- installable wheel, public `ksupervisor` facade, CLI/config and extension discovery.

## Active Phase 1

Phase 1 targets:

- explicit storage connection lifecycle and ownership;
- transaction-boundary hardening;
- persistent schema version/migration mechanism;
- storage abstractions independent of SQLite physical layout;
- cleanup of known SQLite ResourceWarning leaks;
- deterministic reopen/restart recovery;
- documented storage replacement boundary.

Phase 1 completion requires phase-specific tests plus the full permanent Core Validation suite on the committed implementation baseline.

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
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md`;
- `docs/TEST_MATRIX.md`;
- `docs/CHAT_HANDOFF.md`.

The completed v0.2 roadmap remains archived in `docs/ROADMAP_V0_2_ARCHIVE.md`.
