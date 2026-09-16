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
v0.3 Phase 3 - Centralized Side-Effect Enforcement: COMPLETE
v0.3 Phase 4 - Runtime Isolation & Cancellation: COMPLETE
v0.3 Phase 5-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Continuation State

Phase 4 is complete. `docs/PROJECT_HANDOFF_2026_09_16.md` remains a historical Phase 3 startup checkpoint. The next roadmap phase, Phase 5, remains PLANNED / NOT STARTED.

## Current Runtime Baseline

```text
Core Validation run: 35092932820
Implementation SHA: 34049f601fc8116aa12ee15023f1dc20bc25901a
Python: 3.13.15
pytest: 117 passed
branch-aware coverage: 85.13%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Documentation-only closure commits after this implementation SHA do not replace the validated runtime baseline.

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

## Completed Phase 3

`v0.3 Phase 3 - Centralized Side-Effect Enforcement` delivered:

- one standard Tool Gateway / side-effect execution gateway;
- normalized side-effect invocation/result contracts;
- policy, tool-operation and protected-reference checks before external invocation;
- correlation and idempotency propagation;
- durable normalized side-effect attempt/outcome audit;
- deterministic no-invocation behavior for DENY and REQUIRE_APPROVAL;
- replaceable concrete tool/provider adapters.

Phase 3 passed its gateway enforcement tests and the full cumulative Core Validation suite on implementation SHA `6868d595b66a6ada91a2e6f2f62866721d0f3560`. Completion evidence is recorded in `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_3_COMPLETE.md`.

Phase 4 is complete on implementation SHA `34049f601fc8116aa12ee15023f1dc20bc25901a`. Completion evidence is recorded in `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_4_COMPLETE.md`.

## Completed Phase 4

`v0.3 Phase 4 - Runtime Isolation & Cancellation` delivered:

- `ProcessRuntimeAdapter` with one isolated worker process per invocation;
- parent-enforced timeout and cancellation with bounded escalation from cooperative signal to terminate/kill;
- contained worker-process crashes and normalized runtime failure semantics;
- child runtime-limit/error normalization across the process boundary;
- bounded worker cleanup with no live worker left on supported completion paths;
- compatibility preservation for `InProcessRuntimeAdapter` and the existing `RuntimeAdapter` contract.

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
- `docs/TEST_MATRIX.md`;
- `docs/HARDENING_BASELINE_V0_3.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_4_COMPLETE.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_3_COMPLETE.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`;
- `docs/PERSISTENCE.md`;
- `docs/AGENT_RUNTIME.md`;
- `docs/POLICY_AND_PERMISSIONS.md`;
- `docs/CHAT_HANDOFF.md`.

The completed v0.2 roadmap remains archived in `docs/ROADMAP_V0_2_ARCHIVE.md`.
