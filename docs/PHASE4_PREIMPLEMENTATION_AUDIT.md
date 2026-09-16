# PHASE4_PREIMPLEMENTATION_AUDIT
Pre-implementation audit for ROADMAP v0.3 Phase 4 - Runtime Isolation & Cancellation.

Version: 1.0
Status: COMPLETE
Date: 2026-09-16
Baseline main: 84b2f5cd218b7b02d9412638c4325e2151f1e03a
Validated predecessor runtime: 6868d595b66a6ada91a2e6f2f62866721d0f3560

## Scope

Phase 4 is limited to the runtime boundary assigned by `HARDENING_BASELINE_V0_3.md` and `TEST_MATRIX.md`: stronger execution isolation, bounded termination, cancellation escalation, timeout enforcement, worker/process crash containment and normalized runtime failure handling.

## Existing Runtime Boundary

`AgentRuntimeDispatcher` already owns normalized runtime results, cancellation lookup by `run_id`, idempotency, health updates and correlation validation. `RuntimeAdapter` is already replaceable, so Supervisor and Workflow contracts do not need to change.

`InProcessRuntimeAdapter` executes handlers in `ThreadPoolExecutor`. On timeout it sets cooperative cancellation and calls `future.cancel()`, but Python cannot forcibly stop a running thread. A handler that ignores `ExecutionControl.check_cancelled()` may therefore continue after the dispatcher has returned `TIMED_OUT` or after cancellation is requested.

## Gaps Assigned to Phase 4

- no OS/process execution boundary for Agent handlers;
- no parent-enforced termination of an unresponsive handler;
- no escalation from cooperative cancellation to terminate/kill;
- no normalized worker-process crash result;
- no bounded worker cleanup guarantee before isolated execution returns.

## Preserved Boundaries

Phase 4 must not redesign Supervisor orchestration, Workflow Engine, Agent contracts, policy/approval, SideEffectGateway, persistence schema, service/API boundaries, extension trust/governance or production telemetry/exporters.

`InProcessRuntimeAdapter` remains available for compatibility and trusted development scenarios. The hardened isolated adapter must fit the existing `RuntimeAdapter` contract.

## Implementation Decision

Add a process-isolated runtime adapter that starts one worker process per invocation, mirrors the existing handler-registration shape, propagates runtime limits into a child `ExecutionControl`, and keeps timeout/cancellation authority in the parent process.

Parent-side enforcement will request cooperative cancellation first, then terminate, then kill if required, with bounded joins. A worker exit without a valid result/error envelope is normalized as a worker crash. Child `AgentRuntimeError` semantics and cooperative resource-limit errors remain normalized through the existing dispatcher boundary.

## Verification Required

- unresponsive worker cannot outlive timeout cleanup;
- cancellation of an unresponsive worker escalates and returns `CANCELLED` within a bounded interval;
- worker crash does not crash the supervisor/test process and returns normalized failure;
- child runtime errors preserve normalized status/category semantics;
- successful isolated execution preserves correlation and returns the normal result;
- all predecessor tests and permanent Core Validation gates remain green.
