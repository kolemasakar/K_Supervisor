# PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_IMPLEMENTED

Контрольна точка реалізації ROADMAP v0.4 Phase 3 — Production Single-Node Service Host & Operator CLI.

Version: 1.0
Status: IMPLEMENTED — PROTECTED MERGE PENDING
Roadmap: v0.4
Phase: 3
Date: 2026-09-19
Activated main predecessor: `f65df3b11ab46730295c13fb2c7f6d91243e89ff`
Activated predecessor tree: `6aef5afe60712b660cc9d67f375a2a8c2df90286`

## Implementation Evidence

```text
Implementation PR: #29
Initial implementation head: 46bca5223d5e42d9051f886832a7d12a87a5d812
Initial implementation tree: 82da649caa8afff0c04124f3a9dd2b61e9c886e8
Protected PR Core Validation: 35452558739 — PASS
Authoritative CI regression: 229 passed
Authoritative CI branch-aware coverage: 82.06%
Installed-wheel Phase 3 service/CLI smoke: PASS
Final exact-head Core Validation: PENDING
Merged main SHA: PENDING
Merged-main Core Validation: PENDING
Local targeted Phase 3 + legacy CLI subset: 17 passed
Local full regression: 229 passed
Local branch-aware coverage: 82.06%
ResourceWarning gate: PASS / no warnings
Local installed-wheel smoke: PASS (Python 3.12.3 supplementary)
Authoritative CI Python: 3.13
```
## Implemented Boundary

- additive `PlatformConfig v1` service-host/client configuration; old config remains valid;
- protected bearer principal configuration through `AccessReference` + `SecretBackend`;
- one production `ServiceRuntime` composition root over one authoritative SQLite store;
- configured extensions activate only through existing `ExtensionGovernance`;
- bounded single-node WSGI host with worker semaphore, socket timeout, explicit lifecycle and drain;
- minimal unauthenticated `GET /healthz` and `GET /readyz`;
- trusted-proxy allowlist and required forwarded HTTPS in proxy mode;
- reusable transport-only `ServiceClientV1`;
- operator CLI route parity for Project, ProjectSpec, Human Action, Approval, Task, Workflow, Release and recovery-status operations;
- mutation idempotency keys are preserved/surfaced, including transport uncertainty;
- SQLite read/write access is serialized across host threads without persistence schema change;
- protected CI includes installed-wheel host/client/CLI smoke outside source checkout.

## Preserved Invariants

- Service/API v1 remains authoritative for route, scope, error and mutation semantics;
- 64 KiB request-body bound remains unchanged;
- bearer token contents are never configuration values or CLI arguments;
- client timeout/disconnect does not redefine material mutation outcome;
- certificate lifecycle remains external;
- no GitHub repository/VCS provider or other Phase 4 work is included;
- no paid development resource is required.
## Deterministic Validation

Local candidate validation passed the targeted Phase 3/legacy CLI subset, cumulative regression, branch-aware coverage gate, ResourceWarning-as-error gate, compileall and a supplementary installed-wheel smoke. The authoritative package/host qualification remains the protected Python 3.13 `Core Validation` workflow.

## Completion Gate

Phase 3 is not COMPLETE until:

1. the implementation candidate is committed to a protected pull request;
2. exact implementation head passes required `Core Validation`;
3. final documentation/evidence head also passes required `Core Validation`;
4. the PR merges to `main`;
5. merged `main` passes `Core Validation`;
6. the completion checkpoint records exact immutable evidence.

Phase 4 remains inactive until a separate pre-implementation audit/activation decision.
