# PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_ACTIVATED

Контрольна точка активації ROADMAP v0.4 Phase 3 — Production Single-Node Service Host & Operator CLI.

Version: 1.0
Status: ACTIVATED — EFFECTIVE ON PROTECTED MERGE
Roadmap: v0.4
Phase: 3
Date: 2026-09-19
Baseline main: `3f1f386434f73d4cbd85ddd6dfad6135ae21f520`
Baseline tree: `66d92d290be42e503ea0df3f923a8af212b4eb38`
Validated runtime predecessor: `9b532e4dd7c3aaaaaab2beaea97a3b017b7fff56`
Validated runtime predecessor tree: `dbf8eb357a1cc0bd133b58a55603e2bcc26d341c`

## Activation Basis

Phase 0, Phase 1 and Phase 2 are COMPLETE. `V0_4_PHASE3_PREIMPLEMENTATION_AUDIT.md` is COMPLETE and merged through protected PR #26. The owner explicitly approved Phase 3 activation on 2026-09-19.

The handoff synchronization PR #27 is documentation-only, merged as `3f1f386434f73d4cbd85ddd6dfad6135ae21f520`, and contains no runtime/source/test changes after the validated Phase 2 runtime baseline.

## Authorized Runtime Scope

After this activation checkpoint passes protected `Core Validation` and merges to `main`, Phase 3 authorizes only the audited service-host/operator-CLI work:
- additive production service composition root with one authoritative SQLite/control-plane lifecycle;
- production-capable bounded single-node WSGI host around existing Service/API v1;
- additive host/client configuration with fail-closed startup validation;
- protected-reference/environment-injected bearer authentication with no token persistence;
- minimal `/healthz` and `/readyz` wired to existing health/deployment qualification;
- graceful drain/shutdown with readiness=false before resource close and SQLite reopen safety;
- explicit trusted-proxy/TLS-forwarding contract with forwarded headers ignored by default;
- reusable HTTP `ServiceClientV1` transport boundary;
- operator CLI command groups that use Service/API only;
- restart/retry behavior preserving Phase 2 durable command/idempotency authority;
- installed-wheel host/client/CLI smoke and runbook updates;
- deterministic zero-cost validation under `DEVELOPMENT_RESOURCE_POLICY.md`.

## Explicit Non-Scope

- no second control plane or CLI direct persistence/registry/kernel/workflow/provider/tool/secret mutation path;
- no Service/API business-semantic expansion outside the audited Phase 3 contract;
- no certificate issuance/renewal platform;
- no horizontal scaling, multi-node coordination or distributed persistence;
- no Phase 4 GitHub repository/VCS provider implementation;
- no paid development-validation dependency;
- no automatic external publication.

## Permanent Invariants
- Phase 2 `/api/v1` routes, scopes, status/error meanings and durable idempotency semantics remain authoritative;
- plaintext bearer tokens never enter config files, CLI arguments, logs, telemetry, errors or durable state;
- client timeout/disconnect does not redefine material mutation outcome;
- forwarded headers are trusted only from explicitly configured proxy addresses;
- safe default binding remains loopback unless the audited secure-proxy boundary is satisfied;
- existing `version`, `validate-config` and `extensions` CLI behavior remains compatible;
- normal protected CI remains deterministic, credential-free and zero-cost.

## Protected Activation Evidence

```text
Activation PR: #28
Initial activation head: f06673fc1f6469d11c3f16b341238c76ba473494
Initial activation tree: 634324ffee6bd31b1dfe1fd0a77e517c9cb49475
Core Validation: 35450123607 — PASS
Runtime/source/test paths changed: NONE
```

The exact final PR head, including recorded validation evidence, must also pass required `Core Validation` before merge.

## Activation State

```text
Owner approval: YES — 2026-09-19
Pre-implementation audit: COMPLETE
Audit PR: #26
Audit final Core Validation: 35445489807 — PASS
Phase 3 runtime implementation authorization: YES — audited scope only, effective after this checkpoint merges
Phase 4-7 runtime implementation authorization: NO
Zero-cost development policy: REQUIRED
```

No Phase 3 runtime/source/test code may be committed before this checkpoint passes protected governance and merges to `main`.
