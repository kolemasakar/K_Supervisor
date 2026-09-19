# V0_4_PHASE3_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 3 — Production Single-Node Service Host & Operator CLI.

Version: 1.0
Status: COMPLETE — ACTIVATION PENDING
Date: 2026-09-19
Baseline main: 5b15e54ce4fb0efd50a8e8c41e083a9e870c3294
Baseline tree: de06c7166bd7b08daabdf362e2ff8e81b39e26b7
Validated runtime predecessor main: 9b532e4dd7c3aaaaaab2beaea97a3b017b7fff56
Validated runtime predecessor tree: dbf8eb357a1cc0bd133b58a55603e2bcc26d341c
Predecessor phase: v0.4 Phase 2 COMPLETE
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 3 is limited to the approved ROADMAP v0.4 Production Single-Node Service Host & Operator CLI assignment:

- production-capable long-running host around the existing versioned Service/API boundary;
- explicit bind/port/configuration and startup validation;
- bounded request handling plus graceful drain/shutdown;
- authentication configuration through protected references / environment injection;
- liveness/readiness HTTP endpoints wired to existing health/deployment qualification contracts;
- explicit trusted reverse-proxy/TLS termination contract;
- operator CLI commands that call the Service/API over HTTP and never become a second control plane;
- installed-wheel host/client smoke and runbook updates.

Explicitly out of Phase 3 scope:

- new business/control-plane semantics not already authorized by Service/API v1;
- direct persistence, registry, Tool, Provider or secret-resolution CLI commands;
- certificate issuance/renewal or an embedded certificate-management platform;
- horizontal scaling, multi-node coordination, remote worker federation or distributed persistence;
- production GitHub repository/VCS implementation (Phase 4);
- Plugin-native packaging work (Phase 5);
- mandatory remote telemetry/exporter infrastructure (Phase 6);
- paid external development resources.

`DEVELOPMENT_RESOURCE_POLICY.md` remains authoritative: implementation and validation must remain zero-cost.

## 2. Frozen Predecessor and Ancestry

Phase 2 runtime completion is the predecessor:

```text
Phase 2 implementation PR: #24
Validated code/test head: f9f7284c407734fc2a3286f755c6827229142514
Validated code/test tree: abf48bbbfc2fe5e69c08fb7f6c8f3e9faee1b7ea
Code/test Core Validation: 35443690831 — PASS
Full regression: 214 passed
Branch-aware coverage: 83.21%

Final PR head: 067828dfb6618ab412dfdfc64045cff9e8ea9cef
Final exact-head Core Validation: 35443735846 — PASS
Runtime merged main: 9b532e4dd7c3aaaaaab2beaea97a3b017b7fff56
Runtime merged tree: dbf8eb357a1cc0bd133b58a55603e2bcc26d341c
Merged-main Core Validation: 35443778180 — PASS
```

Current documentation main is:

```text
main: 5b15e54ce4fb0efd50a8e8c41e083a9e870c3294
tree: de06c7166bd7b08daabdf362e2ff8e81b39e26b7
```

The compare from the validated Phase 2 runtime main to current main is ahead-only and changes only `README.md` / `docs/*`. No runtime/source/test path changed after the validated Phase 2 runtime merge. Therefore `9b532e4d...` / tree `dbf8eb35...` remains the authoritative runtime predecessor for Phase 3.

Repository ruleset `main-core-validation` (id `23556478`) remains active and required.

## 3. Existing Service/API Compatibility Floor

The Phase 2 Service/API v1 boundary is complete and remains authoritative. Phase 3 must host it; it must not reimplement it.

Existing reusable boundaries:

- `ServiceApiV1` owns route dispatch, normalized errors, scope checks and Phase 2 operator orchestration;
- `WsgiServiceAppV1` is a thin WSGI adapter;
- `StaticBearerAuthenticator` performs constant-time token comparison against an in-memory principal mapping;
- `ServicePrincipal` and the existing independent scopes remain the access-control contract;
- material mutations retain Phase 2 idempotency / durable `ServiceCommandRecord` or legacy `ServiceMutationRecord` authority.

Existing WSGI compatibility floor:

- request body bound: 64 KiB;
- UTF-8 JSON body parsing;
- `Cache-Control: no-store`;
- Bearer authentication injected by the host;
- normalized generic internal error response;
- no bearer-token persistence by the API.

Phase 3 must preserve all existing `/api/v1` routes, scopes, status/error meanings and idempotency semantics.

## 4. Current Gaps

The current repository does not yet provide a production single-node operator product boundary.

### 4.1 No production composition root

Phase 2 tests compose SQLite, registries, Supervisor, WorkflowEngine, Human Intervention, approvals and ServiceApiV1 in `tests/v04_phase2_support.py`. Test support is not a production bootstrap contract.

Required Phase 3 prerequisite:

- add a production composition/app-factory boundary (for example `ServiceRuntime` / `build_service_runtime()`);
- it owns resource creation and shutdown ordering;
- it creates one authoritative SQLite store and injects that same store into the control-plane components;
- configured installed extensions may be activated only through existing extension governance;
- no production module may import test fixtures.

The host process owns the composition root; CLI client commands do not.

### 4.2 No long-running host

`WsgiServiceAppV1` explicitly states that deployment/hosting remains external. There is no bind/listen loop, worker bound, connection/request timeout policy, signal handling, drain state or shutdown ownership.

Phase 3 must introduce a host adapter/process without moving domain logic into it.

### 4.3 No host/auth configuration contract

`PlatformConfig v1` currently contains state DB and extension settings only.

Required compatible extension:

- old config files remain valid;
- service-host configuration is additive and optional for non-server commands;
- `serve` fails closed when required host/auth configuration is absent or invalid;
- unknown fields continue to fail validation;
- no config version bump is required if old config semantics remain valid and all new fields are optional/defaulted; otherwise a versioned migration is mandatory.

### 4.4 No health/readiness HTTP surface

`ServiceHealthEvaluator` and `DeploymentQualifier` already exist, but no HTTP endpoint exposes their safe status.

Phase 3 must add host-level health/readiness endpoints without serializing Project records, secrets or detailed internal exception text.

### 4.5 No trusted-proxy/TLS contract

There is no current interpretation of `X-Forwarded-*`, trusted proxy addresses or secure external scheme.

Phase 3 must fail closed instead of implicitly trusting forwarded headers.

### 4.6 No HTTP client / operator CLI

The public CLI currently supports only:

```text
k-supervisor version
k-supervisor validate-config PATH
k-supervisor extensions
```

There is no Service/API client and no operator command surface.

## 5. Service Runtime Composition Contract

Phase 3 implementation must create one production composition root with explicit lifecycle ownership.

Minimum responsibilities:

```text
ServiceRuntime
  store
  projects
  capabilities / agents
  dispatcher / kernel
  human intervention
  policy approvals
  workflows
  release manager where configured
  telemetry / health evaluator
  ServiceApiV1
  authenticator
  WsgiServiceAppV1
  close()
```

Rules:

- one authoritative `PersistenceStore` instance per process;
- startup initializes/validates SQLite before serving;
- runtime components that require the store share that exact instance;
- extension activation must use `ExtensionGovernance` and existing trust records;
- strict extension mode fails startup on an unauthorized/incompatible configured extension;
- runtime shutdown is idempotent and closes owned resources only after request drain;
- no public CLI mutation command may obtain this runtime object locally.

Phase 3 does not require a new persistence schema unless implementation actually adds durable fields that cannot use existing generic resources/events.

## 6. Host and Request-Handling Contract

Phase 3 must add a replaceable host adapter around the WSGI app.

Required capabilities:

- explicit bind host and TCP port;
- bounded worker/concurrency count;
- bounded connection/header/body read time;
- deterministic maximum request body behavior no weaker than the current 64 KiB WSGI bound;
- graceful stop-accepting-new-requests state;
- bounded drain interval;
- deterministic process exit status on startup/config/bind failure;
- no traceback/private internal data in HTTP responses.

A stdlib reference/development WSGI server alone is insufficient evidence for the roadmap's “production-capable” host claim. Phase 3 may add one maintained zero-cost WSGI host dependency or an equivalent bounded server adapter. Any selected dependency must be package-declared, covered by installed-wheel tests and require no paid service.

Application-dispatch semantics remain authoritative:

- an HTTP/client timeout after a material mutation has been dispatched does **not** mean that mutation was cancelled;
- the host must not rewrite durable command status merely because a client disconnected;
- uncertain mutation outcomes are resolved by the Phase 2 idempotency/recovery contract using the same idempotency key and/or status reads;
- explicit Task/Workflow cancellation continues to use Phase 2 API operations.

## 7. Startup, Drain and Shutdown Semantics

Required state model:

```text
STARTING -> READY -> DRAINING -> STOPPED
                 \-> FAILED (startup only)
```

Startup must validate at least:

- config version/shape;
- bind host/port;
- SQLite initialization/current schema;
- required auth principal/token references;
- extension activation policy where configured;
- required service health/deployment qualification probes.

Drain/shutdown rules:

- on supported termination signal or explicit host stop, readiness becomes false before the listener stops;
- stop accepting new application requests;
- allow in-flight requests to finish within the configured drain window;
- do not close SQLite while accepted requests still own application work;
- do not reinterpret an unfinished material API call as rolled back unless its lower-layer authority actually rolled it back;
- after clean shutdown the store must reopen and pass integrity/recovery checks.

The implementation must document the bounded-shutdown behavior for the case where an in-flight operation outlives the preferred drain interval; it may not silently corrupt/close shared resources beneath a live request.

## 8. Authentication and Protected Credentials

The existing `StaticBearerAuthenticator` remains acceptable as the first single-node auth mechanism if tokens are injected safely.

Required server-side configuration shape is conceptually:

```text
principal_id
scopes
token_ref = secret://...
```

Rules:

- config may persist the opaque `AccessReference`, not bearer token contents;
- token references resolve at startup through `SecretBackend` / `EnvironmentSecretBackend`;
- resolved values remain in memory only;
- startup fails if a required token reference is unavailable;
- plaintext bearer tokens must not appear in config validation output, telemetry, logs, errors or durable state;
- no service token CLI argument such as `--token <secret>` is permitted because process arguments are not an approved secret channel;
- the client may resolve a configured token reference or use explicitly documented environment injection.

Phase 3 does not add external vault infrastructure.

## 9. Health and Readiness HTTP Contract

Host-level endpoints are authorized as additive operational surfaces, separate from business `/api/v1` routes:

```text
GET /healthz
GET /readyz
```

Required semantics:

- `/healthz`: process/service liveness only;
- `/readyz`: ability to accept new operator requests, derived from existing health/deployment qualification boundaries plus host drain state;
- DRAINING always makes readiness false;
- Project lifecycle states such as `WAITING_FOR_OWNER` are not service-health substitutes;
- response bodies are allowlisted and minimal;
- no Project IDs, secret references, tokens, filesystem paths, exception messages or private request data are exposed;
- successful or failed probes are safe for unauthenticated reverse-proxy/orchestrator use;
- detailed internal diagnostics remain outside this unauthenticated surface.

Suggested status behavior:

```text
health live       -> 200
health not live   -> 503
ready             -> 200
not ready/draining-> 503
```

The implementation may expose equivalent names only if compatibility/documentation remains explicit.

## 10. Reverse Proxy and TLS Boundary

Supported Phase 3 production topology:

```text
client
  -> TLS reverse proxy owned/configured by operator
  -> trusted local/private hop
  -> K_Supervisor single-node HTTP host
```

Security rules:

- certificate issuance/renewal remains external;
- forwarded headers are ignored by default;
- proxy mode requires an explicit allowlist of trusted proxy addresses/CIDRs;
- `X-Forwarded-Proto` or equivalent is honored only from a trusted peer;
- secure production proxy mode requires forwarded scheme `https`;
- untrusted peers cannot use forwarded headers to claim HTTPS/client identity;
- bearer authentication never derives identity from forwarded user headers;
- host/client URL construction must not trust arbitrary `Host` / forwarded-host values for authorization.

The safe default is loopback binding. Any non-loopback production exposure must satisfy the documented secure-proxy configuration boundary rather than silently serving cleartext credentials over an untrusted network.

## 11. Service Client and Operator CLI Contract

Phase 3 must add a reusable HTTP `ServiceClientV1` (name may vary) that implements transport only. It must not contain business-state rules.

The CLI then calls that client for the Phase 2 operator surface. Command groups should cover, at minimum, route-equivalent operations for:

- Projects: list/get/register and existing lifecycle/operational transitions;
- ProjectSpecs: list/submit/approve/reject/activate;
- Human Actions: list/verify/cancel;
- Policy Approvals: list/approve/reject/revoke;
- Tasks: list/get/start/cancel;
- Workflows: list/get/start/cancel;
- Releases: list/get and confirm-publication;
- recovery status.

Exact command spelling may be adjusted during implementation, but semantics must remain one-to-one with supported Service/API v1 operations.

CLI rules:

- no direct `SQLitePersistenceStore`, `ProjectRegistry`, `SupervisorKernel`, `WorkflowEngine`, broker or `ReleaseManager` imports for operator mutations;
- complex request bodies may come from JSON files/stdin rather than unsafe shell arguments;
- bearer token contents are not command-line arguments;
- material mutation calls preserve the API `Idempotency-Key` contract;
- if the CLI auto-generates a key, it must surface that safe key to the operator even when the transport outcome is uncertain so the same logical request can be replayed;
- non-2xx responses map to deterministic non-zero CLI exit status without raw traceback;
- machine-readable JSON output is preferred for automation;
- existing `version`, `validate-config`, and `extensions` commands remain backward-compatible.

## 12. Restart and Idempotency Contract

Phase 3 introduces a real network boundary but must not create new material-mutation semantics.

Required rules:

- all Phase 2 mutation idempotency behavior remains authoritative;
- a network retry uses the same idempotency key for the same logical mutation;
- host restart/reopen reconciles existing durable command receipts rather than creating replacement work;
- client retry logic must never blindly retry non-idempotent mutation requests with a new key;
- read operations may be retried safely subject to normal timeout policy;
- service restart must not create duplicate Task, Workflow, release/publication or Project mutations.

No additional “exactly once over HTTP” claim is made beyond the existing durable command/reconciliation contract.

## 13. Configuration Compatibility Decision

Preferred compatible direction:

- keep `config_version = "1"` if the implementation only adds optional/defaulted service-host/client sections and old config behavior remains unchanged;
- `k-supervisor validate-config` must redact or omit any resolved secret value;
- fail closed on unsupported future config versions/unknown fields;
- if implementation discovers that existing config semantics must change incompatibly, stop and use an explicit config-version migration rather than silently changing v1.

Service config must include bounded numeric validation for port, worker/concurrency count and timeout/drain values.

## 14. Packaging and Installation Contract

The existing console entry point remains:

```text
k-supervisor = ksupervisor.cli:main
```

Phase 3 may add a `serve` subcommand and operator subcommands rather than a second executable. A second executable is not required.

Installed-wheel qualification must prove, outside the source checkout:

- import of public service/client surfaces;
- config validation;
- server startup on an ephemeral loopback port;
- `/healthz` and `/readyz`;
- one authenticated Service/API request;
- one CLI request against the running installed service;
- graceful shutdown and SQLite reopen.

Any new runtime dependency must be declared in package metadata and present in wheel-install validation.

## 15. Zero-Cost Validation Plan

Phase 3 requires no paid provider, cloud host, public DNS or TLS certificate.

Authoritative validation can use:

- loopback sockets;
- ephemeral ports;
- temporary SQLite;
- deterministic local/fake runtime capabilities;
- local HTTP client requests;
- deterministic proxy-header fixtures;
- subprocess-installed-wheel smoke;
- signals/process shutdown under CI where supported.

External production deployment remains an operator concern; paid infrastructure is not a completion gate.

## 16. Required Test Families

Planned families remain:

```text
tests/test_v04_phase3_service_host_*.py
tests/test_v04_phase3_operator_cli_*.py
```

Required deterministic coverage:

- valid startup/bind and fail-closed invalid bind/port/config;
- missing/invalid protected auth reference blocks startup without revealing token material;
- bearer scope enforcement remains identical through the real host;
- 64 KiB request-body compatibility floor and malformed UTF-8/JSON behavior;
- bounded worker/request/connection configuration validation;
- health/readiness 200/503 semantics and DRAINING readiness=false;
- deployment/service-health integration without using Project lifecycle as readiness;
- trusted proxy allowlist and rejection/ignoring of spoofed forwarded headers;
- production proxy mode requires secure forwarded scheme;
- graceful stop accepting new requests and clean SQLite reopen;
- restart preserves Phase 2 command receipts/idempotent replay with no duplicate material work;
- transport uncertainty followed by same-idempotency-key replay;
- CLI imports/calls the HTTP client, not control-plane persistence/registry/kernel internals;
- CLI/HTTP parity for representative read and material mutation flows;
- CLI errors and exit codes are deterministic and do not leak traceback/secrets;
- legacy CLI commands remain compatible;
- installed-wheel service + CLI smoke outside source checkout;
- cumulative regression, branch-aware coverage >=80%, ResourceWarning-as-error, compileall, build/install and public CLI/import smoke.

## 17. Implementation Order Guard

After a separate owner-approved activation checkpoint is merged through protected governance, Phase 3 implementation should proceed in this order:

1. additive service-host/client configuration contracts and redaction validation;
2. production composition root with explicit owned-resource lifecycle;
3. health/readiness host wrapper and startup qualification;
4. production-capable bounded WSGI host adapter plus drain/shutdown state;
5. trusted-proxy/TLS-forwarding enforcement;
6. HTTP `ServiceClientV1`;
7. operator CLI command groups over that client only;
8. installed-wheel host/client smoke and runbook documentation;
9. full Phase 3 + cumulative validation.

If any implementation step requires changing Service/API business semantics, pause and audit that change rather than embedding it in the host or CLI.

## 18. Protected Governance Evidence

```text
Audit PR: #26
Initial audit head: 4499c98a47710d6c3c1ac2a71d0cd2264fbe8e86
Initial audit tree: b39c88572d2d1ca6baf32194f4798e9ba07f7fe6
Initial Core Validation: 35445444720 — PASS

Final audit head: 31eff0be47afdbc5837aa08595f3553d9bf022ca
Final audit tree: 241b9588ecbaf8f9ec02c31f71562d0a0867cf96
Final exact-head Core Validation: 35445489807 — PASS
Audit merged main: 31e39bf44e43ca241fb2536aa30bdfc519e0f020
Runtime/source/test paths changed: NONE
```

Protected audit governance is complete. The merged audit remains documentation-only and does not activate Phase 3.

## 19. Audit Outcome

The existing architecture is suitable for additive Phase 3 productization. The principal missing layer is operational composition/hosting/client infrastructure, not a new control plane.

Audit result:

```text
Phase 0: COMPLETE
Phase 1: COMPLETE
Phase 2: COMPLETE
Phase 3 pre-implementation audit: COMPLETE
Phase 3 activation: NO / PENDING OWNER APPROVAL
Phase 3 runtime implementation authorized: NO
Phase 4-7: PLANNED / INACTIVE
```

This document does not activate Phase 3. Runtime changes may begin only after explicit owner approval, a separate Phase 3 activation checkpoint, protected `Core Validation` PASS, and merge to `main`.
