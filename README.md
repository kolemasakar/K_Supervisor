# K_Supervisor
Система автоматизованого життєвого циклу AI-проєктів поверх модульної мультиагентної платформи.

Status: PRE-ALPHA
Concept baseline: v0.2
Roadmap: v0.3 ACTIVE
Current phase: v0.3 Phase 0
Package version: 0.1.0
Repository: `kolemasakar/K_Supervisor`

## Purpose

K_Supervisor combines an AI Project Lifecycle Supervisor with a modular multi-agent platform. It manages approved projects, orchestration, workflows, controlled execution, parallel scheduling, integrations, owner intervention, notifications, policy enforcement, reusable agent creation, release preparation, owner-controlled publication handoff, reference multi-agent compositions, observability/reliability, packaging and external extension discovery.

The long-term objective is for an owner to approve a structured ProjectSpec and for the platform to bootstrap, coordinate, implement, validate and prepare that project for release while requesting owner intervention only at explicit boundaries.

K_Supervisor is a separate project. K-Research & Critic v1.0.0 remains a reference product only.

## Canonical Status Documents

- `docs/PROJECT_STATE.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md`
- `docs/TEST_MATRIX.md`
- `docs/ROADMAP_IMPLEMENTATION_AUDIT.md`
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md`
- `docs/ROADMAP_V0_2_ARCHIVE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/DOCS_INDEX.md`

## Completed v0.2 Runtime Baseline

```text
v0.2 Phase 0   Foundation / Architecture                    COMPLETE
v0.2 Phase 1   Machine Contracts / Core Models             COMPLETE
v0.2 Phase 2   Persistence / Project Registry              COMPLETE
v0.2 Phase 3   Human Intervention / Email Notification     COMPLETE
v0.2 Phase 4   Agent / Capability Registries               COMPLETE
v0.2 Phase 5   Supervisor Orchestration Kernel             COMPLETE
v0.2 Phase 6   Project Factory / Repository Bootstrap      COMPLETE
v0.2 Phase 7   Workflow Engine / Multi-Agent Composition   COMPLETE
v0.2 Phase 8   Agent Runtime / Execution Control           COMPLETE
v0.2 Phase 9   Project Scheduler / Parallel Execution      COMPLETE
v0.2 Phase 10  Tools / Providers / Provisioning / Secrets  COMPLETE
v0.2 Phase 11  Policy / Permissions / Risk / Approval      COMPLETE
v0.2 Phase 12  Reference Agents / Agent Factory            COMPLETE
v0.2 Phase 13  Release Manager / Publication Readiness     COMPLETE
v0.2 Phase 14  Reference Research-Critic Workflow          COMPLETE
v0.2 Phase 15  Observability / Reliability / CI            COMPLETE
v0.2 Phase 16  Interfaces / Packaging / Extensibility      COMPLETE
```

Final validated predecessor runtime baseline:

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

Documentation synchronization after that implementation SHA does not itself replace the runtime baseline.

## Active ROADMAP v0.3

ROADMAP v0.3 — Production Hardening & Service Boundary is approved and active.

```text
v0.3 Phase 0  Baseline Freeze & Hardening Contract                       ACTIVE
v0.3 Phase 1  Persistence & Resource Hygiene                              PLANNED
v0.3 Phase 2  Durable Control State                                       PLANNED
v0.3 Phase 3  Centralized Side-Effect Enforcement                         PLANNED
v0.3 Phase 4  Runtime Isolation & Cancellation                            PLANNED
v0.3 Phase 5  Service/API Boundary                                        PLANNED
v0.3 Phase 6  Production Observability                                    PLANNED
v0.3 Phase 7  Extension Trust & Platform Governance                       PLANNED
v0.3 Phase 8  Operational Readiness & Autonomous Lifecycle Qualification  PLANNED
```

ROADMAP v0.3 uses revision-local numbering and does not create or imply a Phase 17.

## Public Baseline

The distribution remains `k-supervisor==0.1.0` and exposes the `ksupervisor` Python facade plus the `k-supervisor` CLI.

Standard Python entry points support externally packaged agents, capabilities, project templates and adapters without Supervisor-core edits:

```text
k_supervisor.agents
k_supervisor.capabilities
k_supervisor.project_templates
k_supervisor.adapters
```

These public compatibility surfaces remain governed by `docs/COMPATIBILITY_POLICY.md`.

## Validation Rule

The completed v0.2 Core Validation remains the minimum regression floor for v0.3. A v0.3 runtime phase is not COMPLETE until its phase-specific checks and the cumulative authoritative regression suite pass on the committed implementation baseline.

For continuing work in a new conversation, start with `docs/CHAT_HANDOFF.md` and re-fetch the canonical status documents from `main` before making changes.
