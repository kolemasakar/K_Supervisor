# SERVICE_API
Versioned Service/API boundary for K_Supervisor project lifecycle control.

Version: 1.0
Status: ACTIVE
Baseline: v0.3 Phase 5
Date: 2026-09-16

## 1. Purpose

Phase 5 exposes a narrow external service boundary over the existing Project Control Plane. The service never reimplements lifecycle rules and never becomes a parallel orchestration path.

## 2. Public Version

```text
API version: v1
Base path: /api/v1
Python facade: ksupervisor.service
Transport adapter: WsgiServiceAppV1
```

`ServiceApiV1` is transport-neutral. `WsgiServiceAppV1` is a thin standard-library WSGI adapter; production hosting/TLS are outside Phase 5.

## 3. Routes

```text
GET  /api/v1/projects
GET  /api/v1/projects/{project_id}
POST /api/v1/projects/{project_id}/lifecycle-transitions
POST /api/v1/projects/{project_id}/operational-transitions
```

Read responses expose the `Project` contract only. ProjectSpec integration/repository/notification/release configuration is not returned.

## 4. Authentication and Scopes

The service requires an injected authenticator. The baseline HTTP adapter supports host-supplied Bearer-token authentication through `StaticBearerAuthenticator`; tokens are not persisted by the service.

```text
projects:read
projects:lifecycle:write
projects:operational:write
```

Scopes are independent. A write scope does not implicitly grant read scope or another write scope.

## 5. Mutation Authority

Lifecycle mutation calls:

```text
ProjectRegistry.transition_lifecycle()
```

Operational mutation calls:

```text
ProjectRegistry.transition_operational()
```

The API does not copy the allowed-transition tables. Existing Pydantic/domain state models remain authoritative.

## 6. Idempotency

Every POST mutation requires `Idempotency-Key`.

The service stores an immutable `ServiceMutationRecord` containing project/API/operation/key scope, canonical request signature, resulting Project snapshot and creation time.

Rules:

- same key + same request -> stored Project result is replayed;
- replay does not append a second transition or audit event;
- same key + different request -> `IDEMPOTENCY_CONFLICT`;
- replay survives supported persistence restart/reopen;
- transition + service receipt share one persistence transaction.

## 7. Error Contract

Normalized v1 errors include:

```text
AUTH_REQUIRED        401
ACCESS_DENIED        403
NOT_FOUND            404
INVALID_REQUEST      400
INVALID_TRANSITION   409
IDEMPOTENCY_REQUIRED 400
IDEMPOTENCY_CONFLICT 409
METHOD_NOT_ALLOWED   405
INTERNAL_ERROR       500
```

Unexpected exceptions are converted to a generic `INTERNAL_ERROR` envelope; internal tracebacks are not returned by the service boundary.

## 8. Protected Data Boundary

The service does not resolve or return protected-reference contents. ProjectSpec configuration and `secret://...` access remain owned by existing access/policy/side-effect paths.

## 9. Explicit Non-Surface

Phase 5 does not expose Project registration, ProjectSpec approval/activation, Human Intervention/Approval mutation, Task/Workflow/Agent execution, release/publication mutation, Tool/Provider invocation, secret resolution or full ProjectRecoverySnapshot.

## 10. Validation Baseline

```text
Implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Core Validation run: 35103131762
Phase-specific tests: tests/test_v03_phase5_service_api.py
Cumulative pytest: 129 passed
branch-aware coverage: 85.34%
Core Validation: PASS
```
