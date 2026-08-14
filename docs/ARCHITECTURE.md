# ARCHITECTURE
Архітектурні принципи, компоненти та межі модульної мультиагентної платформи K_Supervisor.

Version: 0.1
Status: ACTIVE
Phase: 0

## 1. Architectural Objective

K_Supervisor is a domain-neutral orchestration platform built around explicit contracts and capability-based composition.

The architecture separates:

```text
orchestration
agent execution
capability description
workflow definition
policy and permissions
state and persistence
tools and providers
observability
```

No single specialized workflow defines the platform architecture.

## 2. Architectural Principles

### 2.1 Platform first, workflows second

The core must remain reusable across domains. Research, critique, planning, analysis, and other workflows are compositions built on the platform.

### 2.2 Contract-driven interaction

All executable agents communicate through a versioned Agent Contract. Supervisor must not depend on private agent implementation details.

### 2.3 Capability-based discovery

Supervisor selects eligible executors using declared capabilities and constraints rather than hard-coded imports or agent names.

### 2.4 Supervisor orchestrates, agents execute

Supervisor owns task decomposition, routing, workflow control, approval boundaries, retries, and final execution status. Specialized domain work belongs to agents.

### 2.5 Domain-neutral core

Domain rules must be supplied through capabilities, profiles, policies, workflow definitions, or specialized agents. They must not be embedded in the core unless universally required.

### 2.6 Replaceable agents

Any agent should be replaceable by another compatible implementation that satisfies the required contract and capability constraints.

### 2.7 Capabilities are separate from agents

An agent is an execution entity. A capability is a declarative statement of work that an executor can perform. One agent may expose many capabilities, and one capability may have many providers.

### 2.8 Mediated collaboration

Agents should not directly depend on each other. Cross-agent work is mediated through Supervisor, workflow state, events, or task envelopes so routing remains observable and replaceable.

### 2.9 Explicit state

Task state, workflow state, agent run state, approval state, and domain result status are separate concepts.

### 2.10 Controlled autonomy

Autonomous execution is allowed only inside explicit policy, permission, resource, and approval boundaries.

### 2.11 Provider isolation

LLM providers, external APIs, tools, storage, and execution backends are adapters behind platform interfaces.

### 2.12 Deterministic boundaries

Non-deterministic AI work is wrapped by deterministic validation of envelopes, schemas, permissions, state transitions, limits, and persistence operations.

### 2.13 Idempotency and retries

Operations that can cause duplicate side effects must define idempotency semantics before automatic retry is allowed.

### 2.14 Auditability by default

Important routing decisions, approvals, tool calls, state transitions, failures, and final outputs must be representable as audit records without storing hidden chain-of-thought.

### 2.15 Versioned evolution

Contracts and capability descriptors evolve through explicit versions. Breaking changes require deliberate migration rather than silent mutation.

## 3. Logical Architecture

```text
USER / CALLER
     |
     v
+---------------------------+
|       SUPERVISOR CORE     |
| task control              |
| workflow control          |
| policy gates              |
| routing decisions         |
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
       +-----------------+
       | ROUTER / MATCHER|
       +--------+--------+
                |
                v
       +-----------------+
       | AGENT RUNTIME   |
       +--------+--------+
                |
      +---------+----------+
      |                    |
      v                    v
+-----------+        +-------------+
| TOOLS /   |        | PROVIDERS / |
| SERVICES  |        | MODELS      |
+-----------+        +-------------+

Shared platform services:
- workflow definitions
- context/state
- persistence
- policy/permissions
- schemas/validation
- observability/audit
```

## 4. Core Components

### 4.1 Supervisor Core

Responsibilities:

- accept tasks;
- create task identity;
- resolve workflow requirements;
- request capabilities;
- enforce approval and policy gates;
- dispatch agent runs;
- process results;
- manage retries and escalation;
- finalize task status.

Supervisor must not become a universal domain agent.

### 4.2 Agent Registry

Stores executable agent descriptors and current availability.

Primary operations:

```text
register
unregister
get
list
find_by_type
find_by_capability
health
```

### 4.3 Capability Registry

Stores normalized capability descriptors independently of agent implementation details.

Primary operations:

```text
register
resolve
find_candidates
validate_compatibility
list_versions
```

### 4.4 Router / Matcher

Converts workflow requirements into eligible agent candidates.

Routing must separate hard constraints from preference scoring.

Hard constraints may include:

- capability identifier;
- compatible version;
- required input/output schema;
- policy permission;
- tool availability;
- trust/risk requirements;
- provider restrictions;
- execution environment.

Preference scoring may include:

- cost;
- latency;
- quality profile;
- locality;
- historical reliability;
- user preference.

### 4.5 Agent Runtime

Executes one AgentRunRequest and returns one AgentRunResult under the Agent Contract.

The runtime owns timeout, cancellation, exception normalization, resource limits, and execution telemetry.

### 4.6 Workflow Engine

Represents multi-step collaboration as explicit workflow definitions or task graphs.

A workflow node requests capabilities. It should not require one concrete agent implementation unless explicitly pinned.

### 4.7 State and Persistence

Stores task, workflow, run, approval, artifact, and audit state.

Persistence implementation is replaceable. Core semantics must not depend on one database engine.

### 4.8 Policy and Permission Layer

Defines what each task, workflow, agent, capability, and tool is allowed to do.

Permission checks occur before execution, not after side effects.

### 4.9 Tool and Provider Adapters

External dependencies remain behind stable interfaces. Agents declare dependencies without embedding platform-global provider assumptions.

### 4.10 Observability and Audit

Records execution metadata needed to understand what ran, why it was selected, what boundaries were applied, what failed, and what artifact was produced.

Hidden chain-of-thought is not an audit artifact.

## 5. Primary Domain Objects

The initial platform object model includes:

```text
Task
WorkflowDefinition
WorkflowRun
CapabilityRequirement
CapabilityDescriptor
AgentDescriptor
AgentRunRequest
AgentRunResult
ApprovalRecord
PolicyDecision
ArtifactReference
AuditEvent
```

Machine schemas are scheduled for Phase 1.

## 6. Interaction Rule

The preferred collaboration pattern is:

```text
Workflow requests capability
-> Supervisor resolves candidates
-> Router selects eligible agent
-> Supervisor creates AgentRunRequest
-> Runtime invokes agent
-> Agent returns AgentRunResult
-> Supervisor validates and records result
-> Workflow continues
```

An agent that needs additional work should request another capability through the platform rather than importing or directly calling another agent implementation.

## 7. Reference Product Boundary

K-Research & Critic v1.0.0 is an external reference source.

The new platform may learn from its validated patterns, including explicit profile approval, independent critique, evidence handling, state separation, and auditable workflow transitions.

K_Supervisor does not preserve K-Research & Critic internal structure as a compatibility requirement.

A future Research-Critic workflow should be re-composed from K_Supervisor capabilities and contracts instead of copied as a legacy subsystem.

## 8. Repository Bootstrap Boundaries

Phase 0 creates documentation and structural placeholders only. Runtime behavior begins in Phase 1 and later phases.

This prevents premature coupling before contracts are approved.
