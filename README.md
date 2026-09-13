# K_Supervisor
Система автоматизованого життєвого циклу AI-проєктів поверх модульної мультиагентної платформи.

Status: PRE-ALPHA
Concept baseline: v0.2
Roadmap baseline: Phase 11
Repository: `kolemasakar/K_Supervisor`

## Purpose

K_Supervisor combines an AI Project Lifecycle Supervisor with a modular multi-agent platform. It manages approved projects, orchestration, workflows, controlled execution, parallel scheduling, integrations, owner intervention, notifications, and release preparation.

K_Supervisor is a separate project. K-Research & Critic v1.0.0 remains a reference product only.

## Core Documents

- `docs/VISION.md`
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
- `docs/ROADMAP.md`
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
Phase 11  Policy / Permissions / Risk / Approval      NEXT
```

Validation baseline:

```text
Core Validation: PASS
Python: 3.13.15
pytest: 59 passed
live owner mailbox delivery: PASS
```

Current integration baseline includes replaceable Tool/Provider contracts and registries, protected `secret://` access references, environment-backed secret resolution, provisioning adapters, provider-independent model selection hooks, and ProjectSpec rejection of raw credential-like values.
