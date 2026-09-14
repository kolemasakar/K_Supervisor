# ROADMAP v0.2 ARCHIVE
Історичний snapshot завершеного ROADMAP v0.2 для K_Supervisor.

Version: 0.2
Status: COMPLETE / ARCHIVED
Roadmap start: 2026-08-14
Roadmap completed: 2026-09-14
Archived: 2026-09-14

> This file preserves the completed v0.2 roadmap after approval of ROADMAP v0.3. The authoritative active roadmap is `docs/ROADMAP.md`. Completion evidence remains in `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` and `ROADMAP_IMPLEMENTATION_AUDIT.md`.

## 1. Roadmap Rule

K_Supervisor starts from Phase 0 and does not continue the historical phase numbering of K-Research & Critic.

Each phase must define deliverables, tests, exit criteria, and deferred work.

The v0.2 roadmap adds the Project Lifecycle Control Plane above the previously defined Multi-Agent Core.

## Phase 0 - Foundation and Architecture Baseline

Goal: freeze the product concept before runtime implementation.

Scope:

- define K_Supervisor as AI Project Lifecycle Supervisor + Modular Multi-Agent Platform;
- define Project Control Plane;
- define Project Contract / ProjectSpec;
- define Project Lifecycle and operational state separation;
- define Agent Contract;
- define Capability Model;
- define email-first Notification Broker policy;
- define parallel-project requirement;
- define release/publication boundary;
- define reference-product boundary;
- create repository bootstrap structure.

Primary deliverables:

```text
README.md
docs/VISION.md
docs/ARCHITECTURE.md
docs/PROJECT_CONTROL_PLANE.md
docs/PROJECT_CONTRACT.md
docs/PROJECT_LIFECYCLE.md
docs/AGENT_CONTRACT.md
docs/CAPABILITY_MODEL.md
docs/ROADMAP.md
docs/DOCS_INDEX.md
```

Exit criteria:

- Project is the top-level managed unit;
- Project and Task are separated;
- Agent and Capability are separated;
- Control Plane and Multi-Agent Core boundaries are explicit;
- email is the initial notification channel;
- future messaging channels are deferred;
- GPT Store preparation and publication are separate;
- parallel project operation is an explicit requirement;
- K-Research & Critic remains reference-only.

## Phase 1 - Machine Contracts and Core State Models

Goal: convert Phase 0 logical contracts into executable validated models.

Planned work:

- select implementation language/runtime baseline;
- implement Project and ProjectSpec models;
- implement lifecycle and operational state models;
- implement Task and WorkflowRun models;
- implement AgentDescriptor, CapabilityDescriptor, AgentRunRequest, and AgentRunResult;
- implement HumanActionRequest and NotificationEvent;
- implement Release and ReleaseTarget models;
- add JSON schemas where interchange requires them;
- add validation, serialization, compatibility, and transition tests;
- freeze first machine-readable contract versions.

Exit criteria:

- core models round-trip reliably;
- invalid state transitions fail deterministically;
- ProjectSpec approval state is machine-enforced;
- contract compatibility is testable.

## Phase 2 - Persistence and Project Registry

Goal: establish durable project identity and resumable state early.

Planned work:

- persistence interface;
- initial local persistence backend;
- Project Registry;
- ProjectSpec version storage;
- lifecycle and operational transition records;
- task/workflow/run records;
- artifact references;
- release records;
- recovery and resume baseline.

Exit criteria:

- projects survive process restart;
- current project state can be reconstructed without hidden memory;
- multiple projects can be registered independently.

## Phase 3 - Human Intervention and Email Notification Baseline

Goal: provide the owner-control boundary required for autonomous project work.

Planned work:

- Human Intervention Broker;
- HumanActionRequest state machine;
- Notification Broker;
- EmailAdapter / EmailProvider interface;
- one working email transport;
- owner email configuration;
- delivery attempt records;
- duplicate suppression / idempotency protection;
- verification and resume hooks;
- notification policy for ACTION_REQUIRED, FIRST_WORKING, RELEASE_READY, and critical failures.

Deferred:

```text
WhatsApp
Viber
other messaging transports
```

Exit criteria:

- a project can enter WAITING_FOR_OWNER;
- owner receives an email with a structured required action;
- the project can resume after the completion condition is verified;
- unrelated projects remain unaffected.

## Phase 4 - Agent and Capability Registries

Goal: provide dynamic discovery without hard-coded Supervisor imports.

Planned work:

- AgentRegistry;
- CapabilityRegistry;
- capability version resolution;
- provider registration;
- availability state;
- duplicate/conflict handling;
- compatibility tests.

Exit criteria:

- agents can be added or removed without Supervisor-core changes;
- providers can be resolved by capability requirement.

## Phase 5 - Supervisor Orchestration Kernel

Goal: implement the smallest useful task-level Supervisor.

Planned work:

- task intake within a Project;
- task/run identifiers;
- capability requirement creation;
- candidate resolution;
- dispatch boundary;
- normalized result handling;
- retry and escalation hooks;
- explicit task state machine.

Exit criteria:

- one project task can request one capability and receive a validated result from a dynamically selected agent.

## Phase 6 - Project Factory and Repository Bootstrap

Goal: automate creation of approved projects.

Planned work:

- onboarding-to-ProjectSpec handoff;
- repository create/connect adapter;
- reusable project templates;
- README and baseline documentation generation;
- roadmap generation;
- architecture/bootstrap generation;
- initial CI scaffolding where required;
- initial agent/workflow scaffolding;
- bootstrap validation;
- Project Registry update.

Exit criteria:

- an approved ProjectSpec can produce a valid managed repository with minimum project documentation and structure;
- manual owner intervention is requested only at explicit boundaries.

## Phase 7 - Workflow Engine and Multi-Agent Composition

Goal: orchestrate multi-step collaboration.

Planned work:

- WorkflowDefinition;
- workflow nodes and transitions;
- sequential and conditional nodes;
- capability-based node binding;
- bounded iteration loops;
- approval gates;
- delegation through Supervisor;
- workflow validation.

Exit criteria:

- a workflow can use multiple capabilities without direct agent coupling.

## Phase 8 - Agent Runtime and Execution Control

Goal: standardize safe agent execution.

Planned work:

- runtime adapter interface;
- local/in-process executor;
- timeout and cancellation;
- exception normalization;
- resource limits;
- retry classification;
- idempotency hooks;
- agent health and availability.

Exit criteria:

- runtime failures are isolated and represented through Agent Contract statuses.

## Phase 9 - Project Scheduler and Parallel Execution

Goal: support simultaneous work across multiple independent projects.

Planned work:

- Project Scheduler;
- project priority;
- per-project concurrency limits;
- global concurrency limits;
- shared-resource locks;
- provider/rate-limit coordination;
- project-level budgets;
- blocked-project isolation;
- parallel execution tests.

Exit criteria:

- at least two independent projects can make progress concurrently;
- WAITING_FOR_OWNER on one project does not stop the other;
- shared limits are enforced deterministically.

## Phase 10 - Tools, Providers, Provisioning, and Secret Backends

Goal: connect projects to external systems through stable adapters.

Planned work:

- Tool interface;
- Provider interface;
- dependency declaration;
- tool/provider registry;
- protected access-reference interface;
- initial protected storage backend;
- repository/service provisioning adapters;
- server/database/cloud integration patterns;
- availability checks;
- provider-independent model selection hooks.

Exit criteria:

- platform integrations can be replaced behind stable interfaces;
- project access data is not embedded in normal documentation or notification events.

## Phase 11 - Policy, Permissions, Risk, and Approval

Goal: enforce controlled autonomy before side effects occur.

Planned work:

- policy decision model;
- capability risk classes;
- side-effect permissions;
- per-agent tool permissions;
- approval gates;
- project/workflow policy constraints;
- least-privilege execution context;
- audit of policy decisions.

Exit criteria:

- prohibited operations are blocked before execution;
- material permission expansion requires explicit approval.

## Phase 12 - Reference Agents and Agent Factory

Goal: validate the common contracts and automate new agent creation.

Planned work:

- reusable agent template/scaffolder;
- AgentDescriptor generation;
- capability declaration generation;
- validation and test template;
- automatic registry integration;
- reference agents such as ResearchAgent, CriticAgent, ReportAgent, DataAnalysisAgent, and FactCheckAgent.

Exit criteria:

- at least three agent types use the same Agent Contract;
- at least one capability has two interchangeable providers;
- a new compliant agent can be scaffolded and validated with minimal manual work.

## Phase 13 - Release Manager and Publication Readiness

Goal: automate release preparation after a project reaches a working state.

Planned work:

- Release Manager;
- Release and ReleaseTarget state machines;
- generic release readiness checks;
- release artifacts and checklists;
- FIRST_WORKING event handling;
- RELEASE_READY event handling;
- GPT Store preparation profile;
- automated preparation of feasible GPT assets and validation;
- owner publication handoff.

Exit criteria:

- a project can move from FIRST_WORKING to target-specific RELEASE_READY;
- GPT Store publication requirements that can be generated or validated automatically are prepared automatically;
- publication remains an explicit per-project owner action.

## Phase 14 - Reference Research-Critic Workflow

Goal: demonstrate that K-Research & Critic behavior can be re-composed on the new platform.

Planned work:

- study v1.0.0 reference behavior;
- define Research-Critic workflow from capabilities;
- implement profile approval as a reusable mechanism;
- implement independent critique/revision loop;
- compare behavior against reference expectations;
- document intentional differences.

Exit criteria:

- required behavior is expressed through new contracts and registries;
- no direct legacy runtime dependency exists.

## Phase 15 - Observability, Reliability, CI, and Test Matrix

Goal: make project and platform behavior diagnosable and regression-safe.

Planned work:

- structured audit events;
- project and agent metrics;
- routing records;
- notification records;
- release validation records;
- integration tests;
- failure injection;
- recovery tests;
- deterministic fixtures;
- CI quality gates;
- coverage and performance baseline.

Exit criteria:

- major project transitions, routing decisions, intervention requests, notifications, and releases are testable and auditable.

## Phase 16 - Interfaces, Packaging, and Extensibility

Goal: expose a stable platform for wider use and extension.

Planned work:

- CLI and/or API boundary;
- configuration model;
- extension discovery;
- packaging;
- example project templates and workflows;
- developer documentation;
- compatibility policy;
- future notification adapter interface documentation.

Exit criteria:

- an external developer can add a compliant agent, capability, project template, or adapter without changing Supervisor core code.

## Roadmap Closure

ROADMAP v0.2 is complete as of 2026-09-14.

```text
Published phases: 0-16
Completed phases: 0-16
Unmet published exit criteria: 0
Current approved implementation phase: NONE at v0.2 closure
Phase 17: NOT DEFINED
```

Completion evidence is recorded in:

- `docs/PROJECT_CHECKPOINT_PHASE_16_COMPLETE.md`;
- `docs/PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md`;
- `docs/ROADMAP_IMPLEMENTATION_AUDIT.md`;
- `docs/PROJECT_STATE.md`.

The successor roadmap is ROADMAP v0.3. It uses revision-local phase numbering beginning again at `v0.3 Phase 0`; this archive does not define or imply a Phase 17.
