# SERVICE_API
Versioned Service/API boundary for K_Supervisor owner/operator control.

Version: 2.1
Status: ACTIVE
Baseline: v0.4 Phase 3 implementation candidate
Date: 2026-09-19
Public API version: v1

## 1. Purpose

`ServiceApiV1` is the supported versioned owner/operator boundary over the existing K_Supervisor control plane. It remains a thin orchestration layer: lifecycle rules, ProjectSpec state, Human Intervention, Policy Approval, execution and release/publication authority stay in their domain services.

Phase 3 supplies the single-node hosting/client boundary around this API while preserving all v1 business semantics. TLS certificate lifecycle remains external.

## 2. Public Boundary

```text
API version: v1
Base path: /api/v1
Python facade: ksupervisor.service
Transport-neutral service: ServiceApiV1
HTTP adapter: WsgiServiceAppV1
```

`WsgiServiceAppV1` keeps the existing standard-library transport contract:

- injected authentication;
- bounded 64 KiB request body;
- UTF-8 JSON;
- `Cache-Control: no-store`;
- no bearer-token persistence;
- normalized error envelopes.

## 3. Legacy Compatibility Routes

The v0.3 Phase 5 surface remains unchanged:

```text
GET  /api/v1/projects
GET  /api/v1/projects/{project_id}
POST /api/v1/projects/{project_id}/lifecycle-transitions
POST /api/v1/projects/{project_id}/operational-transitions
```

Legacy scopes remain valid and independent:

```text
projects:read
projects:lifecycle:write
projects:operational:write
```

Legacy mutations continue to use immutable `ServiceMutationRecord` receipts and existing ProjectRegistry lifecycle authority.

## 4. Phase 2 Additive Routes

### Project and ProjectSpec

```text
POST /api/v1/projects
GET  /api/v1/projects/{project_id}/specs
POST /api/v1/projects/{project_id}/specs
POST /api/v1/projects/{project_id}/specs/{project_spec_id}/approve
POST /api/v1/projects/{project_id}/specs/{project_spec_id}/reject
POST /api/v1/projects/{project_id}/specs/{project_spec_id}/activate
```

Registration always creates a safe initial Project state:

```text
lifecycle_state = IDEA
operational_state = ACTIVE
ProjectSpec status = DRAFT
```

The client cannot choose an arbitrary initial lifecycle state. ProjectSpec approval/rejection uses `ProjectRegistry` status-transition authority; activation remains a separate operation.

### Human Action and Policy Approval

```text
GET  /api/v1/projects/{project_id}/human-actions
POST /api/v1/projects/{project_id}/human-actions/{human_action_id}/verify
POST /api/v1/projects/{project_id}/human-actions/{human_action_id}/cancel

GET  /api/v1/projects/{project_id}/approvals
POST /api/v1/projects/{project_id}/approvals/{approval_id}/approve
POST /api/v1/projects/{project_id}/approvals/{approval_id}/reject
POST /api/v1/projects/{project_id}/approvals/{approval_id}/revoke
```

Human Action mutations delegate to `HumanInterventionBroker`. Policy Approval mutations delegate to `PolicyApprovalBroker`; approval expiry remains domain/time controlled rather than a general owner endpoint.

### Task and Workflow execution

```text
GET  /api/v1/projects/{project_id}/tasks
GET  /api/v1/projects/{project_id}/tasks/{task_id}
POST /api/v1/projects/{project_id}/tasks
POST /api/v1/projects/{project_id}/tasks/{task_id}/cancel

GET  /api/v1/projects/{project_id}/workflows
GET  /api/v1/projects/{project_id}/workflows/{workflow_run_id}
POST /api/v1/projects/{project_id}/workflows
POST /api/v1/projects/{project_id}/workflows/{workflow_run_id}/cancel
```

Task start accepts a `CapabilityRequirement` plus bounded JSON input/context/policy/limits and delegates to `SupervisorKernel.run_task()`.

Workflow start accepts a declarative validated `WorkflowDefinition`; no callable or executable Python object crosses the API. The persisted WorkflowRun carries definition version/hash identity. Status projections omit workflow input/context.

Task/Workflow cancellation is durable. Active runtime cancellation is requested through the existing runtime dispatcher when available; CANCELLED state cannot be overwritten by a late success.

### Release and recovery status

```text
GET  /api/v1/projects/{project_id}/releases
GET  /api/v1/projects/{project_id}/releases/{release_id}
POST /api/v1/projects/{project_id}/releases/{release_id}/targets/{target_type}/confirm-publication
GET  /api/v1/projects/{project_id}/recovery-status
```

Publication confirmation delegates to `ReleaseManager.confirm_publication()`. It confirms an already owner-performed publication action; the API does not automatically publish externally.

Recovery status is an explicit allowlisted projection. The full internal `ProjectRecoverySnapshot` is never returned.

## 5. Phase 2 Scopes

All scopes are independent; mutation permission does not imply read permission or another write domain.

```text
projects:register

project-specs:read
project-specs:submit
project-specs:approve
project-specs:activate

human-actions:read
human-actions:verify

approvals:read
approvals:decide

executions:read
executions:start
executions:cancel

releases:read
releases:publication:confirm

recovery:read
```

Legacy Phase 5 scopes remain unchanged.

## 6. Protected Data Boundary

The Service/API never resolves protected references.

ProjectSpec submission passes through the existing access-reference validation. Sensitive configuration keys such as API keys, passwords, private keys, secrets or tokens must contain `secret://...` references rather than raw access material.

Rules:

- raw secret contents never enter API responses;
- bearer tokens are not persisted by the service;
- `ServiceCommandRecord` stores canonical request signatures and safe result references, not request bodies;
- workflow status never serializes workflow input/context;
- recovery status uses allowlisted summaries/counters;
- no direct secret-resolution route exists.

Opaque `secret://...` reference URIs may remain in an explicitly requested ProjectSpec representation; they are references, not resolved secret contents.

## 7. Idempotency and Durable Command Receipts

Every POST mutation requires `Idempotency-Key`.

Two compatible receipt families exist.

### Legacy Project mutation receipt

`ServiceMutationRecord` remains authoritative for the original lifecycle/operational transition routes.

### Phase 2 generic command receipt

`ServiceCommandRecord` supports:

```text
PENDING
SUCCEEDED
FAILED
```

It persists:

- project/API/operation/idempotency scope;
- canonical request signature;
- safe result kind/reference identifiers;
- normalized safe failure code/category/status where applicable;
- timestamps.

It does not persist the request body.

Rules:

- same operation/key/signature -> replay/reconcile authoritative durable state;
- same operation/key with a different signature -> `IDEMPOTENCY_CONFLICT`;
- local-only mutations can commit domain state + successful command completion in one SQLite transaction;
- execution commands claim PENDING before runtime work and do not hold a SQLite transaction across provider/tool/runtime execution;
- terminal durable Task/Workflow state can reconcile an interrupted command after restart;
- stale nonterminal execution is cancelled/fails closed instead of being blindly re-executed;
- concurrent in-process duplicate command claims return `COMMAND_IN_PROGRESS`.

## 8. Authoritative Mutation Boundaries

```text
Project lifecycle           -> ProjectRegistry
ProjectSpec status/activate -> ProjectRegistry
Human Action                -> HumanInterventionBroker
Policy Approval             -> PolicyApprovalBroker
Task execution/cancel       -> SupervisorKernel
Workflow execution/cancel   -> WorkflowEngine
Publication confirmation    -> ReleaseManager
```

The Service/API does not directly rewrite these domain records to manufacture state transitions.

## 9. Error Contract

The existing v1 error envelope remains:

```json
{
  "api_version": "v1",
  "error": {
    "code": "...",
    "message": "..."
  }
}
```

Supported normalized errors include predecessor errors plus Phase 2 additions:

```text
AUTH_REQUIRED              401
ACCESS_DENIED              403
NOT_FOUND                  404
INVALID_REQUEST            400
INVALID_TRANSITION         409
IDEMPOTENCY_REQUIRED       400
IDEMPOTENCY_CONFLICT       409
COMMAND_IN_PROGRESS        409
PROJECT_NOT_RUNNABLE       409
EXECUTION_NOT_CANCELLABLE  409
EXECUTION_INTERRUPTED      409
OWNER_ACTION_INVALID       409
APPROVAL_STATE_CONFLICT    409
RELEASE_STATE_CONFLICT     409
DEPENDENCY_UNAVAILABLE     503
METHOD_NOT_ALLOWED         405
INTERNAL_ERROR             500
```

Unexpected exceptions become generic `INTERNAL_ERROR`; internal traceback/private provider content is not returned.

## 10. Project Isolation

Every nested resource operation validates that the resource belongs to the route `project_id` before read or mutation. A resource identifier from another project fails closed rather than mutating cross-project state.

## 11. Explicit Non-Surface

Phase 2 does not expose:

```text
/tools
/providers
/secrets
raw ProjectRecoverySnapshot
raw secret retrieval
direct Tool invocation
direct Provider invocation
arbitrary executable workflow code
administrator-wide multi-tenant RBAC
automatic external publication
```

## 12. Validation Baseline

Phase 2 implementation candidate:

```text
Implementation PR: #24
Validated head: d6503d9a0a3f64ee14a003c22e61c03a1bfdf960
Validated tree: c5ccce4e3ad93de69e16d55bd441bf934e7e92cc
Core Validation: 35443466438 — PASS
Python: 3.13
pytest: 210 passed
branch-aware coverage: 83.12%
coverage gate >=80%: PASS
ResourceWarning-as-error: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

The exact final PR head including synchronized documentation must pass protected `Core Validation` before Phase 2 completion merge.

## 13. Phase 3 Hosting Boundary

The Phase 2 versioned operator surface remains authoritative. Phase 3 adds only operational transport/composition infrastructure:

```text
ServiceRuntime
  -> one authoritative SQLite/control-plane composition
  -> StaticBearerAuthenticator from protected token references
  -> WsgiServiceAppV1
  -> bounded ServiceHost

ServiceClientV1
  -> /api/v1 over HTTP(S)
  -> operator CLI
```

The host adds `GET /healthz` and `GET /readyz` as minimal unauthenticated operational probes outside the business API. Readiness becomes false during drain. The host bounds worker count and socket timeout, preserves the 64 KiB WSGI request-body limit, stops new application requests before resource close, and leaves in-flight material outcomes to existing Service/API durability/idempotency authority.

The safe default bind is loopback. Non-loopback binding requires explicit proxy mode and trusted proxy address/CIDR configuration. Forwarded headers are ignored by default; in proxy mode, only trusted peers may supply forwarding data and `X-Forwarded-Proto` must indicate HTTPS. Certificate issuance/renewal remains external.

The reusable `ServiceClientV1` contains transport logic only. Operator CLI mutation commands call this client, never persistence/registry/kernel/workflow mutation authorities. Plaintext bearer tokens are not CLI arguments; client and host credentials resolve from protected references/environment injection.

The installed-wheel Core Validation smoke runs outside the checkout and verifies host startup, health/readiness, authenticated CLI-over-HTTP access, clean shutdown and SQLite integrity.
