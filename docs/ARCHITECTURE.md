# ARCHITECTURE
Архітектура K_Supervisor як керуючого рівня AI-проєктів поверх модульного мультиагентного ядра.

Version: 0.3
Status: ACTIVE
Phase: 0

## 1. Objective

K_Supervisor has two architectural layers:

```text
PROJECT LIFECYCLE CONTROL PLANE
              |
              v
MODULAR MULTI-AGENT EXECUTION CORE
```

The Control Plane manages long-lived projects. The Multi-Agent Core performs project work.

## 2. Core Principles

- Project is the top-level managed unit; Task is a unit of work inside a Project.
- Project behavior follows Project Contract and Project Lifecycle.
- Agent execution follows Agent Contract.
- Work is selected by capability rather than concrete agent name where practical.
- Supervisor orchestrates; agents execute specialized work.
- Agent implementations remain replaceable.
- Project lifecycle state and project operational state are separate.
- Task, workflow, agent-run, approval, release, and domain-result states are also separate.
- Human intervention is explicit and resumable.
- Email is the initial owner notification channel.
- Other messaging channels are deferred adapters.
- Independent projects may progress concurrently.
- Important decisions and transitions are auditable without hidden chain-of-thought.

## 3. Logical Architecture

```text
OWNER / ONBOARDING
        |
        v
+---------------------------+
| PROJECT CONTROL PLANE     |
| Service/API v1            |
| Project Factory           |
| Project Registry          |
| Project Scheduler         |
| Human Intervention Broker |
| Notification Broker       |
| Secret Manager            |
| Release Manager           |
+-------------+-------------+
              |
              v
+---------------------------+
| PROJECT SUPERVISOR        |
| task/workflow control     |
| approvals and policy      |
| capability requirements   |
+-------------+-------------+
              |
       +------+------+
       |             |
       v             v
+-------------+  +----------------+
| AGENT       |  | CAPABILITY     |
| REGISTRY    |  | REGISTRY       |
+------+------+  +-------+--------+
       |                 |
       +--------+--------+
                |
                v
          ROUTER / MATCHER
                |
                v
           AGENT RUNTIME
             /      \
            v        v
          TOOLS   PROVIDERS
```

## 4. Control Plane Components

### Service/API v1

Provides authenticated/scoped external Project reads and lifecycle/operational transitions while delegating authoritative state changes to Project Registry. Durable mutation idempotency is service-owned; state-machine semantics remain control-plane-owned.

### Project Factory

Creates or connects the project repository and bootstraps documentation, roadmap, architecture, initial automation, and project scaffolding from an approved ProjectSpec.

### Project Registry

Maintains the authoritative index of managed projects and their current specification, state, repository reference, roadmap phase, blockers, and release targets.

### Project Scheduler

Coordinates concurrent project work under project and global limits. A project waiting for owner action does not block unrelated projects.

### Human Intervention Broker

Creates structured HumanActionRequests with a clear required action, blocking status, and resume condition.

### Notification Broker

Consumes transport-neutral NotificationEvents.

Initial baseline:

```text
primary channel: EMAIL
required initial channels: EMAIL only
```

WhatsApp, Viber, and other messaging transports are future extension points.

### Secret Manager

Provides a replaceable protected reference boundary for integration access data. Normal project documentation and notifications use references rather than embedded values.

### Release Manager

Prepares and validates release targets and performs publication handoff. GPT Store preparation should be automated where feasible; publication remains a per-project owner action.

## 5. Multi-Agent Core

### Supervisor Core

Supervisor accepts project tasks, creates execution identities, resolves workflow requirements, requests capabilities, applies policy and approvals, dispatches agent runs, processes normalized results, and manages retries and escalation.

### Agent Registry

Stores executable agent descriptors and availability.

### Capability Registry

Stores capability descriptors independently of concrete agent implementations.

### Router / Matcher

Selects eligible agents from capability requirements and compatibility constraints.

### Agent Runtime

Executes AgentRunRequest and returns normalized AgentRunResult with timeout, cancellation, limit, error, and telemetry boundaries.

### Workflow Engine

Represents multi-step work as explicit workflow definitions. Workflow nodes normally request capabilities rather than concrete agents.

## 6. Project Initiation

```text
Onboarding chat
-> Draft ProjectSpec
-> owner review
-> ProjectSpec APPROVED
-> Project Factory
-> project execution
```

Material scope changes require a new ProjectSpec version.

## 7. Human Intervention

```text
Project work
-> HumanActionRequest
-> NotificationEvent
-> Email
-> owner action
-> verification when possible
-> resume
```

The project keeps its lifecycle stage while its operational state changes to reflect waiting or blocking.

## 8. Parallel Projects

Each project isolates its specification, lifecycle and operational state, workspace, repository references, project access references, budgets, tasks, runs, artifacts, logs, and releases.

Shared resources are controlled through scheduler limits and explicit locking.

## 9. Primary Platform Objects

```text
Project
ProjectSpec
ProjectLifecycleState
ProjectOperationalState
Task
WorkflowDefinition
WorkflowRun
CapabilityRequirement
CapabilityDescriptor
AgentDescriptor
AgentRunRequest
AgentRunResult
ApprovalRecord
HumanActionRequest
NotificationEvent
NotificationDelivery
SecretReference
Release
ReleaseTarget
ArtifactReference
AuditEvent
```

Machine schemas are scheduled for Phase 1.

## 10. Persistence and Resume

Project, workflow, run, intervention, notification, release, artifact, and audit state must be durable enough for safe reconstruction without hidden in-memory state.

## 11. First Working and Release Boundary

FIRST_WORKING is a project milestone defined by ProjectSpec.

RELEASE_READY is a target-specific readiness state.

Publication is a separate action and may remain owner-controlled.

## 12. Reference Product Boundary

K-Research & Critic v1.0.0 remains a production reference source only. Its validated patterns may inform K_Supervisor, but its runtime structure is not inherited as the platform architecture.

## 13. Phase 0 Boundary

Phase 0 defines architecture and logical contracts. Runtime implementation begins in Phase 1.
