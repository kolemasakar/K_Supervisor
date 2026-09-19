# V0_4_PHASE2_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 2 — Operator Control API.

Version: 1.0
Status: COMPLETE — ACTIVATION PENDING
Date: 2026-09-19
Baseline main: 15e6fa08ef348cb13d15b269110aa60a1cc3f537
Baseline tree: 51b62d79af1391d85a1d53ccdd38027e88caf78c
Predecessor phase: v0.4 Phase 1 COMPLETE
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 2 is limited to the approved ROADMAP v0.4 Operator Control API assignment:

- additive authenticated `/api/v1` owner/operator operations for Project onboarding/registration and ProjectSpec submission/approval/activation;
- Human Intervention and Policy Approval read/owner-decision operations;
- Task/Workflow execution start, status and cancellation through existing or explicitly extended runtime authority;
- release/readiness/target status and owner publication-confirmation;
- redacted recovery/status projections;
- independent domain scopes, restart-safe idempotency and durable command receipts;
- normalized conflict/error semantics and service telemetry.

Explicitly out of Phase 2 scope:

- raw secret retrieval or secret-resolution endpoints;
- direct Tool or Provider invocation endpoints;
- administrator-wide multi-tenant RBAC;
- Phase 3 production service-host/CLI work;
- paid external development resources.

`DEVELOPMENT_RESOURCE_POLICY.md` is authoritative: Phase 2 implementation and validation must remain zero-cost.

## 2. Frozen Predecessor and Current Service Boundary

Current Phase 1 completion main:

```text
main: 15e6fa08ef348cb13d15b269110aa60a1cc3f537
tree: 51b62d79af1391d85a1d53ccdd38027e88caf78c
Phase 1 completion PR: #21
Final exact-head Core Validation: 35440792545 — PASS
Validated Phase 1 regression candidate: 192 passed / 84.86% branch-aware coverage
```

The existing v1 Service/API boundary from v0.3 Phase 5 remains public and must stay backward-compatible:

```text
GET  /api/v1/projects
GET  /api/v1/projects/{project_id}
POST /api/v1/projects/{project_id}/lifecycle-transitions
POST /api/v1/projects/{project_id}/operational-transitions
```

Existing scopes remain valid:

```text
projects:read
projects:lifecycle:write
projects:operational:write
```

Existing WSGI behavior remains a compatibility floor:

- injected Bearer authentication;
- 64 KiB bounded request body;
- UTF-8 JSON request bodies;
- `Cache-Control: no-store`;
- normalized generic internal errors;
- mutation idempotency requirement;
- no service-side bearer-token persistence.

## 3. Authority Inventory

### 3.1 Project onboarding / registration

Available authority:

- `factory.onboarding.build_draft_project_spec()` constructs a validated DRAFT ProjectSpec from onboarding data;
- `ProjectRegistry.register()` registers the authoritative Project and optional ProjectSpec;
- lifecycle transition rules remain in `ProjectLifecycleTransition`.

Audit decision:

- Phase 2 registration must not accept an arbitrary caller-supplied lifecycle/operational state.
- New Project registration must create a fixed safe initial state and advance only through existing authoritative transitions.
- A caller must not be able to create a Project directly in APPROVED, BUILDING, RELEASE_READY or another later lifecycle state.

### 3.2 ProjectSpec submission / approval / activation

Available authority:

- `ProjectRegistry.add_spec()` persists a submitted ProjectSpec;
- `ProjectRegistry.activate_spec()` activates only an APPROVED ProjectSpec;
- `ProjectSpec` validates approval timestamps and protected-access configuration.

Gap:

- there is no authoritative ProjectSpec approval/rejection transition method.
- persisted ProjectSpec resources are currently immutable on ordinary `save_project_spec()`, so the Service API must not rewrite status directly or bypass persistence invariants.

Required Phase 2 lower-layer work:

- introduce an explicit ProjectSpec status-transition authority in the ProjectRegistry/domain layer;
- preserve content immutability while allowing only validated lifecycle metadata transitions;
- define and test allowed approval/rejection/supersession transitions;
- keep activation separate from approval;
- audit every material ProjectSpec status/activation change.

The API must call that authority; it must not manufacture an APPROVED object and write it directly.

### 3.3 Human Intervention

Available authority:

- `HumanInterventionBroker.open()`;
- `verify()`;
- `cancel()`;
- atomic project operational-state handling for blocking actions.

Audit decision:

- read projections may expose safe action identity/type/status/timestamps and required owner action;
- verification/cancellation mutations must call the broker;
- API must not write `HumanActionRequest` records directly;
- a negative owner decision must use an explicit supported domain operation rather than overloading `verify(ok=False)`, which currently leaves the action unchanged.

### 3.4 Policy approvals

Available authority:

- `PolicyApprovalBroker.approve()`;
- `reject()`;
- `expire()`;
- `revoke()`;
- `get_approval()`.

Audit decision:

- owner approval/rejection/revocation endpoints must call the broker;
- service code must not mutate `ApprovalRecord` directly;
- expiry remains time/domain controlled, not a general owner mutation;
- requested protected access may be represented only as opaque `secret://...` references, never resolved values.

### 3.5 Single-capability Task execution

Available authority:

- `SupervisorKernel.run_task()` is the authoritative capability-routing/task execution path;
- it creates Task, WorkflowRun and AgentRun records and routes through the existing dispatcher/policy boundary.

Gaps for the Phase 2 public execution contract:

- `run_task()` is synchronous;
- it has no service-command idempotency parameter for task creation;
- Task status has no CANCELLED state;
- the kernel exposes no authoritative cancel operation;
- a lower runtime adapter may support cancellation, but the Service API must not reach through the kernel and mutate runtime internals directly.

Required Phase 2 lower-layer work:

- add an explicit task execution-control authority for start/status/cancel;
- make cancellation durable and correlation-safe;
- connect active runtime cancellation where supported;
- add terminal cancellation semantics to Task/Workflow state without rewriting history;
- ensure retries/restarts cannot create duplicate tasks for one service command.

### 3.6 Workflow execution

Available authority:

- `WorkflowEngine.start()` and `resume()`;
- `WorkflowDefinition` is a declarative, validated Pydantic graph with bounded `max_steps` and per-node `max_visits`;
- workflow capability nodes ultimately invoke `SupervisorKernel.run_task()`.

Gaps:

- there is no WorkflowRegistry;
- there is no workflow cancellation authority;
- WorkflowExecutionStatus has no CANCELLED state;
- current resume requires the caller to provide a matching definition/version again.

Audit decision:

- Phase 2 may accept a declarative `WorkflowDefinition` in an authenticated start command because it contains no executable Python object and is already structurally validated, subject to the existing HTTP body bound and policy/capability enforcement;
- the start command must persist definition identity/version/hash in authoritative run metadata for restart/reconciliation;
- the API must not expose arbitrary code/callables;
- cancellation must be implemented below the API as an authoritative WorkflowEngine/control-plane operation before a cancellation endpoint is enabled.

A persistent WorkflowRegistry is not required by Phase 2 unless implementation proves it necessary for correct restart/cancellation semantics.

### 3.7 Release/readiness/publication

Available authority:

- persisted `Release`, `ReleaseTarget` and `ReleaseValidationRecord`;
- `ReleaseManager.confirm_publication()`;
- `PublicationHandoff.confirm()` verifies the linked Human Action and records publication state/audit.

Audit decision:

- GET status endpoints must project persisted release/target/validation state and must not trigger publication or remote repository side effects;
- publication-confirmation must delegate to `ReleaseManager.confirm_publication()`;
- project ownership of the release/target must be checked before mutation;
- publication remains explicit owner action; no automatic external publication is introduced.

## 4. Protected Data and Redaction Boundary

Existing `access.validation.validate_access_references()` rejects raw values under sensitive keys such as `api_key`, `client_secret`, `password`, `private_key`, `secret` and `token`; those values must be `secret://...` references.

Phase 2 requirements:

- ProjectSpec submission continues to pass through the existing protected-reference validator;
- no endpoint resolves `AccessReference`;
- response projections may carry opaque reference URIs only where operationally necessary;
- raw secret contents, bearer tokens and resolved provider/repository credentials never enter API response bodies, service command records, telemetry or error messages;
- recovery/status endpoints are explicit projections and must never serialize the full internal `ProjectRecoverySnapshot` wholesale;
- audit/telemetry projections must be allowlisted rather than recursively dumping internal records.

## 5. Idempotency and Durable Command Receipts

Current `ServiceMutationRecord` is intentionally narrow and stores a completed `Project` result. Existing Phase 5 endpoints and persisted records must remain readable/replayable unchanged.

It is insufficient for Phase 2 because new mutations return different domain types and some operations can outlive one local transaction.

Required additive contract:

```text
ServiceCommandRecord
  command_id
  project_id
  api_version
  operation
  idempotency_key
  request_signature
  status: PENDING | SUCCEEDED | FAILED
  safe result kind/reference(s)
  normalized safe error code/category when failed
  created_at / updated_at / completed_at
```

Rules:

- do not store full request payloads when a signature is sufficient;
- never store secret contents;
- same operation/key/signature replays or reconciles the authoritative result;
- same key with a different signature is `IDEMPOTENCY_CONFLICT`;
- command claim occurs before non-transactional/long-running material work;
- completed local-only mutations may commit domain state + command completion atomically;
- execution commands must not hold a SQLite write transaction across provider/tool/runtime work;
- orphaned PENDING commands after restart must reconcile against durable Task/Workflow/Release/HumanAction state by correlation references;
- legacy `ServiceMutationRecord` remains supported for the four existing Phase 5 routes.

Because SQLite uses generic `resources(kind, ... payload ...)`, a new resource kind can be additive without a physical table-layout change. A schema-version bump is not required unless implementation introduces a physical SQL-layout change. Backup/restore/upgrade tests remain mandatory for any actual schema/config migration.

## 6. Proposed Additive v1 Route Surface

The audit authorizes design/implementation of the following route families after a separate activation gate; exact naming may be adjusted only if semantics remain equivalent and backward-compatible.

```text
POST /api/v1/projects
GET  /api/v1/projects/{project_id}/specs
POST /api/v1/projects/{project_id}/specs
POST /api/v1/projects/{project_id}/specs/{project_spec_id}/approve
POST /api/v1/projects/{project_id}/specs/{project_spec_id}/reject
POST /api/v1/projects/{project_id}/specs/{project_spec_id}/activate

GET  /api/v1/projects/{project_id}/human-actions
POST /api/v1/projects/{project_id}/human-actions/{human_action_id}/verify
POST /api/v1/projects/{project_id}/human-actions/{human_action_id}/cancel

GET  /api/v1/projects/{project_id}/approvals
POST /api/v1/projects/{project_id}/approvals/{approval_id}/approve
POST /api/v1/projects/{project_id}/approvals/{approval_id}/reject
POST /api/v1/projects/{project_id}/approvals/{approval_id}/revoke

GET  /api/v1/projects/{project_id}/tasks
GET  /api/v1/projects/{project_id}/tasks/{task_id}
POST /api/v1/projects/{project_id}/tasks
POST /api/v1/projects/{project_id}/tasks/{task_id}/cancel

GET  /api/v1/projects/{project_id}/workflows
GET  /api/v1/projects/{project_id}/workflows/{workflow_run_id}
POST /api/v1/projects/{project_id}/workflows
POST /api/v1/projects/{project_id}/workflows/{workflow_run_id}/cancel

GET  /api/v1/projects/{project_id}/releases
GET  /api/v1/projects/{project_id}/releases/{release_id}
GET  /api/v1/projects/{project_id}/recovery-status
POST /api/v1/projects/{project_id}/releases/{release_id}/targets/{target_type}/confirm-publication
```

No direct `/tools`, `/providers`, `/secrets` or raw recovery-snapshot route is authorized.

## 7. Scope Model

Existing scopes remain unchanged. Phase 2 must use independent least-privilege scopes rather than one broad write permission.

Planned scope families:

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

A mutation scope must not imply read permission or another mutation scope unless explicitly documented. Existing Phase 5 independent-scope behavior remains the compatibility precedent.

## 8. Error and Ownership Contract

Phase 2 must preserve the current normalized envelope and add typed errors as needed without exposing internal tracebacks.

Required categories include:

```text
AUTH_REQUIRED
ACCESS_DENIED
NOT_FOUND
INVALID_REQUEST
INVALID_TRANSITION
IDEMPOTENCY_REQUIRED
IDEMPOTENCY_CONFLICT
COMMAND_IN_PROGRESS
PROJECT_NOT_RUNNABLE
EXECUTION_NOT_CANCELLABLE
OWNER_ACTION_INVALID
APPROVAL_STATE_CONFLICT
RELEASE_STATE_CONFLICT
INTERNAL_ERROR
```

Every nested resource route must verify `resource.project_id == route project_id` before read/mutation. Cross-project identifiers must fail as NOT_FOUND or an equivalent non-leaking result rather than mutate another project.

## 9. Telemetry and Audit

Service telemetry remains best-effort and may not corrupt authoritative state.

Phase 2 must add safe operation/correlation attributes for new routes while excluding request bodies, bearer tokens, raw ProjectSpec protected material and provider/repository secrets.

Material mutations must retain authoritative domain audit from their lower-layer authority. The Service API may add service-command correlation evidence but must not replace or duplicate domain authority audit semantics.

## 10. Zero-Cost Validation Plan

Phase 2 requires no paid provider or hosted service.

Authoritative validation uses:

- local SQLite;
- direct `ServiceApiV1` tests;
- stdlib WSGI adapter tests;
- deterministic agent/runtime/workflow fixtures;
- deterministic release/repository fixtures;
- local restart/reopen tests;
- fake/no-network side-effect providers where execution paths require a provider.

No Phase 2 acceptance criterion may require OpenAI credits, paid cloud infrastructure or another paid external dependency.

## 11. Required Test Families

Phase 2 implementation must add deterministic tests covering:

- all existing v0.3 Phase 5 API tests unchanged;
- registration safe initial state and duplicate/conflict behavior;
- ProjectSpec plaintext-secret rejection, immutable content, status transition authority, approval/rejection/activation;
- per-domain scope denial before mutation;
- Human Action verify/cancel and linked operational-state semantics;
- approval approve/reject/revoke through `PolicyApprovalBroker`;
- task/workflow start, status and cancellation through authoritative control paths;
- no direct provider/tool invocation route;
- execution command idempotency, crash/restart reconciliation and no duplicate Task/Workflow creation;
- release/target/readiness status projection and publication-confirmation idempotency;
- cross-project resource-ID isolation;
- redacted recovery/status projection;
- service command PENDING/SUCCEEDED/FAILED persistence and replay;
- telemetry redaction/failure isolation;
- malformed/oversized/unauthorized WSGI requests fail closed;
- cumulative regression, branch-aware coverage >=80%, ResourceWarning-as-error, compileall, isolated wheel build/install and public CLI/import smoke.

## 12. Implementation Order Guard

After a separate owner-approved activation gate, Phase 2 implementation should proceed in this order:

1. additive domain prerequisites: ProjectSpec status authority, cancellation state/control authority, generic service command receipt;
2. read projections and independent scope constants/contracts;
3. Project/ProjectSpec routes;
4. Human Action/Approval routes;
5. Task/Workflow start/status/cancel routes;
6. Release/recovery status and publication-confirmation routes;
7. WSGI/telemetry/docs integration;
8. full Phase 2 + cumulative validation.

The Service API must remain a thin orchestration boundary; business-state rules stay below it.

## 13. Audit Outcome

The existing architecture is suitable for additive Phase 2 work, but implementation must first close the explicitly identified lower-layer authority gaps. None requires paid resources or a Phase 3 service host.

Audit result:

```text
Phase 1: COMPLETE
Phase 2 audit: COMPLETE
Phase 2 activation: NO / PENDING OWNER APPROVAL
Phase 2 runtime implementation authorized: NO
Phase 3-7: INACTIVE / PLANNED
```

This document does not activate Phase 2. Runtime changes may begin only after an explicit Phase 2 activation checkpoint is approved and merged through protected `main` with required `Core Validation`.
