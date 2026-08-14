# ROADMAP
Новий поетапний план розвитку K_Supervisor від Phase 0 до модульної production-ready мультиагентної платформи.

Version: 0.1
Status: ACTIVE
Roadmap start: 2026-08-14

## 1. Roadmap Rule

K_Supervisor starts with a new roadmap from Phase 0.

K-Research & Critic v1.0.0 is a production reference source only. Its historical phase numbering does not continue in this repository.

Each phase should have explicit deliverables, tests, exit criteria, and a checkpoint before the next phase begins.

## Phase 0 - Foundation and Architecture Baseline

Goal: define the new platform before runtime implementation begins.

Scope:

- establish K_Supervisor identity and boundaries;
- define VISION;
- define architectural principles;
- define Agent Contract;
- define Capability Model;
- adopt project file/documentation standard;
- create repository bootstrap structure;
- define reference-product boundary;
- create new ROADMAP.

Deliverables:

```text
README.md
docs/VISION.md
docs/ARCHITECTURE.md
docs/AGENT_CONTRACT.md
docs/CAPABILITY_MODEL.md
docs/ROADMAP.md
docs/DOCS_INDEX.md
bootstrap directories
```

Exit criteria:

- platform is explicitly domain-neutral;
- Agent and Capability abstractions are separated;
- Supervisor responsibility boundary is documented;
- K-Research & Critic is reference-only;
- no legacy runtime is cloned or forked;
- repository structure exists for Phase 1.

## Phase 1 - Machine Contracts and Core Models

Goal: convert Phase 0 architecture into executable, validated core contracts.

Planned work:

- choose initial implementation language/runtime baseline;
- implement Task, WorkflowRun, AgentDescriptor, CapabilityDescriptor, AgentRunRequest, and AgentRunResult models;
- create JSON schemas where external interchange requires them;
- implement validation and serialization;
- freeze Agent Contract v1.0 and Capability Schema v1.0;
- add unit tests for valid and invalid envelopes.

Exit criteria:

- all core models round-trip reliably;
- invalid contracts fail deterministically;
- schema/version compatibility is testable.

## Phase 2 - Agent and Capability Registries

Goal: provide dynamic discovery without hard-coded Supervisor imports.

Planned work:

- AgentRegistry;
- CapabilityRegistry;
- provider registration;
- capability version resolution;
- availability state;
- duplicate and conflict handling;
- registry tests.

Exit criteria:

- agents can be added and removed without Supervisor code changes;
- providers can be discovered by capability requirement.

## Phase 3 - Supervisor Orchestration Kernel

Goal: implement the smallest useful Supervisor core.

Planned work:

- task intake;
- task/run identifiers;
- capability requirement creation;
- candidate resolution;
- dispatch boundary;
- normalized result handling;
- failure and retry policy hooks;
- explicit task state machine.

Exit criteria:

- one task can request one capability and receive a validated result through a dynamically selected agent.

## Phase 4 - Workflow Engine and Multi-Agent Composition

Goal: orchestrate multi-step agent collaboration.

Planned work:

- WorkflowDefinition;
- workflow nodes and transitions;
- sequential and conditional nodes;
- capability-based node binding;
- delegation through Supervisor;
- bounded iteration loops;
- approval gates;
- workflow validation.

Exit criteria:

- a workflow can execute multiple different capabilities without direct agent coupling.

## Phase 5 - Agent Runtime and Execution Control

Goal: standardize safe execution behavior across agent implementations.

Planned work:

- runtime adapter interface;
- local/in-process executor;
- timeout and cancellation;
- normalized exceptions;
- resource limits;
- idempotency hooks;
- retry classification;
- agent health/availability.

Exit criteria:

- runtime failures are isolated and represented through Agent Contract statuses.

## Phase 6 - Context, State, Persistence, and Resume

Goal: make workflows durable and resumable.

Planned work:

- task state repository;
- workflow state repository;
- run records;
- artifact references;
- approval records;
- persistence interface;
- initial local persistence implementation;
- resume/recovery semantics.

Exit criteria:

- interrupted workflows can be reconstructed without hidden in-memory state.

## Phase 7 - Tools and Provider Adapter Layer

Goal: decouple agents from external services and model providers.

Planned work:

- Tool interface;
- Provider interface;
- dependency declaration;
- tool/provider registry;
- credentials by reference;
- availability checks;
- provider-independent model selection hooks.

Exit criteria:

- at least two interchangeable adapters can satisfy one abstract dependency class.

## Phase 8 - Policy, Permissions, Risk, and Approval

Goal: enforce controlled autonomy before side effects occur.

Planned work:

- policy decision model;
- capability risk classes;
- side-effect permissions;
- per-agent tool permissions;
- approval gates;
- user/workflow policy constraints;
- least-privilege context and credentials;
- audit of policy decisions.

Exit criteria:

- prohibited operations are blocked deterministically before execution.

## Phase 9 - Reference Agents

Goal: validate platform neutrality with several replaceable agent types.

Planned candidates:

```text
ResearchAgent
CriticAgent
ReportAgent
DataAnalysisAgent
FactCheckAgent
```

Agents are reference implementations, not privileged Supervisor components.

Exit criteria:

- at least three agent types use the same Agent Contract;
- at least one capability has two interchangeable providers.

## Phase 10 - Reference Research-Critic Workflow

Goal: prove that the completed K-Research & Critic behavior can be expressed as a K_Supervisor composition without importing its legacy runtime.

Planned work:

- study v1.0.0 reference behavior;
- define Research-Critic workflow from capabilities;
- implement profile approval gate as reusable workflow/policy mechanism;
- implement independent critique loop;
- compare behavior against reference expectations;
- document intentional differences.

Exit criteria:

- workflow reproduces required behavior through new contracts and registries;
- no direct clone/fork dependency exists.

## Phase 11 - Observability, Audit, Reliability, and Test Matrix

Goal: make platform behavior diagnosable and regression-safe.

Planned work:

- structured audit events;
- metrics;
- routing decision records;
- integration tests;
- failure injection;
- recovery tests;
- deterministic fixtures;
- CI quality gates;
- performance baseline.

Exit criteria:

- major state transitions and routing decisions are testable and auditable.

## Phase 12 - Interfaces, Packaging, and Extensibility

Goal: expose a stable platform for external use and extension.

Planned work:

- CLI and/or API boundary;
- configuration model;
- plugin/extension discovery;
- packaging;
- example workflows;
- developer documentation;
- compatibility policy.

Exit criteria:

- an external developer can add a compliant agent and capability without changing Supervisor core code.

## Future Direction

Later phases may cover distributed execution, remote agents, event buses, multi-tenant isolation, capability marketplaces, scheduling, advanced planning, and production deployment profiles.

These are intentionally deferred until the local contract-driven platform is proven.
