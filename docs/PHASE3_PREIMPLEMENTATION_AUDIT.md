# v0.3 Phase 3 Pre-Implementation Audit

Version: 1.0  
Status: COMPLETE  
Audit date: 2026-09-16  
Scope: v0.3 Phase 3 - Centralized Side-Effect Enforcement

## 1. Baseline Verification

The required Phase 2 runtime baseline is:

```text
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Core Validation run: 34808287772
pytest: 103 passed
branch-aware coverage: 85.23%
```

At audit start, `main` was:

```text
main SHA: a7cdbe17d1a33ea056b9ae60ca96398ffeec4fb6
main vs Phase 2 runtime baseline: ahead 18 / behind 0
```

The compare contained only `README.md` and `docs/*`. No runtime/source/test file changed after the validated Phase 2 implementation SHA. Therefore `573cbe433ece8ffae45d83a30fd3287fac40d820` remained the authoritative runtime baseline when Phase 3 implementation began.

A clean local checkout of `main` reproduced the predecessor regression floor with `103 passed` before Phase 3 code changes.

## 2. Existing Enforcement Boundaries

Before Phase 3:

- `PolicyEngine` evaluated capability risk, declared side effects, project/workflow constraints, requested tool permissions, protected-reference scope and approval state.
- `PolicyEnforcedDispatcher` prevented Agent dispatch for `DENY` and `REQUIRE_APPROVAL`.
- `require_tool_operation()` and `require_access_reference()` existed as helpers, but callers had to invoke them correctly.
- `ToolRegistry` and `ProviderRegistry` resolved replaceable concrete adapters.
- `Tool.invoke()` and `Provider.execute()` had no standard platform gateway that combined policy, least privilege, protected references, idempotency and normalized audit at the external invocation boundary.
- Phase 2 durable runtime idempotency protected Agent execution replay, but did not provide an authoritative side-effect attempt/outcome record around external Tool/Provider calls.

This left a composition gap: an allowed Agent could still call a concrete Tool/Provider without a mandatory platform boundary rechecking the least-privilege execution context immediately before the external adapter invocation.

## 3. Material Side-Effect Path Inventory

### 3.1 Agent/workflow Tool and Provider operations

This is the primary Phase 3 target.

Existing contracts:

```text
Tool.invoke(ToolRequest)
Provider.execute(ProviderRequest)
```

Required insertion point:

```text
Agent / Workflow
    -> Supervisor / policy-controlled Agent execution
    -> SideEffectGateway
    -> ToolRegistry / ProviderRegistry
    -> replaceable Tool / Provider adapter
```

The gateway must own the final policy decision, tool-operation permission check, protected-reference authorization, correlation/idempotency propagation and durable attempt/outcome audit before/around the adapter call.

### 3.2 Provider-backed provisioning adapter

`ProviderProvisioningAdapter` is a low-level compatibility adapter that can directly call `Provider.execute()`. The repository audit found no standard production orchestration composition using this class; predecessor tests exercise it as an adapter contract.

Phase 3 therefore preserves this existing low-level API for compatibility rather than changing the Phase 10 provisioning contract. Any standard Agent/Workflow production path that performs provider-backed provisioning must use the new side-effect gateway rather than treating this adapter as an authorization boundary.

### 3.3 Owner notification transport

`NotificationBroker` calls the email transport directly. This is a platform control-plane path for required owner notifications, not an Agent capability permission path. It already has:

- durable notification records;
- durable delivery attempts;
- restart-safe SENT duplicate suppression;
- normalized success/failure audit;
- SMTP as a replaceable transport adapter.

Phase 3 does not replace or weaken this specialized boundary. Email remains the required primary owner-notification transport, and notification delivery remains distinct from owner approval/action completion.

### 3.4 Repository bootstrap and local filesystem preparation

`FilesystemRepositoryAdapter` performs managed local filesystem writes and `git init` during Project Factory bootstrap. This path is already gated by an approved `ProjectSpec`, project lifecycle/operational state, repository target rules, conflict checks and Human Intervention when owner action is required.

It is not a generic Agent Tool/Provider invocation path and is retained unchanged in Phase 3.

### 3.5 Release publication

Automated external publication is not present. `PublicationHandoff` creates an explicit owner action and only records owner confirmation. This owner-controlled boundary remains unchanged.

## 4. Minimum Compatible Phase 3 Contract

Phase 3 introduces:

- `SideEffectGateway` as the standard Agent/Workflow Tool/Provider execution boundary;
- normalized `SideEffectResult`;
- durable `SideEffectExecutionRecord` with project/request/agent/capability/component correlation;
- optional correlation/idempotency fields added compatibly to `ToolRequest` and `ProviderRequest`;
- strict pre-invocation policy and least-privilege checks;
- atomic persistence of side-effect attempt/outcome records with their required audit events;
- durable idempotency claims that suppress repeated supported-path adapter invocation for the same semantic key/signature.

No physical SQLite schema migration is required because the existing generic `resources` / `events` layout can store the new record kind.

## 5. Explicit Non-Goals Preserved

Phase 3 does not add:

- arbitrary third-party Python sandboxing;
- process/container isolation or forced cancellation;
- distributed transactions with external providers;
- universal exactly-once guarantees across remote systems;
- provider-specific authorization administration;
- automatic external publication.

Direct low-level Python adapter calls remain technically possible outside the standard orchestration composition; preventing arbitrary code from bypassing interfaces would require isolation/sandboxing beyond Phase 3 scope.

## 6. Audit Result

The smallest compatible implementation is to insert one enforceable Tool/Provider side-effect gateway underneath the existing policy-controlled Agent execution model, reuse the Phase 11 policy/approval helpers and Phase 2 persistence primitives, preserve specialized control-plane notification/repository/publication boundaries, and add only the Phase 3 contracts/persistence/tests required by `ROADMAP.md` and `TEST_MATRIX.md`.
