# TEST_MATRIX
Active cumulative verification contract for approved ROADMAP v0.4.

Version: 3.5
Status: ACTIVE
Roadmap baseline: v0.2 COMPLETE + v0.3 COMPLETE + v0.4 ACTIVE
Current phase: v0.4 Phase 2 — AUDIT COMPLETE / INACTIVE
Date: 2026-09-19

## Preserved Regression Floor

The full completed v0.2/v0.3 matrix is frozen in `TEST_MATRIX_V0_3_ARCHIVE.md`. The complete Phase-0-era v0.4 matrix, including detailed planned Phase 1-7 families, is frozen in `TEST_MATRIX_V0_4_PHASE0_ARCHIVE.md`. Those requirements remain cumulative unless an explicit approved migration replaces them.

Authoritative predecessor runtime:

```text
Implementation commit: f0c9bc30a5562c83803a861aafe6f669a2ae4730
Implementation tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Validated runtime main: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Protected PR Core Validation: 35134961231 — PASS
Merged-main Core Validation: 35135133947 — PASS
Python workflow: 3.13
Local exact-tree regression: 163 passed / 85.82% branch coverage
```

## v0.4 Phase State

| Phase | Verification focus | Status |
| --- | --- | --- |
| 0 | predecessor traceability, product contract, no runtime diff | COMPLETE |
| 1 | governed production MODEL provider, protected credentials, non-reference capability path, zero-cost validation | COMPLETE |
| 2 | operator API lifecycle, scopes, idempotency, redaction | AUDIT COMPLETE / INACTIVE — ACTIVATION PENDING |
| 3 | service host, health/readiness, shutdown, CLI parity | PLANNED |
| 4 | GitHub repository/VCS provider and governed handoff | PLANNED |
| 5 | Plugin-native package/manifest/marketplace validation | PLANNED |
| 6 | structured telemetry plus SBOM/vulnerability/provenance evidence | PLANNED |
| 7 | end-to-end single-node product qualification | PLANNED |

## Phase 0 Evidence

```text
Activation PR: #10
Activation tree: c19e76192ab98003060bd86e5a193676029b358b
Core Validation: 35143639772 — PASS
Phase 0 completion PR: #11
Completion tree: 9e0cce06a27305d3143a01c242501070b67e417d
Completion Core Validation: 35146876160 — PASS
Runtime paths changed: NONE
```

## Phase 1 Activation Evidence

```text
Activation PR: #12
Activation head: b7f42a8051d730b75e48b811d252f711e8177d64
Activation tree: 2b47efc5aa56157b1877f8ff2b263d338f1dd250
Core Validation: 35150309758 — PASS
Merged main: 9d5b0fc9e0ab82fc7e61b1ebe0303b10a051c8b6
Runtime paths changed: NONE
```

Audit authority: `V0_4_PHASE1_PREIMPLEMENTATION_AUDIT.md`.

## Phase 1 Implementation Evidence

```text
Implementation PR: #14
Implementation head: 0d6a3ed863c687ec9461135a306180014c248312
Implementation tree: 7fabf5220d4370124bb245445c84f9ed77eb2041
Protected PR Core Validation: 35175344558 — PASS
Merged main: 8f748e993737cebe45a6e8ebaac74d8c0e10d1b7
Merged-main Core Validation: 35175392964 — PASS
Deterministic Phase 1 tests added: 24
Local full candidate: 187 passed / 85.02% branch coverage (Python 3.12.3, non-authoritative)
Live provider attempt: REACHED PROVIDER / credit_balance_exhausted — supplemental evidence; paid retry prohibited by development policy
```

All deterministic Phase 1 implementation requirements are merged and green. The earlier paid-success live-smoke gate is superseded by `DEVELOPMENT_RESOURCE_POLICY.md`: project development must not purchase provider credits. Phase 1 now requires formal completion review against the amended zero-cost criteria.

## v0.4 Phase 1 — Required Verification

Planned family: `tests/test_v04_phase1_model_provider_*.py`.

Required deterministic behaviors:

- production `openai.responses` MODEL adapter availability/config validation;
- configurable model ID and vendor-neutral `ModelProfile`/candidate projection;
- API credential represented only by authorized `AccessReference`, resolved through `SecretBackend` at the adapter boundary;
- no plaintext secret in Provider payload, durable state, audit, telemetry, idempotency signatures, exception text or ordinary logs;
- invocation only through `PolicyEngine` + `SideEffectGateway.execute_provider()` + `ProviderRegistry`;
- ALLOW invokes exactly once; DENY invokes zero times; REQUIRE_APPROVAL invokes zero times until a valid approval exists;
- outbound Responses request explicitly uses `store=false`;
- provider-hosted tools, remote conversation state and background mode are absent from Phase 1 requests;
- successful text, provider response id, effective model, status and usage normalize into provider-neutral result metadata;
- hidden reasoning content is not persisted as product state;
- incomplete/failed/malformed provider responses do not normalize as success;
- authentication/configuration, invalid request, timeout/cancellation, rate limit, transient server/provider and non-retryable failures have safe normalized codes/category/retryability;
- retry count/backoff and network timeouts are bounded and do not bypass gateway idempotency;
- unknown legacy adapter exceptions preserve backward-compatible generic gateway normalization;
- deterministic fake transport/provider keeps normal CI credential-free and network-free;
- existing offline model/provider registry and SideEffectGateway tests remain green;
- a no-cost owner-controlled live provider smoke may supplement evidence when available; successful paid live inference is not a completion requirement, and paid credits/subscriptions must not be purchased for validation.

## Phase 1 Completion Review

```text
Gap-closure PR: #21
Validated code/test head: 4bfacabec2da3e48618efd6ee0dd9f9b4c2e1d88
Validated code/test tree: 77f1c5aad6b34a8408353f8655c2ac5b06fcb886
Core Validation: 35440664106 — PASS
Full regression: 192 passed
Branch-aware total coverage: 84.86%
Non-reference model-backed capability path: PASS
Zero-transport DENY behavior: PASS
Safe credit_balance_exhausted normalization: PASS
Paid successful live inference required: NO
```

Completion authority: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_COMPLETE.md`.

## v0.4 Phase 2 — Audited Verification Contract

Canonical audit: `V0_4_PHASE2_PREIMPLEMENTATION_AUDIT.md`.

Phase 2 remains inactive. When separately activated, required deterministic verification includes:

- backward compatibility of all v0.3 Phase 5 Service/API routes/scopes/idempotency;
- safe fixed-state Project registration/onboarding;
- ProjectSpec protected-reference validation, explicit status-transition authority and separate activation;
- independent domain scopes with denial before mutation;
- Human Action and Policy Approval operations through their authoritative brokers;
- Task/Workflow start/status/cancel through lower-layer execution control, never direct persistence rewrites;
- generic durable service command receipts with restart/crash reconciliation and no duplicate material work;
- explicit redacted status/recovery projections;
- persisted release/readiness/target status and owner publication-confirmation through ReleaseManager;
- cross-project resource isolation;
- no raw-secret, direct Tool or direct Provider endpoint;
- no paid external resource requirement.

## Permanent Quality Gates

```text
protected Core Validation                     PASS
full v0.2 + v0.3 + active v0.4 regression   PASS
branch-aware total coverage                   >= 80%
ResourceWarning                               error / PASS
compileall including examples                 PASS
isolated wheel build                          PASS
wheel install outside checkout                PASS
public package/CLI import smoke               PASS
secret/redaction regression                   PASS for material new boundaries
restart/recovery regression                   PASS for durable new state
failure-injection regression                  PASS for external provider boundaries
migration/rollback regression                 PASS for schema/config contract changes
GitHub ruleset / required CI                  enforced
zero-cost development resource policy         PASS / no paid-only phase gate
```

## Live External Evidence Rule

Normal protected CI remains deterministic, credential-free and zero-cost to the project owner. `DEVELOPMENT_RESOURCE_POLICY.md` is authoritative for external development resources.

A live external smoke is supplemental when the required operation is available without payment. If successful live evidence requires purchasing credits, a subscription or paid infrastructure, it is non-blocking and must be replaced by deterministic contract/integration evidence plus safe governed failure/reachability evidence where useful. No phase may require a paid-only external service to pass development validation.

## Activation Rule

Phase 0 and Phase 1 are COMPLETE. Phase 2 pre-implementation audit is COMPLETE; Phase 2 remains INACTIVE / ACTIVATION PENDING. No Phase 2 runtime work is authorized until a separate activation checkpoint is owner-approved and merged through protected governance. Phases 3-7 remain inactive.
