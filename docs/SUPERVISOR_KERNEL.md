# SUPERVISOR_KERNEL
Опис мінімального ядра оркестрації Supervisor для виконання однієї capability-задачі.

Version: 1.0
Status: ACTIVE
Phase: 5

## 1. Scope

Phase 5 implements the smallest useful task-level orchestration path.

```text
Project
  -> Task
  -> CapabilityRequirement
  -> AgentRegistry
  -> ProviderRouter
  -> AgentDispatcher
  -> AgentRunRequest
  -> AgentRunResult
  -> persistence
```

The kernel is not a full workflow engine or full Agent Runtime.

## 2. Responsibilities

`SupervisorKernel`:

- verifies that the Project exists and is operationally ACTIVE;
- creates and persists Task and single-capability WorkflowRun records;
- resolves eligible providers through AgentRegistry;
- delegates soft preference ranking to ProviderRouter;
- creates request/run identifiers;
- dispatches through the AgentDispatcher boundary;
- validates result correlation fields;
- persists every AgentRunResult;
- applies bounded retry policy for explicitly retryable results;
- exposes an escalation hook for terminal failure;
- completes Task and WorkflowRun state.

## 3. Task State Machine

```text
NEW
 -> ROUTING
 -> RUNNING
 -> SUCCEEDED

RUNNING
 -> RETRYING
 -> RUNNING

ROUTING -> BLOCKED | FAILED
RUNNING -> FAILED | BLOCKED
RETRYING -> FAILED | BLOCKED
```

Task.status remains compatible with the Phase 1 string contract. Transition validity is enforced by the Supervisor layer.

## 4. Routing Boundary

Registry code determines hard eligibility.

ProviderRouter applies soft routing preferences. Phase 5 supports `preferences.preferred_agents` while preserving deterministic version/agent ordering.

Routing does not import concrete agent implementations.

## 5. Dispatch Boundary

`AgentDispatcher` is a protocol.

`LocalAgentDispatcher` is a minimal in-process adapter for development and tests. It is not the final Agent Runtime. Timeout, cancellation, resource control, remote execution, and health management remain later runtime concerns.

## 6. Result Validation

Before a result is accepted, these fields must match the request:

```text
request_id
project_id
task_id
workflow_run_id
run_id
agent_id
capability_id
capability_version
```

A correlation mismatch becomes a normalized failed AgentRunResult and cannot be accepted as successful work.

## 7. Retry and Escalation

Retry is bounded by `RetryPolicy.max_attempts`.

A retry occurs only when the returned error is explicitly marked retryable or the execution status is TIMED_OUT.

Each attempt receives a new request_id and run_id and is persisted separately.

Terminal failure may invoke an injected escalation hook. Human notification policy remains separate from the task kernel.

## 8. Persistence

The kernel uses the existing PersistenceStore interface and has no SQLite-specific dependency.

It persists:

- Task;
- WorkflowRun;
- every AgentRunResult.

## 9. Deferred

The following are intentionally deferred:

- multi-node workflow execution;
- approval gates inside workflows;
- full Agent Runtime controls;
- provider/tool adapters;
- advanced policy enforcement;
- parallel project scheduling;
- reference production agents.

## 10. Phase 5 Exit Contract

One Project Task can request one capability and receive a validated result from a dynamically selected Agent without Supervisor-core imports of that concrete Agent.
