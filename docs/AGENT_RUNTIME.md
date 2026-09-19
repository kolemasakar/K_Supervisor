# AGENT_RUNTIME
Опис runtime-рівня K_Supervisor для контрольованого виконання агентів, normalized failures та durable idempotency.

Version: 1.3
Status: ACTIVE
Baseline: v0.4 Phase 2 Operator Control API
Date: 2026-09-16

## Purpose

The Agent Runtime sits behind the existing `AgentDispatcher` boundary.

```text
SupervisorKernel
      |
      v
AgentDispatcher
      |
      v
AgentRuntimeDispatcher
      |
      v
RuntimeAdapter
```

Supervisor and Workflow Engine remain independent of concrete execution mechanisms.

## Runtime Adapter

`RuntimeAdapter` is the replaceable execution boundary. `InProcessRuntimeAdapter` remains available for compatibility and trusted development scenarios. `ProcessRuntimeAdapter` provides the Phase 4 hardened execution path with one isolated worker process per invocation and parent-enforced termination.

## Execution Control

Each invocation receives `ExecutionControl` with cancellation signal, parsed runtime limits and usage counters.

Supported limits include:

```text
timeout_seconds
max_tool_calls
max_tokens
max_sources
max_cost
max_retries
```

Retry orchestration remains owned by Supervisor.

## Timeout, Cancellation and Errors

Timeout/cancellation and handler failures are normalized to `AgentRunResult`; raw execution exceptions do not cross the runtime boundary. Returned results are correlation-validated before acceptance.

The in-process adapter remains cooperative. `ProcessRuntimeAdapter` enforces timeout/cancellation in the parent process: cooperative cancellation is requested first, then termination and kill escalation use bounded joins. Worker exit without a valid result envelope is normalized as a runtime worker crash.

## Operator Cancellation Authority

v0.4 Phase 2 adds durable Task/Workflow operator cancellation above the existing runtime adapter boundary.

```text
ServiceApiV1
  -> OperatorControlApi
  -> SupervisorKernel.cancel_task() / WorkflowEngine.cancel()
  -> AgentRuntimeDispatcher.cancel(run_id) when an active runtime run exists
```

Task and Workflow state now include terminal `CANCELLED` semantics. The kernel records the active runtime `run_id` in Task metadata before dispatch so an operator cancellation can reach the existing runtime dispatcher without creating a second execution path.

If cancellation is persisted while a handler is already executing, a later success result cannot overwrite the durable cancellation. The kernel re-checks authoritative Task state before accepting the returned result and normalizes it as `CANCELLED`.

Workflow cancellation also cancels linked unresolved workflow-owner action and active child tasks identified by `parent_workflow_run_id`. The workflow drive loop re-checks persisted cancellation before writing subsequent RUNNING state.

Cancellation remains cooperative for the in-process adapter and parent-enforced for `ProcessRuntimeAdapter`.

## Runtime Idempotency

For requests with `idempotency_key`, successful results can be replayed with the new request correlation IDs and:

```text
metadata.idempotent_replay = true
```

Reuse of the same semantic idempotency scope with a different input signature is rejected.

### Durable platform path

When `AgentRuntimeDispatcher` is constructed with the platform persistence store, it uses `PersistenceIdempotencyStore`.

Durable scope includes:

```text
project_id
agent_id
capability_id
capability_version
operation
idempotency_key
```

The prior successful result is stored as `RuntimeIdempotencyRecord`. Supported store/process restart therefore does not change replay semantics, and the handler is not invoked again for an equivalent replay.

Scopes are project-isolated. Concurrent durable claims are resolved against the immutable authoritative record and cannot silently replace a different signature.

### Standalone compatibility path

`MemoryIdempotencyStore` remains available when no platform persistence store is supplied. It preserves the original Phase 8 behavior but remains process-local and does not claim restart durability.

## Health and Availability

Runtime execution continues to update Agent Registry availability:

```text
AVAILABLE/DEGRADED -> BUSY during execution
SUCCEEDED          -> AVAILABLE
CANCELLED          -> AVAILABLE
BLOCKED            -> AVAILABLE
runtime failure    -> DEGRADED
repeated failures  -> UNAVAILABLE
```

A later successful run resets the consecutive-failure counter.

## Resource Accounting

Handlers may report controlled resource consumption through `ExecutionControl.consume(...)`. Exceeding configured limits produces normalized `BLOCKED` policy failures. Usage is attached to `AgentRunResult.metrics.runtime_usage`.

Resource accounting remains cooperative inside the handler. Phase 3 centralizes external side-effect enforcement; Phase 4 adds parent-enforced process isolation, bounded cancellation and crash containment.

## Recovery Boundary

Durable runtime idempotency records are project-scoped persistence resources and are included in `ProjectRecoverySnapshot`. Runtime handler/process-local execution stacks themselves are not serialized as authoritative state.

Workflow/Task/Human Intervention durable records determine restart recovery and resumability through their existing platform boundaries. Phase 2 ServiceCommandRecord correlation prevents a restart from blindly duplicating Task/Workflow start commands.

## Validation

Authoritative v0.3 Phase 4 baseline:

```text
Implementation SHA: 34049f601fc8116aa12ee15023f1dc20bc25901a
Core Validation run: 35092932820
Python: 3.13.15
pytest: 117 passed
branch-aware coverage: 85.13%
ResourceWarning gate: PASS
```

Phase 4 verifies isolated success/correlation, parent-enforced timeout, cancellation escalation, worker crash containment, runtime-limit normalization and successful recovery on the next run. v0.4 Phase 2 additionally verifies operator cancellation, late-success suppression, durable CANCELLED state and stale execution-command reconciliation. All predecessor runtime/idempotency/health regressions remain green.

## Current Limits

- `InProcessRuntimeAdapter` cancellation remains cooperative by design;
- `ProcessRuntimeAdapter` is process isolation, not a universal sandbox for arbitrary untrusted Python;
- durable idempotency prevents supported duplicate platform execution but does not claim universal exactly-once external effects;
- distributed worker clusters/remote execution are outside Phase 4 scope.
