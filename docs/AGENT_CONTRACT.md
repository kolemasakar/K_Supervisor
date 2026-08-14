# AGENT_CONTRACT
Єдиний версійований контракт реєстрації, виклику, виконання та результатів агентів у K_Supervisor.

Version: 0.1
Status: ACTIVE
Phase: 0

## 1. Purpose

The Agent Contract defines how Supervisor and the platform runtime interact with any executable agent.

The contract is domain-neutral and implementation-neutral.

Core execution form:

```text
AgentRunRequest -> execute -> AgentRunResult
```

## 2. Contract Goals

The contract must provide:

- stable agent identity;
- versioned compatibility;
- declared capabilities;
- schema-bounded input and output;
- explicit execution context;
- policy and resource limits;
- normalized status and errors;
- cancellation and timeout semantics;
- audit metadata;
- replaceability of implementations.

## 3. Agent Descriptor

Every registered agent exposes an AgentDescriptor.

Baseline fields:

```text
agent_id
agent_type
agent_version
contract_version
display_name
capabilities[]
execution_mode
status
metadata
```

Example:

```json
{
  "agent_id": "research.web.default",
  "agent_type": "RESEARCH",
  "agent_version": "1.0.0",
  "contract_version": "1.0",
  "display_name": "Default Web Research Agent",
  "capabilities": ["research.web"],
  "execution_mode": "LOCAL",
  "status": "AVAILABLE",
  "metadata": {}
}
```

## 4. Identity Rules

- `agent_id` is unique within one registry namespace.
- `agent_version` identifies implementation behavior relevant to compatibility.
- `contract_version` identifies the Agent Contract version supported by the implementation.
- `agent_type` is descriptive and may support operational grouping, but routing should prefer capabilities.
- an agent may expose multiple capabilities.

## 5. AgentRunRequest

Every execution receives a structured request envelope.

Required baseline fields:

```text
request_id
task_id
workflow_run_id
run_id
agent_id
capability_id
operation
input
context
policy
limits
idempotency_key
metadata
```

Logical example:

```json
{
  "request_id": "REQ_000001",
  "task_id": "TASK_000001",
  "workflow_run_id": "WF_000001",
  "run_id": "RUN_000001",
  "agent_id": "research.web.default",
  "capability_id": "research.web",
  "operation": "research",
  "input": {},
  "context": {},
  "policy": {},
  "limits": {},
  "idempotency_key": null,
  "metadata": {}
}
```

## 6. Request Semantics

### 6.1 input

Primary work payload. The selected capability defines the expected input schema.

### 6.2 context

Read-only workflow context supplied by the platform unless the capability explicitly allows context mutation through a returned proposal.

Typical context:

```text
iteration
language
prior_run_ids
artifact_refs
workflow_state
approved_profiles
```

### 6.3 policy

Resolved execution policy for this run.

An agent must not silently broaden permissions beyond the supplied policy.

### 6.4 limits

Execution limits may include:

```text
timeout_seconds
max_tool_calls
max_tokens
max_sources
max_cost
max_retries
```

Not every runtime must support every limit in Phase 1, but unsupported limits must be explicit.

### 6.5 idempotency_key

Required when an operation may be retried and can produce external side effects.

The platform must not automatically retry non-idempotent side effects without defined protection.

## 7. AgentRunResult

Every completed invocation returns a normalized result envelope.

Required baseline fields:

```text
request_id
task_id
workflow_run_id
run_id
agent_id
capability_id
status
output
artifacts[]
metrics
error
warnings[]
metadata
```

Logical example:

```json
{
  "request_id": "REQ_000001",
  "task_id": "TASK_000001",
  "workflow_run_id": "WF_000001",
  "run_id": "RUN_000001",
  "agent_id": "research.web.default",
  "capability_id": "research.web",
  "status": "SUCCEEDED",
  "output": {},
  "artifacts": [],
  "metrics": {},
  "error": null,
  "warnings": [],
  "metadata": {}
}
```

## 8. Execution Status

Baseline run statuses:

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
TIMED_OUT
BLOCKED
```

Agent execution status must remain separate from domain-specific conclusions such as PASS, REVISE, APPROVED, REJECTED, VALID, or INVALID.

Those belong inside capability output.

## 9. Error Contract

Normalized error fields:

```text
code
category
message
retryable
details
```

Baseline categories:

```text
VALIDATION_ERROR
POLICY_BLOCKED
DEPENDENCY_UNAVAILABLE
TOOL_ERROR
PROVIDER_ERROR
TIMEOUT
CANCELLED
EXECUTION_ERROR
INTERNAL_ERROR
```

Error messages may be human-readable. `code` must remain stable enough for machine handling.

## 10. Lifecycle

Logical agent lifecycle:

```text
UNREGISTERED
-> REGISTERED
-> AVAILABLE
-> BUSY
-> AVAILABLE

Optional transitions:
AVAILABLE/BUSY -> DEGRADED
AVAILABLE/BUSY/DEGRADED -> UNAVAILABLE
REGISTERED/UNAVAILABLE -> UNREGISTERED
```

Lifecycle state is operational metadata and must not be confused with one run status.

## 11. Cancellation and Timeout

The runtime may request cancellation.

Agents should support cooperative cancellation when their execution mode permits it.

A timeout must return or be normalized to `TIMED_OUT` even if the underlying provider reports another exception type.

## 12. Capability Compliance

An agent may accept a request only when:

- it declares the requested capability;
- the capability version is compatible;
- input validates against the selected capability schema;
- required dependencies are available;
- policy permits execution;
- the agent status allows work.

## 13. Collaboration Boundary

Agents must not require direct imports of other agent implementations.

If additional specialized work is needed, the preferred pattern is to return a structured capability request or emit a platform-recognized delegation request. Supervisor then performs normal discovery and routing.

This preserves replaceability and auditability.

## 14. Side Effects

Capabilities with side effects must declare them.

Examples:

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

The runtime and policy layer may require additional approval for side-effecting operations.

## 15. Security Boundary

An agent receives only the tools, credentials, context, and data required for its run.

Secrets must not be stored inside AgentDescriptor, AgentRunRequest artifacts, or audit logs unless a dedicated secret reference mechanism explicitly permits it.

## 16. Audit Minimum

The platform should be able to record without hidden reasoning:

```text
who executed
what capability was requested
why the candidate was eligible
when execution started and ended
what policy applied
what tools/providers were used
what status resulted
what artifacts were produced
what error occurred
```

## 17. Versioning

Phase 0 defines logical version `0.1` of this document.

Machine contract version `1.0` will be frozen only after Phase 1 schemas and validation tests are implemented.

Breaking contract changes require a major version change or an explicit migration rule.
