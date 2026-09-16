# POLICY_AND_PERMISSIONS
Політика контрольованої автономності, дозволів, ризику та явного погодження у K_Supervisor.

Version: 1.2
Status: ACTIVE
Baseline: v0.3 Phase 3 implementation
Date: 2026-09-16

## 1. Purpose

The policy boundary resolves project/workflow constraints before controlled execution.

Core rule:

```text
resolve policy -> decide -> audit -> execute only if ALLOW
```

Agents do not decide or broaden their own permissions.

## 2. Policy Effects

Every evaluation returns one of:

```text
ALLOW
DENY
REQUIRE_APPROVAL
```

`DENY` and `REQUIRE_APPROVAL` remain normalized orchestration blocking states; downstream execution is not called unless the decision is `ALLOW`.

## 3. Trusted Capability Declarations

Risk and side effects come from the registered `CapabilityDescriptor`, not caller-provided data.

Risk classes:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Side effects:

```text
NONE
READ_EXTERNAL
WRITE_EXTERNAL
SEND_MESSAGE
CREATE_RESOURCE
MODIFY_RESOURCE
DELETE_RESOURCE
EXECUTE_CODE
```

A request may narrow declared effects but cannot broaden them.

## 4. Project and Workflow Policy

Project policy is resolved from the active approved ProjectSpec. Workflow overlays are restrictive-only and may narrow capability, side-effect, tool-operation and protected-reference scope; they may not expand project authority.

## 5. Tool Permissions and Protected References

Tool operations are scoped by agent/tool/operation. Protected access uses canonical protected references rather than plaintext secrets.

`require_tool_operation()` and `require_access_reference()` remain reusable enforcement helpers. v0.3 Phase 3 invokes them inside the standard `SideEffectGateway` immediately before Tool/Provider resolution/use, so Agent/Workflow callers do not compose authorization independently.

## 6. Least-Privilege Execution Context

An ALLOW decision contains only the resolved scope:

```text
project_id
agent_id
capability_id
operation
side_effects
tool_permissions
access_refs
approval_id
```

Production policy dispatch attaches this authoritative least-privilege context before execution. Original requested policy fields may remain only as input for deterministic re-evaluation; downstream authority comes from the resolved execution context, not from caller-provided scope.

## 7. Approval Scope

Material permission expansion produces `REQUIRE_APPROVAL`. `PolicyApprovalBroker` creates a durable `ApprovalRecord` and blocking `HumanActionRequest`.

Approval remains bound to deterministic permission scope containing project, agent, capability/version, operation, risk, side effects, tool permissions and protected references.

Notification delivery is not approval:

```text
NOTIFICATION_SENT != POLICY_APPROVED
```

## 8. Approval Lifecycle

Current durable states:

```text
PENDING
APPROVED
REJECTED
EXPIRED
REVOKED
```

Optional `expires_at` may be assigned when the approval request is created.

Rules:

- PENDING can become APPROVED, REJECTED or EXPIRED;
- APPROVED can expire after `expires_at` or be explicitly REVOKED;
- REJECTED, EXPIRED and REVOKED records are not treated as active permission;
- an expired/revoked/rejected exact scope may later create a new approval request instead of permanently reusing the old record;
- revocation requires an explicit non-empty reason;
- policy evaluation returns `APPROVAL_EXPIRED` or `APPROVAL_REVOKED` and requires fresh approval rather than silently allowing execution.

Existing historical approval records remain valid because new expiry/revocation fields default to `None`.

## 9. Human Intervention Interaction

A blocking approval request uses Human Intervention and moves the project to `WAITING_FOR_OWNER` when required.

- approval verifies the matching HumanAction before authorization becomes APPROVED;
- rejection or pending expiry cancels the matching owner action;
- when no other blockers remain, the project returns to ACTIVE;
- Human Intervention state/project transition/required audit uses the Phase 2 atomic persistence boundary.

Owner action completion and permission state remain explicit durable records.

## 10. Approval Audit

Approval lifecycle mutations generate normalized durable audit events including:

```text
APPROVAL_REQUESTED
APPROVAL_APPROVED
APPROVAL_REJECTED
APPROVAL_EXPIRED
APPROVAL_REVOKED
```

Approval record mutation and its required audit event are committed through the same SQLite transaction boundary.

Phase 2 regression tests explicitly verify durable expiry/revocation audit evidence.

## 11. Policy Decision Audit

Every policy evaluation still produces a durable structured `PolicyDecision` containing decision identity, project/request correlation, effect, reason code, risk, timestamp, least-privilege context when allowed, approval reference and scope metadata.

No hidden chain-of-thought is stored.

## 12. Failure Safety

The platform fails closed for invalid, expired, revoked or missing approvals. Human Intervention and Approval remain separate domain records, but each control-state mutation is persisted with its required normalized audit where defined.

Universal cross-system atomicity is not claimed. Phase 3 centralizes the external side-effect invocation boundary; distributed transaction guarantees remain out of scope.

## 13. Orchestration Semantics

Policy blocking remains distinct from execution failure:

```text
AgentRunResult: BLOCKED
Task: BLOCKED
WorkflowRun: BLOCKED
```

A prohibited operation is not converted into a transient provider failure.

## 14. Production Composition

Current controlled execution composition:

```text
SupervisorKernel
    -> PolicyEnforcedDispatcher
        -> PolicyEngine
        -> durable PolicyDecision audit
        -> optional PolicyApprovalBroker
        -> AgentDispatcher / AgentRuntimeDispatcher only when ALLOW
```

Phase 3 adds `SideEffectGateway` underneath the approved execution context. The gateway evaluates policy at the invocation boundary, requires `ALLOW`, validates correlation and least-privilege tool/access scope, then invokes the replaceable Tool/Provider adapter. `PolicyEnforcedDispatcher` preserves the original requested permission/approval fields when attaching the authoritative ALLOW context so the gateway can re-evaluate the same scope.

A blocked gateway decision is not an adapter failure: `DENY` and `REQUIRE_APPROVAL` never reach the external adapter. Allowed attempts/outcomes receive durable normalized side-effect audit through the persistence boundary.

## 15. Validation Baseline

Authoritative Phase 2 baseline:

```text
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Core Validation run: 34808287772
pytest: 103 passed
branch-aware coverage: 85.23%
ResourceWarning gate: PASS
```

Approval expiry, revocation, audit persistence and restart recovery are covered by v0.3 Phase 2 tests while all Phase 11 predecessor policy tests remain green.

## 16. Current Non-Goals

Not yet implemented here:

- organization-wide RBAC/ABAC administration UI;
- cryptographic approval signing;
- provider-specific authorization administration;
- arbitrary untrusted Python sandboxing;
- hidden reasoning audit.
