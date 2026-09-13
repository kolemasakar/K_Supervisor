# AGENT_RUNTIME
Опис Phase 8 runtime-рівня для контрольованого виконання агентів та нормалізації runtime failures.

Version: 1.0
Status: ACTIVE
Phase: 8

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

`RuntimeAdapter` is the replaceable execution boundary.

Phase 8 provides `InProcessRuntimeAdapter` as the first reference implementation. It runs registered handlers in a worker thread and returns only `AgentRunResult` envelopes to the orchestration layer.

Future process, container, remote-service, or managed runtimes can implement the same adapter contract.

## Execution Control

Each invocation receives an `ExecutionControl` object with:

- cancellation signal;
- parsed runtime limits;
- runtime usage counters;
- cooperative resource-consumption checks.

Supported request limits in the Phase 8 baseline are:

```text
timeout_seconds
max_tool_calls
max_tokens
max_sources
max_cost
max_retries
```

`max_retries` is accepted as part of the common request contract but retry orchestration remains owned by `SupervisorKernel`.

Unknown limit names and invalid limit values are rejected deterministically as `VALIDATION_ERROR`.

## Timeout and Cancellation

`timeout_seconds` is enforced by the in-process adapter and normalized to:

```text
status: TIMED_OUT
error.category: TIMEOUT
error.retryable: true
```

Cancellation is cooperative. `AgentRuntimeDispatcher.cancel(run_id)` signals the active `ExecutionControl`; a compliant in-process handler calls `check_cancelled()` at safe interruption points.

A cooperative cancellation is normalized to:

```text
status: CANCELLED
error.category: CANCELLED
```

The Phase 8 in-process adapter cannot forcibly terminate arbitrary Python code that ignores cancellation. Hard process isolation is intentionally left to a future runtime adapter.

## Exception Normalization

Raw handler exceptions do not cross the runtime boundary.

Baseline mappings include:

```text
RuntimeDependencyUnavailable -> DEPENDENCY_UNAVAILABLE / retryable
RuntimeProviderError          -> PROVIDER_ERROR / retryable
RuntimeToolError              -> TOOL_ERROR
RuntimeTimeout                -> TIMEOUT / TIMED_OUT
RuntimeCancelled              -> CANCELLED / CANCELLED
RuntimeLimitExceeded          -> POLICY_BLOCKED / BLOCKED
RuntimeValidationError        -> VALIDATION_ERROR
unexpected exception          -> EXECUTION_ERROR
```

Runtime-generated results preserve the request correlation fields required by Agent Contract v1.

Returned handler results are also checked for correlation consistency before they are accepted.

## Resource Limits

In-process handlers may report controlled resource consumption through:

```text
control.consume("tool_calls", amount)
control.consume("tokens", amount)
control.consume("sources", amount)
control.consume("cost", amount)
```

A configured limit is checked before the updated usage value is accepted. Exceeding a limit produces a normalized `BLOCKED` result with `POLICY_BLOCKED` error category.

Recorded runtime usage is attached to `AgentRunResult.metrics.runtime_usage`.

This is a cooperative accounting boundary. Provider-native token, cost, and tool enforcement can be added by later provider/runtime adapters.

## Idempotency

`MemoryIdempotencyStore` is the Phase 8 reference idempotency hook.

For requests with `idempotency_key`:

- a successful result can be replayed without invoking the handler again;
- replay receives the correlation IDs of the new request;
- reuse of the same key with a different input payload is rejected;
- replay is marked with `metadata.idempotent_replay = true`.

The reference store is process-local and not durable across restarts. Durable cross-process idempotency can replace it behind the runtime boundary in a later persistence/infrastructure refinement.

## Health and Availability

Runtime execution updates `AgentRegistry` availability:

```text
AVAILABLE/DEGRADED -> BUSY during execution
SUCCEEDED          -> AVAILABLE
CANCELLED          -> AVAILABLE
BLOCKED            -> AVAILABLE
runtime failure    -> DEGRADED
repeated failures  -> UNAVAILABLE
```

The default unavailability threshold is three consecutive runtime failures and is configurable on `AgentRuntimeDispatcher`.

A later successful run resets the consecutive-failure counter and restores `AVAILABLE`.

## Isolation Boundary

Phase 8 guarantees logical failure isolation at the Agent Contract boundary: handler exceptions, timeout, cancellation, invalid results, and runtime policy failures are represented as normalized `AgentRunResult` statuses and errors.

The reference in-process adapter does not claim OS/process isolation. Stronger isolation belongs to additional `RuntimeAdapter` implementations and does not require Supervisor-core changes.

## Validation

Core Validation on the committed Phase 8 baseline:

```text
Python 3.13.15
46 tests PASS
```

Coverage includes success, exception normalization, timeout, cooperative cancellation, resource limits, idempotency replay/conflict, retry classification, result correlation, and agent health transitions.
