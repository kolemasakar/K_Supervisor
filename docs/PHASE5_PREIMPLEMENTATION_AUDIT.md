# PHASE5_PREIMPLEMENTATION_AUDIT
Pre-implementation audit for ROADMAP v0.3 Phase 5 - Service/API Boundary.

Version: 1.0
Status: COMPLETE
Date: 2026-09-16
Baseline main: 33e2db4406bd4fe4cf99de37324600fd525c54fe
Validated predecessor runtime: 34049f601fc8116aa12ee15023f1dc20bc25901a

## Scope

Phase 5 is limited to the hardening assignment in `HARDENING_BASELINE_V0_3.md`, `ROADMAP.md` and `TEST_MATRIX.md`: introduce a controlled versioned Service/API boundary for project lifecycle operations without bypassing the existing control plane. Required verification is limited to API contracts, access control, invalid transitions, idempotent mutations and restart continuity.

Phase 6 production observability, Phase 7 extension trust/governance and Phase 8 operational-readiness work remain out of scope.

## Baseline Verification

Current remote `main` is `33e2db4406bd4fe4cf99de37324600fd525c54fe` and is a descendant of the validated Phase 4 runtime `34049f601fc8116aa12ee15023f1dc20bc25901a`.

The commits after the validated runtime baseline are documentation/README closure and handoff changes only. No later runtime checkpoint exists. Phase 4 validation therefore remains the runtime predecessor baseline: 117 tests passed, 85.13% branch-aware coverage and all permanent Core Validation gates PASS.

## Existing Authoritative Control Plane

`ProjectRegistry` is already the authoritative project state boundary over `PersistenceStore`.

Existing lifecycle/control operations are:

- `ProjectRegistry.get()` and `ProjectRegistry.list()` for current Project state;
- `ProjectRegistry.recover()` for the full project recovery aggregate;
- `ProjectRegistry.transition_lifecycle()` for validated lifecycle transitions plus atomic Project/transition/audit persistence;
- `ProjectRegistry.transition_operational()` for validated operational transitions plus atomic Project/transition/audit persistence;
- `ProjectRegistry.register()`, `add_spec()` and `activate_spec()` for project/spec administration.

Human Intervention, Approval, Project Factory, Workflow, Release Manager and SideEffectGateway remain separate authoritative control paths and are not replaced by an API transport.

## Phase 5 Surface Inventory

The minimum approved v1 service surface is intentionally narrower than all registry capabilities.

Expose:

- list Projects;
- get one Project;
- request one lifecycle transition through `ProjectRegistry.transition_lifecycle()`;
- request one operational transition through `ProjectRegistry.transition_operational()`.

Do not expose in Phase 5:

- Project creation/registration;
- ProjectSpec upload, approval or activation;
- full recovery aggregates;
- Human Intervention/Approval mutation;
- task/workflow execution;
- release/publication mutation;
- Tool/Provider side effects;
- secret resolution or protected-reference contents.

This prevents the service surface from becoming a parallel onboarding, approval, orchestration, release or side-effect path.

## Versioned HTTP Contract

The service contract is versioned as `/api/v1` and implemented as a transport-neutral service core plus a thin WSGI/HTTP adapter using the Python standard library interface. No third-party web framework, deployment server, health/readiness endpoint, metrics exporter or tracing stack is introduced in Phase 5.

Endpoints:

```text
GET  /api/v1/projects
GET  /api/v1/projects/{project_id}
POST /api/v1/projects/{project_id}/lifecycle-transitions
POST /api/v1/projects/{project_id}/operational-transitions
```

Mutation bodies are frozen Pydantic contracts. Responses use a versioned JSON envelope. Errors are normalized into stable codes/statuses rather than exposing internal tracebacks.

## Authentication and Access Control

All v1 endpoints require an authenticated `ServicePrincipal` supplied by an injected authenticator. The HTTP adapter supports Bearer authentication through a host-supplied token-to-principal mapping; credentials are not stored in ProjectSpec, persistence records, response payloads or audit details.

Required scopes:

```text
projects:read
projects:lifecycle:write
projects:operational:write
```

Missing/invalid authentication fails closed with 401. An authenticated principal lacking the required scope fails with 403. Write scope does not implicitly grant read scope, and the API does not synthesize broader project/tool/provider authority.

## Protected-Reference Boundary

Project read responses contain only `Project` fields. Phase 5 does not return ProjectSpec integration/repository/notification/release configuration and never resolves `secret://...` references. Existing protected-reference enforcement remains owned by policy/access and SideEffectGateway paths.

## Idempotency and Atomicity

Every POST mutation requires `Idempotency-Key`.

A durable immutable `ServiceMutationRecord` will store project, API version, operation, idempotency key, canonical request signature, resulting Project snapshot and creation time. The record identifier is deterministic within project/API/operation/key scope.

The persistence contract will expose a generic transaction context so the service can perform, in one backend transaction:

1. lookup/check the idempotency record;
2. invoke the normal `ProjectRegistry` transition method;
3. persist the resulting immutable service mutation record.

Because nested `ProjectRegistry` writes participate in the same persistence transaction, the service does not duplicate state-machine or audit logic. Same key + same signature replays the stored result without a second transition. Same key + different signature fails with an idempotency conflict. This behavior survives supported store/process restart.

## Invalid Transitions and Errors

Lifecycle and operational transition validity remains defined only by the existing domain state models invoked through `ProjectRegistry`; the API does not duplicate allowed-transition tables.

Normalized v1 errors include:

```text
AUTH_REQUIRED        -> 401
ACCESS_DENIED        -> 403
NOT_FOUND            -> 404
INVALID_REQUEST      -> 400
INVALID_TRANSITION   -> 409
IDEMPOTENCY_REQUIRED -> 400
IDEMPOTENCY_CONFLICT -> 409
```

Unexpected internal exceptions return a generic 500 envelope without traceback/details disclosure at the HTTP boundary.

## Restart/Reopen Semantics

Project state, transition/audit history and service mutation records remain SQLite-backed authoritative state. Reopening the same database must preserve current Project state and allow replay of a previously completed idempotent mutation without adding another transition or audit event.

No in-memory session is authoritative for project state or mutation replay.

## Verification Required

Phase 5 tests must prove:

- v1 request/response and normalized error contracts;
- unauthenticated and under-scoped requests fail closed;
- valid lifecycle and operational mutations call the existing `ProjectRegistry` path;
- invalid transitions produce 409 and do not mutate state/history;
- same-key/same-body mutation replay creates no duplicate transition/audit;
- same-key/different-body mutation fails with 409;
- idempotent replay still works after persistence close/reopen;
- HTTP adapter applies Bearer authentication and JSON contract routing;
- all predecessor tests and permanent Core Validation gates remain green.

## Explicit Non-Goals

Phase 5 does not add production service hosting, TLS termination, external identity providers, organization-wide RBAC/ABAC administration, health/readiness/SLO endpoints, metrics/tracing exporters, extension governance, distributed persistence, remote worker orchestration or new project lifecycle semantics.
