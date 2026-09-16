# TEST_MATRIX
Active cumulative verification contract for approved ROADMAP v0.4.

Version: 3.0
Status: ACTIVE
Roadmap baseline: v0.2 COMPLETE + v0.3 COMPLETE + v0.4 ACTIVE
Current phase: v0.4 Phase 1 — READY FOR PRE-IMPLEMENTATION AUDIT
Date: 2026-09-16

## Preserved Predecessor Regression Floor

The complete v0.2 + v0.3 matrix and phase evidence are frozen in `TEST_MATRIX_V0_3_ARCHIVE.md`. Every predecessor test remains mandatory unless a later explicit compatibility migration replaces it.

Authoritative v0.3 runtime baseline:

```text
Implementation commit: f0c9bc30a5562c83803a861aafe6f669a2ae4730
Implementation tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Validated main SHA: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Protected PR Core Validation: 35134961231 — PASS
Merged-main Core Validation: 35135133947 — PASS
Python workflow: 3.13
Local exact-tree result: 163 passed / 85.82% branch coverage
```

Predecessor permanent gates remain in force: branch-aware total coverage >=80%, ResourceWarning-as-error, compileall including examples, isolated wheel build, wheel install outside checkout, public package/CLI smoke, persistence/recovery checks, extension governance and protected `Core Validation`.

## v0.4 Phase Status

| Phase | Required verification | Status |
| --- | --- | --- |
| 0 | predecessor traceability, product-gap assignment, deployment/trust contract, compatibility freeze, no runtime diff | COMPLETE |
| 1 | production MODEL provider, protected credentials, policy-gated inference, normalized failure/usage evidence, live smoke | READY — AUDIT PENDING |
| 2 | operator API lifecycle, approval/intervention/execution/release operations, idempotency, redaction | PLANNED |
| 3 | installed service host, health/readiness, graceful shutdown, operator CLI parity, reverse-proxy contract | PLANNED |
| 4 | GitHub repository/VCS provider, protected credentials, idempotent recovery, policy/governance enforcement | PLANNED |
| 5 | Plugin-native package/manifest/marketplace validation with legacy compatibility | PLANNED |
| 6 | structured logs, telemetry exporters, SBOM/vulnerability/provenance CI evidence | PLANNED |
| 7 | complete single-node owner/operator lifecycle, recovery, concurrency, provider and release qualification | PLANNED |

## v0.4 Phase 0 — Baseline & Contract Verification

Required verification:

- current `main` ancestry against the v0.3 validated runtime and closure baseline;
- public package/CLI/config/Service API/extension compatibility inventory;
- repository ruleset and required `Core Validation` verification;
- product-gap classification into Phase 1-7 or explicit deferred scope;
- supported single-node topology and security/control invariants;
- current Plugin compatibility snapshot recorded before runtime implementation;
- migration/rollback and live-external-evidence rules documented;
- no runtime path changed by Phase 0;
- protected activation PR `Core Validation` PASS.

Phase 0 evidence:

```text
Activation PR: #10
Activation head SHA: 78ad31bb7df0b654be3477b0be3136db2270abad
Activation tree: c19e76192ab98003060bd86e5a193676029b358b
Core Validation: 35143639772 — PASS
Merged main: b559f3a6158566531e2896e91ced817484d6f152
Runtime path changes: NONE
```

## v0.4 Phase 1 — Production Model Provider & AI Execution

Planned test family: `tests/test_v04_phase1_model_provider_*.py`.

Required behaviors:

- production MODEL adapter availability/config validation;
- protected-reference credentials with no clear-text persistence/logging;
- vendor-neutral model profile discovery/selection;
- invocation only through governed Provider/SideEffectGateway policy path;
- ALLOW invokes once, DENY zero times, REQUIRE_APPROVAL only after valid approval;
- timeout/cancellation/budget/rate-limit/provider failures normalize deterministically;
- usage/request/provider correlation without hidden chain-of-thought persistence;
- deterministic fake provider for normal CI;
- reference offline agents and predecessor provider/registry tests remain green;
- separate owner-controlled live inference smoke is required for Phase 1 completion but not ordinary PR merge.

## v0.4 Phase 2 — Operator Control API

Planned test family: `tests/test_v04_phase2_operator_api_*.py`.

Required behaviors:

- Project onboarding/registration and immutable ProjectSpec version submission;
- approval/activation authority and rejection of invalid/unapproved conflicts;
- independent scopes for onboarding, approvals, intervention, execution and release;
- HumanActionRequest read/verify and owner-verification audit;
- Task/Workflow start/status/cancel through existing authority;
- release/readiness/target reads and publication confirmation;
- required idempotency for material writes and restart-safe replay;
- redacted recovery/status views with zero raw-secret exposure;
- normalized errors/telemetry;
- existing `/api/v1` behavior remains backward-compatible.

## v0.4 Phase 3 — Service Host & Operator CLI

Planned test families: `tests/test_v04_phase3_service_host_*.py`, `tests/test_v04_phase3_operator_cli_*.py`.

Required behaviors:

- installed-wheel service starts with valid config and fails closed on invalid bind/auth/config;
- health/readiness uses existing qualification contracts;
- authenticated requests cannot bypass API scope/idempotency;
- graceful bounded drain/shutdown leaves store reopenable;
- request size/time limits fail deterministically;
- trusted-proxy/TLS-forwarding configuration is explicit;
- CLI uses supported Service API rather than direct control-plane internals;
- CLI/HTTP operations yield equivalent authoritative transitions;
- restart produces no duplicate side effects;
- service + CLI smoke runs outside source checkout.

## v0.4 Phase 4 — GitHub Repository Provider & VCS Handoff

Planned test family: `tests/test_v04_phase4_github_repository_*.py`.

Required behaviors:

- provider availability/auth fails closed;
- repository create vs resolve-existing is deterministic;
- owner/name/visibility mismatch rejected;
- bootstrap conflict protection preserved;
- credentials only from protected references;
- branch/commit/PR/tag operations preserve policy and correlation context;
- protected-branch/permission denial blocks the material operation;
- retry/restart does not duplicate repository/commit/PR/tag;
- partial provider failure is recoverable and auditable;
- normalized rate-limit/auth/not-found/conflict errors;
- owner intervention opens when permissions/availability block automation;
- filesystem repository regression remains green.

## v0.4 Phase 5 — Plugin-Native Release Packaging

Planned test family: `tests/test_v04_phase5_plugin_packaging_*.py`.

Required behaviors:

- `CHATGPT_PLUGIN` generates the approved versioned native package structure;
- skill/resources/manifests resolve internally;
- required/optional app and app-template declarations serialize deterministically;
- native app references validate or fail closed;
- configured GitHub marketplace entries validate;
- invalid manifests/skills/app refs/marketplace refs block readiness;
- legacy Custom Action dependencies remain migration inventory only;
- no selected-model pinning;
- legacy `GPT_STORE` persisted releases remain resumable;
- owner/workspace controls install/share/publication;
- external-format fixtures are explicitly versioned.

## v0.4 Phase 6 — Production Telemetry & Supply Chain

Planned test families: `tests/test_v04_phase6_observability_*.py`, `tests/test_v04_phase6_supply_chain_*.py` plus CI contract tests.

Required behaviors:

- structured logs preserve correlation with deterministic redaction;
- no raw protected secret/private message body emitted by default;
- concrete Prometheus/OpenTelemetry adapters do not change authoritative state;
- exporter timeout/network/failure is isolated and diagnosable;
- service/auth/model/GitHub/release failure paths emit operational evidence;
- dependency inventory/SBOM generation succeeds;
- approved vulnerability gate fails on prohibited fixture and passes clean fixture;
- artifact provenance/attestation evidence is emitted/validated where supported;
- CI policy covers every Python minor actually claimed as supported;
- predecessor trust/resource-hygiene gates remain green.

## v0.4 Phase 7 — End-to-End Product Qualification

Planned test family: `tests/test_v04_phase7_end_to_end_*.py`.

Required behaviors:

- operator API/CLI onboards and approves ProjectSpec without direct control-plane Python calls;
- governed model-backed capability executes and supported GitHub repository path provisions;
- project reaches `FIRST_WORKING` then release preparation and `RELEASE_READY`;
- Plugin-native release assets validate in the same lifecycle;
- owner publication handoff opens without automatic external publication;
- restart/reopen reconstructs Project/workflow/release/target/HumanAction/provider-operation state;
- backup/restore/upgrade preserves expanded v0.4 state;
- blocked owner-wait project does not stop another project;
- provider/telemetry/service failure injection remains deterministic/recoverable;
- installed-wheel service path passes complete operator smoke;
- final exact tree passes full v0.2 + v0.3 + v0.4 regression suite.

## Permanent v0.4 Quality Gates

```text
protected Core Validation                     PASS
full v0.2 + v0.3 + active v0.4 regression   PASS
branch-aware total coverage                   >= 80%
ResourceWarning                               error / PASS
compileall including examples                 PASS
isolated wheel build                          PASS
wheel install outside checkout                PASS
public package/CLI import smoke               PASS
installed service-host smoke                  PASS after Phase 3
secret/redaction regression                   PASS for material new boundaries
restart/recovery regression                   PASS for every durable new state
failure-injection regression                  PASS for every external provider boundary
migration/rollback regression                 PASS for every schema/config contract change
GitHub ruleset / required CI                  enforced
```

## Live External Tests

Normal protected CI remains deterministic and credential-free. Production model/GitHub adapter live smokes are separate owner-controlled workflows or procedures. Where a phase explicitly requires live evidence, its absence blocks that phase's completion claim without blocking unrelated PR validation.

## Activation Rule

ROADMAP v0.4 is approved and Phase 0 is COMPLETE. Phase 1 is READY FOR PRE-IMPLEMENTATION AUDIT; its runtime verification and implementation scope become active only after the separate Phase 1 audit/activation gate is committed through protected governance.
