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
v0.3 Phase 2 - Durable Control State: COMPLETE
Current approved phase: v0.3 Phase 3 - Centralized Side-Effect Enforcement
v0.3 Phase 3: ACTIVE
v0.3 Phase 3 runtime implementation at handoff: NOT STARTED
v0.3 Phase 4-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Session Handoff

```text
Handoff prepared: 2026-09-14
Planned continuation: 2026-09-16 09:00 Europe/Kyiv
Startup document: docs/PROJECT_HANDOFF_2026_09_16.md
```

The work pause is for the owner-requested transition to a new chat. It does not change Phase 3 authorization and does not create a new runtime baseline.

## Current Runtime Baseline

```text
Core Validation run: 34808287772
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Documentation-only closure/handoff commits after this implementation SHA do not replace the validated runtime baseline.

## Implemented Platform Baseline

The completed v0.2 platform includes Project lifecycle/control plane, machine contracts, persistence/registry, Human Intervention and email notifications, dynamic Agent/Capability routing, Supervisor orchestration, Project Factory, Workflow Engine, Agent Runtime, Scheduler, tools/providers/provisioning boundaries, policy/approval, Agent Factory, Release Manager, reference Research-Critic composition, observability/reliability, packaging, CLI/config and extension discovery.

ROADMAP v0.3 Phase 1 additionally hardened persistence with explicit SQLite lifecycle ownership, transaction/rollback behavior, schema version 2 with tested v1 -> v2 migration, supported local concurrent writers and a permanent `ResourceWarning` CI gate.

ROADMAP v0.3 Phase 2 additionally delivered:

- persistence-backed runtime/command idempotency on the standard AgentRuntimeDispatcher path;
- project-scoped restart-safe successful-result replay;
- restart-safe notification duplicate suppression from durable delivery history;
- approval expiry and revocation with policy enforcement and durable audit;
- richer Project recovery aggregation for Human Intervention, notifications, approvals, runtime idempotency, policy/audit/routing/release-validation state;
- atomic state+audit persistence for core Project, Human Intervention and Approval control mutations;
- verified interrupted Task/WorkflowRun + owner-wait reconstruction and resume after restart.

SQLite physical schema remains version `2`; Phase 2 uses the generic versioned resources/events storage layout.

## Active Phase 3

`v0.3 Phase 3 - Centralized Side-Effect Enforcement` targets:

- one standard Tool Gateway / side-effect execution gateway;
- normalized side-effect invocation/result contracts;
- policy, tool-operation and protected-reference checks before external invocation;
- correlation and idempotency propagation;
- durable normalized side-effect attempt/outcome audit;
- deterministic no-invocation behavior for DENY and REQUIRE_APPROVAL;
- replaceable concrete tool/provider adapters.

Phase 3 is authorized but its runtime implementation was intentionally left unstarted at the 2026-09-14 handoff. The new chat must first follow `docs/PROJECT_HANDOFF_2026_09_16.md` and verify `main` against the frozen Phase 2 implementation baseline.

Phase 3 completion requires its gateway enforcement tests plus the full cumulative Core Validation suite on the committed implementation baseline.

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

- `docs/PROJECT_HANDOFF_2026_09_16.md`;
- `docs/PROJECT_STATE.md`;
- `docs/ROADMAP.md`;
- `docs/TEST_MATRIX.md`;
- `docs/HARDENING_BASELINE_V0_3.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`;
- `docs/PERSISTENCE.md`;
- `docs/AGENT_RUNTIME.md`;
- `docs/POLICY_AND_PERMISSIONS.md`;
- `docs/CHAT_HANDOFF.md`.

The completed v0.2 roadmap remains archived in `docs/ROADMAP_V0_2_ARCHIVE.md`.