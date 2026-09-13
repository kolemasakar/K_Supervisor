# POLICY_AND_PERMISSIONS
Політика контрольованої автономності, дозволів, ризику та явного погодження у K_Supervisor.

Version: 1.0
Status: ACTIVE
Phase: 11

## 1. Purpose

Phase 11 places a deterministic policy boundary before controlled execution.

The core rule is:

```text
resolve policy -> decide -> audit -> execute only if ALLOW
```

Agents do not decide their own permissions and cannot silently broaden the permissions supplied by the platform.

## 2. Policy Effects

Every evaluation returns exactly one effect:

```text
ALLOW
DENY
REQUIRE_APPROVAL
```

`DENY` and `REQUIRE_APPROVAL` are represented to orchestration as a normalized `BLOCKED` AgentRunResult with error category `POLICY_BLOCKED`. The downstream dispatcher is not called unless the decision is `ALLOW`.

## 3. Trusted Declarations

Capability risk and side effects come from the registered `CapabilityDescriptor`, not from caller-provided request data.

Supported risk classes:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Supported side effects:

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

A request may narrow declared side effects. It cannot request effects that the capability did not declare.

## 4. Project Policy

Project policy is resolved from the active approved ProjectSpec:

```text
ProjectSpec.autonomy.policy
```

The baseline machine policy supports:

- capability allow/deny constraints;
- allowed, approval-required, and denied side effects;
- per-agent tool/operation permissions;
- allowed protected access references;
- risk classes that require approval.

Default behavior permits `NONE` and `READ_EXTERNAL`; material side effects require approval by default. `HIGH` and `CRITICAL` capabilities require approval by default.

## 5. Workflow Constraints

A workflow may provide an additional policy overlay in `workflow_constraints`.

The overlay is restrictive only. It may narrow project permissions but may not expand them.

Examples:

- capability allowlists are intersected;
- allowed side effects are intersected;
- denied side effects are accumulated;
- per-agent tool permissions are intersected;
- access-reference allowlists are intersected;
- approval requirements may be strengthened, not weakened.

## 6. Per-Agent Tool Permissions

Tool permissions are scoped by both agent and operation.

Logical form:

```text
agent.policy:
  repo.read: [read]
  repo.write: [write]
```

`PolicyEngine` rejects requested tool operations outside the resolved scope. The resulting least-privilege context contains only the tool operations actually authorized for the run.

`require_tool_operation()` is the Phase 11 enforcement helper for tool invocation boundaries. A universal runtime Tool Gateway is not claimed by this phase; later runtime integration may centralize this helper without changing the policy contract.

## 7. Protected Access References

Policy never places plaintext secrets into execution policy.

Only canonical protected references may be authorized:

```text
secret://<scope>/<name>
```

`allowed_access_refs` defines the project-level reference scope. Workflow policy may narrow it. `require_access_reference()` checks a concrete reference against the resolved least-privilege execution context before secret resolution or tool use.

Phase 10 remains responsible for resolving protected references through a replaceable SecretBackend.

## 8. Least-Privilege Execution Context

An `ALLOW` decision produces a `LeastPrivilegeExecutionContext` containing only:

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

`PolicyEnforcedDispatcher` replaces the broad request policy with this resolved context before passing the request to the actual AgentDispatcher.

This creates a deterministic boundary between project/workflow policy and executable agent context.

## 9. Approval Gate

Material permission expansion produces `REQUIRE_APPROVAL`.

`PolicyApprovalBroker` creates a durable `ApprovalRecord` and a blocking `HumanActionRequest`. The affected project enters `WAITING_FOR_OWNER` through the existing Human Intervention Broker.

Notification delivery is not approval:

```text
NOTIFICATION_SENT != POLICY_APPROVED
```

Execution can continue only after the matching ApprovalRecord is explicitly `APPROVED`.

Approval is bound to a deterministic SHA-256 scope containing:

- project;
- agent;
- capability and capability version;
- operation;
- risk class;
- side effects;
- tool permissions;
- protected access references.

Equivalent future tasks may reuse an approved exact scope. A different permission scope does not inherit that approval. Rejected scopes remain rejected and do not repeatedly create new approval prompts.

Approval expiry and revocation are not claimed by Phase 11.

## 10. Failure Safety

Approval state and project operational state are persisted separately, but ordering is conservative:

- approval resumes the project before the ApprovalRecord becomes `APPROVED`;
- rejection resolves the owner wait before the ApprovalRecord becomes `REJECTED`.

If a process stops between those writes, authorization does not become broader: the permission remains non-approved until the durable approval record is written.

## 11. Policy Audit

Every policy evaluation produces a structured `PolicyDecision` containing:

- decision ID;
- project/request identity;
- effect;
- stable reason code and reason;
- risk class;
- timestamp;
- resolved least-privilege context when allowed;
- approval reference when applicable;
- scope metadata.

Production composition uses `PersistencePolicyAuditSink`. SQLite stores policy decisions as append-only events, so decisions survive process restart without storing hidden chain-of-thought.

## 12. Orchestration Semantics

Policy blocking is distinct from execution failure.

The Supervisor preserves a policy-blocked result as:

```text
AgentRunResult: BLOCKED
Task: BLOCKED
WorkflowRun: BLOCKED
```

A prohibited operation therefore does not become an execution error and is not retried as a transient provider failure.

## 13. Production Composition

Controlled execution is composed as:

```text
SupervisorKernel
    -> PolicyEnforcedDispatcher
        -> PolicyEngine
        -> Policy audit
        -> optional PolicyApprovalBroker
        -> AgentDispatcher / AgentRuntimeDispatcher only when ALLOW
```

This preserves existing AgentDispatcher replaceability while adding a mandatory controlled-autonomy layer for production composition.

## 14. Non-Goals of Phase 11

Phase 11 does not implement:

- a universal centralized Tool Gateway;
- approval expiry or revocation;
- organization-wide RBAC/ABAC administration UI;
- cryptographic signing of approvals;
- provider-specific authorization systems;
- hidden reasoning audit.

These can be added behind the current policy contracts without broadening agent authority by default.
