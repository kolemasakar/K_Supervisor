# AGENT_RUNTIME
Опис runtime-рівня K_Supervisor для контрольованого виконання агентів, normalized failures та durable idempotency.

Version: 1.1
Status: ACTIVE
Baseline: v0.3 Phase 2 COMPLETE
Date: 2026-09-14

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

`RuntimeAdapter` is the replaceable execution boundary. `InProcessRuntimeAdapter` remains the current reference implementation. Future process/container/remote adapters can implement the same contract.

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

The current in-process adapter still uses cooperative cancellation and cannot forcibly terminate arbitrary Python code. Strong process isolation belongs to v0.3 Phase 4.

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

This remains cooperative accounting. Phase 3 centralizes external side-effect enforcement; Phase 4 strengthens runtime isolation/cancellation.

## Recovery Boundary

Durable runtime idempotency records are project-scoped persistence resources and are included in `ProjectRecoverySnapshot`. Runtime handler/process-local execution stacks themselves are not serialized as authoritative state.

Workflow/Task/Human Intervention durable records determine restart recovery and resumability through their existing platform boundaries.

## Validation

Authoritative v0.3 Phase 2 baseline:

```text
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Core Validation run: 34808287772
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
ResourceWarning gate: PASS
```

Phase 2 verifies durable replay across SQLite restart, project isolation, notification/execution duplicate protection and interrupted workflow/project resume. Full predecessor runtime timeout/cancellation/limit/health regressions remain green.

## Current Limits

- in-process cancellation remains cooperative;
- no OS/process isolation yet;
- durable idempotency prevents supported duplicate platform execution but does not claim universal exactly-once external effects;
- centralized external side-effect enforcement belongs to Phase 3.
