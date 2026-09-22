# TEST_MATRIX
Active cumulative verification contract for approved ROADMAP v0.4.

Version: 4.2
Status: ACTIVE
Roadmap baseline: v0.2 COMPLETE + v0.3 COMPLETE + v0.4 ACTIVE
Current phase: v0.4 Phase 6 — PRE-IMPLEMENTATION AUDIT COMPLETE / ACTIVATION PENDING
Date: 2026-09-22

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
| 2 | operator API lifecycle, scopes, idempotency, redaction | COMPLETE |
| 3 | service host, health/readiness, shutdown, CLI parity | COMPLETE |
| 4 | GitHub repository/VCS provider and governed handoff | COMPLETE |
| 5 | Plugin-native package/manifest/marketplace validation | COMPLETE |
| 6 | structured telemetry plus SBOM/vulnerability/provenance evidence | AUDIT COMPLETE / ACTIVATION PENDING |
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

Phase 2 is COMPLETE. The following deterministic verification contract was satisfied:

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

## v0.4 Phase 2 — Completion Evidence

```text
Implementation PR: #24
Validated code/test head: f9f7284c407734fc2a3286f755c6827229142514
Validated code/test tree: abf48bbbfc2fe5e69c08fb7f6c8f3e9faee1b7ea
Code/test Core Validation: 35443690831 — PASS
Final PR head: 067828dfb6618ab412dfdfc64045cff9e8ea9cef
Final exact-head Core Validation: 35443735846 — PASS
Merged main: 9b532e4dd7c3aaaaaab2beaea97a3b017b7fff56
Merged-main Core Validation: 35443778180 — PASS
Full regression: 214 passed
Branch-aware total coverage: 83.21%
```

Completion authority: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_COMPLETE.md`.

## v0.4 Phase 3 — Audit Evidence

```text
Audit PR: #26
Initial audit head: 4499c98a47710d6c3c1ac2a71d0cd2264fbe8e86
Initial Core Validation: 35445444720 — PASS
Final audit head: 31eff0be47afdbc5837aa08595f3553d9bf022ca
Final audit tree: 241b9588ecbaf8f9ec02c31f71562d0a0867cf96
Final exact-head Core Validation: 35445489807 — PASS
Audit merged main: 31e39bf44e43ca241fb2536aa30bdfc519e0f020
Runtime/source/test paths changed: NONE
```

Phase 3 audit alone did not authorize runtime implementation. Owner activation approval was granted on 2026-09-19 through the separate protected activation checkpoint; after its merge the audited Phase 3 verification contract is active.

## v0.4 Phase 3 — Audited Verification Contract

Audit authority: `V0_4_PHASE3_PREIMPLEMENTATION_AUDIT.md`.

After the owner-approved activation checkpoint merges, required deterministic Phase 3 verification includes:

- installed-wheel service starts with valid config and fails closed on invalid bind/port/auth/config;
- one production composition root owns SQLite/control-plane resource lifecycle; production code does not import test fixtures;
- service auth resolves bearer tokens from protected references/environment injection with zero plaintext persistence/logging;
- host preserves the Phase 2 `/api/v1` route/scope/idempotency/error compatibility floor;
- health/readiness endpoints are minimal, redacted, and use existing health/deployment qualification contracts;
- readiness becomes false while draining; Project lifecycle state is not a service-readiness substitute;
- bounded workers plus connection/header/body timeout/config validation;
- existing 64 KiB request body compatibility floor is not weakened;
- graceful shutdown stops new requests before resource close and leaves SQLite reopenable;
- material mutation outcome is not inferred from client disconnect/transport timeout;
- restart/retry reuses Phase 2 durable command receipts and does not duplicate material work;
- forwarded headers are ignored by default and trusted only from configured proxy addresses;
- production proxy mode requires secure forwarded scheme; certificate lifecycle remains external;
- HTTP client/CLI uses Service/API only and does not import persistence/registry/kernel/workflow mutation authorities;
- CLI and direct HTTP yield equivalent authoritative transitions for representative read/mutation flows;
- mutation CLI preserves/surfaces idempotency keys for uncertain outcomes;
- bearer token contents are never CLI arguments;
- legacy `version`, `validate-config`, and `extensions` behavior remains compatible;
- service + CLI smoke runs outside the source checkout from the installed wheel;
- zero paid external resources are required;
- cumulative regression and permanent quality gates remain green.

## v0.4 Phase 3 — Completion Evidence

```text
Implementation PR: #29
Initial protected Core Validation: 35452558739 — PASS
Final PR head: c73e4c5f24f958ebb1473d4c8d23f28244c9f799
Final PR tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Final exact-head Core Validation: 35453258878 — PASS
Merged main: a1791b607496edfaf84593d753f7d1d7662eede1
Merged-main Core Validation: 35453297160 — PASS
Full regression: 229 passed
Branch-aware total coverage: 82.06%
Installed-wheel Phase 3 service/CLI smoke: PASS
Phase 4 activation: NO
```

Phase 3 satisfies the audited host/config/auth/health/readiness/proxy/client/CLI/restart/idempotency and installed-wheel verification contract. Completion authority: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_COMPLETE.md`.

## v0.4 Phase 4 — Audited Verification Contract

Audit authority: `V0_4_PHASE4_PREIMPLEMENTATION_AUDIT.md`.

After a separate owner-approved activation checkpoint merges, required deterministic Phase 4 verification includes:

- GitHub repository target canonicalization with explicit owner/name for automatable create;
- protected GitHub credential references only; no plaintext token persistence/logging/CLI output;
- deterministic fake/injected GitHub transport in normal CI;
- versioned GitHub REST request headers and safe response/error normalization;
- repository create/resolve idempotency, including uncertain-create recovery;
- exact visibility/default-branch/archive/disabled checks;
- new/empty repository bootstrap and existing-repository conflict safety;
- non-force ref updates and concurrent-head conflict handling;
- policy DENY / REQUIRE_APPROVAL blocks before any material GitHub call;
- durable idempotency/correlation with same-key/different-payload rejection;
- branch/commit/PR replay without duplicate repository, commit, branch or PR creation;
- protected-branch/ruleset denial cannot be bypassed;
- optional tag creation is idempotent and never moves an existing divergent tag;
- 401/403 permission/auth failures and 403/429 primary/secondary rate limits normalize safely;
- bounded retry/backoff respects reset/retry-after metadata;
- restart/reopen recovers partial repository/VCS handoff without duplicate material effects;
- Human Intervention fallback for credentials, permissions, policy and content conflicts;
- production ServiceRuntime / ProjectFactory wiring does not create a raw GitHub bypass;
- any additive Service/API/CLI repository operation remains explicit, scoped and idempotent;
- FilesystemRepositoryAdapter predecessor behavior remains compatible;
- release/publication owner-action boundary remains unchanged;
- zero paid external resources are required for authoritative validation;
- cumulative regression and permanent quality gates remain green.

A live GitHub smoke is supplemental and owner-controlled when it can be executed at zero cost. It is not an ordinary protected-PR merge dependency.

## v0.4 Phase 4 — Completion Evidence

Completion authority: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_4_COMPLETE.md`.

```text
Provider boundary PR: #36 / Core Validation 35742759396 — PASS
VCS handoff PR: #37 / Core Validation 35743886773 — PASS
ProjectFactory wiring PR: #38 / Core Validation 35748024918 — PASS
Service/API + CLI PR: #39 / Core Validation 35753867888 — PASS
Qualification PR: #40 / Core Validation 35755061918 — PASS
Qualification main: 8ba51416c561e841ae7a43c5941426b681299e80
Merged-main Core Validation: 35755228146 — PASS
Full regression: 279 passed
Branch-aware total coverage: 81.54%
Installed-wheel Phase 4 repository Service/API/CLI smoke: PASS
Zero-cost validation: PASS
```

The audited Phase 4 deterministic verification contract is satisfied. Live GitHub evidence remains supplemental and is not a protected merge dependency.

## v0.4 Phase 5 — Audited Verification Contract

Audit authority: `V0_4_PHASE5_PREIMPLEMENTATION_AUDIT.md`.

After a separate owner-approved activation checkpoint merges, required deterministic Phase 5 verification includes:

- canonical portable Agent Plugins root `plugin.json` with the pinned Agent Plugins 1.0 schema;
- deterministic plugin name/version/description plus safe OpenAI-specific `extensions.com.openai` metadata;
- current skill packaging at `skills/<slug>/SKILL.md` with valid name/description metadata and explicit workflow boundaries;
- required reference resources are actually packaged or readiness fails;
- source/destination path traversal and credential-file inclusion fail closed;
- structured registered-app mappings generate valid `.app.json` references only for supported app IDs;
- required/optional app semantics are preserved; app templates remain distinct from registered app IDs;
- Custom Action dependencies remain rebuild-required unless an explicit supported replacement mapping exists;
- selected GPT model and prior sharing/access state are never claimed to migrate;
- optional compatibility manifest cannot conflict with canonical portable/OpenAI settings;
- generated `.agents/plugins/marketplace.json` resolves exactly to the generated plugin package;
- optional existing `pluginId` is marketplace metadata only and never enters `plugin.json`;
- bundled MCP configuration is never generated implicitly and web/desktop compatibility implications are recorded when explicitly requested;
- machine-readable migration inventory preserves instructions/reference/apps/actions/MCP/access transfer status;
- structured regression cases validate positive/negative expected behavior;
- public-submission readiness, when explicitly requested, requires at least five positive and three negative cases;
- package validation is network-free and uses a pinned local compatibility/schema snapshot;
- legacy `GPT_STORE` persisted release behavior remains compatible;
- Release Manager continues to stop at the owner/workspace publication/availability boundary;
- no ChatGPT install/share/workspace-import/public-submission operation occurs in protected CI;
- zero paid external resources are required for authoritative validation;
- cumulative regression, branch-aware coverage >=80%, wheel/install smoke and protected `Core Validation` remain green.

Local/private plugin installation and account/workspace testing may supplement evidence when available at no project-attributable cost. They are not ordinary protected-PR merge dependencies.

## v0.4 Phase 5 — Completion Evidence

Completion authority: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_5_COMPLETE.md`.

```text
Activation checkpoint merge: 696c9b2a5873506f6164c03d71d21b557c66c8b4
Native package PR: #44 / Core Validation 35762060534 — PASS
Native package merged main: 57bb901a50fa5217727fa7335550f9794050b604
Metadata/reference/marketplace PR: #45 / Core Validation 35766681043 — PASS
Implementation merged main: f3cf85fce9a88eceab1a5636baf78b109f80d1d4
Implementation merged-main Core Validation: 35772305722 — PASS
Qualification PR: #46
Qualification code/test head: 4dc6308663ff51e86a69aaf8c9671311be17a630
Qualification Core Validation: 35772935562 — PASS
Full regression: 322 passed
Branch-aware total coverage: 81.20%
Installed-wheel Phase 5 native package generation: PASS
Reference fail-closed/path safety: PASS
Registered-app / marketplace consistency: PASS
Owner publication boundary / recovery: PASS
Legacy GPT_STORE compatibility: PASS
Implicit MCP generation: NONE
External ChatGPT install/share/publication: NOT REQUIRED / NOT PERFORMED
Zero-cost development policy: PASS
```

The audited deterministic Phase 5 verification contract is satisfied. Live account/workspace plugin installation remains supplemental owner-controlled evidence and is not a protected merge dependency.

## v0.4 Phase 6 — Audited Verification Contract

Audit authority: `V0_4_PHASE6_PREIMPLEMENTATION_AUDIT.md`.

After a separate owner-approved activation checkpoint merges, Phase 6 verification must prove:

- structured log output is machine-readable, bounded and redacted;
- request bodies, authorization/cookie values, resolved secrets, provider private payloads, model prompt/response content and repository/reference file contents do not leak into logs/telemetry/export output;
- arbitrary unsafe telemetry attributes fail closed;
- production telemetry uses a frozen event taxonomy and preserves correlation across service/provider/repository/release boundaries;
- production metrics use a fixed low-cardinality vocabulary and never use request/project/task/repository/user-controlled IDs as Prometheus labels;
- duration uses seconds and byte quantities use bytes;
- exporter queues, timeouts, retries and shutdown flush are bounded;
- exporter failure/drop does not change authoritative business/control outcomes;
- optional exporter failure does not make default service readiness false;
- OTLP export is optional and disabled safely when not configured;
- Prometheus-compatible output contains only approved metric families;
- exact stable Python support is 3.13 + 3.14 for the Phase 6 compatibility snapshot;
- protected CI gates both Python 3.13 and 3.14 while preserving the required `Core Validation` context;
- package metadata excludes unqualified future stable Python minors until separately approved;
- active external GitHub Actions are pinned to verified full commit SHAs;
- pull-request jobs retain read-only/minimal permissions and receive no attestation/OIDC write authority;
- exact CI dependency resolution is pinned/reviewable;
- built-wheel SHA-256 is recorded;
- deterministic SPDX 2.3 SBOM is generated from the pinned/resolved build environment;
- vulnerability review/scan emits machine-readable current-security evidence and distinguishes scanner/data unavailability from a clean result;
- trusted-main build provenance attestation is generated for the wheel;
- trusted-main SBOM attestation links the wheel and generated SBOM;
- attestation evidence remains verifiable through the supported GitHub attestation path;
- package publication remains manual owner-controlled;
- no external collector/SaaS or paid service is required;
- full cumulative regression, branch-aware coverage >=80%, compile, wheel/install and installed-wheel smokes remain green.

Vulnerability advisory status is intentionally time-sensitive as databases evolve; dependency resolution, scanner/tool configuration and evidence schema remain deterministic and reviewable.

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

Phase 0 through Phase 5 are COMPLETE. Phase 6 pre-implementation audit is COMPLETE. No runtime implementation phase is active; the next permitted action is a separate owner Phase 6 activation decision.
