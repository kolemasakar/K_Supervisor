# K_Supervisor
Система автоматизованого життєвого циклу AI-проєктів поверх модульної мультиагентної платформи.

Status: PRE-ALPHA
Concept baseline: v0.2
Roadmap baseline: COMPLETE (Phase 0-16)
Package version: 0.1.0
Repository: `kolemasakar/K_Supervisor`

## Purpose

K_Supervisor combines an AI Project Lifecycle Supervisor with a modular multi-agent platform. It manages approved projects, orchestration, workflows, controlled execution, parallel scheduling, integrations, owner intervention, notifications, policy enforcement, reusable agent creation, release preparation, owner-controlled publication handoff, reference multi-agent compositions, observability/reliability, packaging, and external extension discovery.

K_Supervisor is a separate project. K-Research & Critic v1.0.0 remains a reference product only.

## Core Documents

- `docs/VISION.md`
- `docs/PROJECT_STATE.md`
- `docs/PROJECT_CONTRACT.md`
- `docs/PROJECT_LIFECYCLE.md`
- `docs/PROJECT_CONTROL_PLANE.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENT_CONTRACT.md`
- `docs/CAPABILITY_MODEL.md`
- `docs/MACHINE_CONTRACTS.md`
- `docs/PERSISTENCE.md`
- `docs/NOTIFICATIONS.md`
- `docs/REGISTRIES.md`
- `docs/SUPERVISOR_KERNEL.md`
- `docs/PROJECT_FACTORY.md`
- `docs/WORKFLOW_ENGINE.md`
- `docs/AGENT_RUNTIME.md`
- `docs/PROJECT_SCHEDULER.md`
- `docs/INTEGRATIONS.md`
- `docs/POLICY_AND_PERMISSIONS.md`
- `docs/AGENT_FACTORY.md`
- `docs/RELEASE_MANAGER.md`
- `docs/REFERENCE_RESEARCH_CRITIC_WORKFLOW.md`
- `docs/OBSERVABILITY_AND_RELIABILITY.md`
- `docs/TEST_MATRIX.md`
- `docs/PLATFORM_INTERFACES.md`
- `docs/DEVELOPER_GUIDE.md`
- `docs/COMPATIBILITY_POLICY.md`
- `docs/NOTIFICATION_ADAPTER_INTERFACE.md`
- `docs/ROADMAP.md`
- `docs/ROADMAP_IMPLEMENTATION_AUDIT.md`
- `docs/DOCS_INDEX.md`

## Implementation Status

```text
Phase 0   Foundation / Architecture                    COMPLETE
Phase 1   Machine Contracts / Core Models             COMPLETE
Phase 2   Persistence / Project Registry              COMPLETE
Phase 3   Human Intervention / Email Notification     COMPLETE
Phase 4   Agent / Capability Registries               COMPLETE
Phase 5   Supervisor Orchestration Kernel             COMPLETE
Phase 6   Project Factory / Repository Bootstrap      COMPLETE
Phase 7   Workflow Engine / Multi-Agent Composition   COMPLETE
Phase 8   Agent Runtime / Execution Control           COMPLETE
Phase 9   Project Scheduler / Parallel Execution      COMPLETE
Phase 10  Tools / Providers / Provisioning / Secrets  COMPLETE
Phase 11  Policy / Permissions / Risk / Approval      COMPLETE
Phase 12  Reference Agents / Agent Factory            COMPLETE
Phase 13  Release Manager / Publication Readiness     COMPLETE
Phase 14  Reference Research-Critic Workflow          COMPLETE
Phase 15  Observability / Reliability / CI            COMPLETE
Phase 16  Interfaces / Packaging / Extensibility      COMPLETE
```

Validation baseline:

```text
Core Validation: PASS
Run: 34793901147
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: >= 80%
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
live owner mailbox delivery: PASS
```

## Public Baseline

The distribution builds as `k-supervisor==0.1.0` and exposes the `ksupervisor` Python facade plus the `k-supervisor` CLI. Standard Python entry points support externally packaged agents, capabilities, project templates and adapters without Supervisor-core edits.

ROADMAP v0.2 has no remaining published implementation phase. Future development must be introduced through an explicit roadmap revision rather than silently extending Phase 16.
