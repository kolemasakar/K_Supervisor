# K_Supervisor
Система автоматизованого життєвого циклу AI-проєктів поверх модульної мультиагентної платформи.

Status: PRE-ALPHA
Concept baseline: v0.2
Roadmap baseline: Phase 9
Repository: kolemasakar/K_Supervisor

## Purpose

K_Supervisor combines:

```text
AI Project Lifecycle Supervisor
+
Modular Multi-Agent Platform
```

The Project Control Plane manages onboarding, ProjectSpec approval, project bootstrap, scheduling, owner intervention, notifications, release preparation, and parallel project execution.

The Multi-Agent Core provides Supervisor orchestration, agent contracts, capability-based discovery and routing, workflows, controlled execution, tools/providers, persistence, and auditability.

K_Supervisor is a new project. It is not a fork, clone, or continuation branch of K-Research & Critic.

## Automation Goal

After an owner approves a ProjectSpec, K_Supervisor should automate as much of the project lifecycle as safely and technically possible, including repository/bootstrap work, documentation, roadmap execution, agent creation, validation, and release preparation.

Owner intervention is explicit and resumable.

The initial notification channel is email. WhatsApp, Viber, and other messaging transports are deferred extension points.

GPT Store preparation should be automated where feasible. Publication remains a per-project owner action.

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
- `docs/ROADMAP.md`
- `docs/DOCS_INDEX.md`

## Reference Product

K-Research & Critic v1.0.0 remains a completed production reference product:

```text
kolemasakar/K_Research_Critic
```

Its validated patterns may inform K_Supervisor design, but its runtime is not the new platform architecture baseline.

## Current Phase

Phase 0 - Foundation and Architecture Baseline - COMPLETE.

Phase 1 - Machine Contracts and Core State Models - COMPLETE.

Phase 2 - Persistence and Project Registry - COMPLETE.

Phase 3 - Human Intervention and Email Notification Baseline - COMPLETE.

Phase 4 - Agent and Capability Registries - COMPLETE.

Phase 5 - Supervisor Orchestration Kernel - COMPLETE.

Phase 6 - Project Factory and Repository Bootstrap - COMPLETE.

Phase 7 - Workflow Engine and Multi-Agent Composition - COMPLETE.

Phase 8 - Agent Runtime and Execution Control - COMPLETE.

Validation baseline:

```text
Core Validation: PASS
Python: 3.13.15
pytest: 46 passed
live owner mailbox delivery: PASS
```

Current implementation baseline:

```text
Python >= 3.13
Pydantic v2
JSON Schema 2020-12
SQLite local persistence baseline
EmailProvider abstraction
SMTP relay email transport
AgentRegistry
CapabilityRegistry
ProviderRouter
SupervisorKernel
AgentDispatcher boundary
bounded retry hooks
ProjectFactory
RepositoryAdapter boundary
FilesystemRepositoryAdapter
ProjectSpec-driven bootstrap templates
bootstrap validation and conflict protection
WorkflowDefinition
WorkflowEngine
capability-based workflow composition
conditional nodes
bounded workflow loops
approval pause/resume
RuntimeAdapter
InProcessRuntimeAdapter
AgentRuntimeDispatcher
timeout and cooperative cancellation
runtime resource limits
exception normalization
idempotency hooks
agent health and availability synchronization
GitHub Actions / pytest validation
```

Next roadmap phase: Phase 9 - Project Scheduler and Parallel Execution.
