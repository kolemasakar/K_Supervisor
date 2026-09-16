# TEST_MATRIX v0.4 — DRAFT
Proposed additions to the permanent K_Supervisor regression floor for ROADMAP v0.4.

Version: 0.4-draft.1
Status: DRAFT / NOT APPROVED / NOT ACTIVE
Date: 2026-09-16

## Preserved Regression Floor

All completed v0.2 and v0.3 tests remain mandatory. The v0.3 authoritative runtime baseline is:

```text
Validated runtime main: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Runtime tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Merged-main Core Validation: 35135133947 — PASS
Local exact-tree result: 163 passed / 85.82% branch coverage
```

No v0.4 test may weaken the permanent coverage, ResourceWarning, compile, wheel install or public-interface smoke gates.

## v0.4 Phase 0 — Baseline & Contract Tests

Proposed verification:

- exact current-main ancestry against the v0.3 runtime/closure baselines;
- public package/CLI/config/Service API/extension compatibility inventory;
- repository ruleset and required `Core Validation` verification;
- deferred-scope classification completeness;
- supported deployment topology/threat-boundary documentation consistency;
- current external Plugin format snapshot recorded before implementation;
- no runtime diff in Phase 0.

## v0.4 Phase 1 — Production Model Provider & AI Execution

Proposed test families: `tests/test_v04_phase1_model_provider_*.py`.

Required behaviors:

- production MODEL adapter availability and configuration validation;
- protected-reference API credential resolution with no clear-text persistence/logging;
- model profiles project into vendor-neutral candidates and selection requirements;
- selected provider/model request is executed only through the governed Provider/SideEffectGateway path;
- policy ALLOW invokes once; DENY invokes zero times; REQUIRE_APPROVAL invokes only after valid approval;
- timeout/cancellation/budget/rate-limit/provider errors normalize deterministically;
- usage/request/provider correlation is captured without hidden chain-of-thought persistence;
- retry/idempotency rules do not cause unintended duplicate material provider effects;
- deterministic fake provider supports normal CI without credentials/network;
- owner-controlled live smoke is separate from ordinary protected PR merge gates and is required as Phase 1 completion evidence for the production adapter;
- reference offline agents and generic Provider/registry regressions remain green.

## v0.4 Phase 2 — Operator Control API

Proposed test families: `tests/test_v04_phase2_operator_api_*.py`.

Required behaviors:

- Project onboarding/registration from valid ProjectSpec input;
- ProjectSpec immutable version creation, approval and activation rules;
- invalid/unapproved/materially conflicting ProjectSpec mutations rejected;
- independent read/write scopes for onboarding, approvals, execution, intervention and release operations;
- HumanActionRequest list/get/verify semantics and owner-verification audit;
- Task/Workflow start/status/cancel through existing control-plane authority;
- release/readiness/target reads and publication-confirmation authority;
- required idempotency key for material writes;
- same-key/same-request replay and same-key/different-request conflict;
- restart-safe mutation replay without duplicate transitions/side effects;
- redacted recovery/status views and zero raw-secret exposure;
- normalized errors and telemetry on successful/failed operations;
- all existing `/api/v1` Phase 5 behavior remains compatible.

## v0.4 Phase 3 — Service Host & Operator CLI

Proposed test families: `tests/test_v04_phase3_service_host_*.py`, `tests/test_v04_phase3_operator_cli_*.py`.

Required behaviors:

- installed-wheel service process starts with valid configuration;
- invalid bind/auth/config fails before accepting requests;
- health/readiness reflect existing service/deployment qualification;
- authenticated requests reach ServiceApiV1 without bypassing scope/idempotency enforcement;
- graceful shutdown drains bounded in-flight work and leaves store reopenable;
- request size/time/boundary limits fail deterministically;
- trusted-proxy/TLS-forwarding configuration is explicit and untrusted forwarding metadata is rejected/ignored as designed;
- CLI commands call the supported API surface rather than direct registries/managers;
- CLI exit codes and normalized errors are stable;
- service restart reconstructs state with no duplicate side effects;
- wheel-install service + CLI smoke runs outside the source checkout.

## v0.4 Phase 4 — GitHub Repository Provider & VCS Handoff

Proposed test families: `tests/test_v04_phase4_github_repository_*.py`.

Required behaviors:

- provider availability/authentication checks fail closed;
- repository create vs resolve-existing behavior is deterministic;
- visibility/owner/name mismatches are rejected rather than silently coerced;
- bootstrap writes preserve conflict protection and do not overwrite unauthorized content;
- credentials are resolved only from protected references and never persisted/logged in clear text;
- branch/commit/PR/tag operations carry project/request correlation and policy context;
- protected-branch or permission denial blocks the material operation;
- repeated request/restart after success does not duplicate repository/commit/PR/tag;
- partial provider failure records recoverable state and safe retry behavior;
- rate-limit/auth/not-found/conflict errors normalize consistently;
- owner intervention opens when credentials/permissions/provider availability prevent automation;
- filesystem repository regression remains green.

## v0.4 Phase 5 — Plugin-Native Release Packaging

Proposed test families: `tests/test_v04_phase5_plugin_packaging_*.py`.

Required behaviors:

- `CHATGPT_PLUGIN` generates the approved versioned native manifest/package structure;
- required skill/resources are present and internally referenced paths resolve;
- required/optional app and app-template declarations serialize deterministically;
- configured native app references validate or fail closed;
- configured GitHub marketplace catalog contains valid plugin source/name references;
- invalid/missing manifests, skills, app references or marketplace entries block readiness;
- legacy Custom Action dependencies remain explicit migration inventory only;
- selected-model pinning remains absent;
- legacy `GPT_STORE` persisted releases remain readable/resumable;
- current portable plugin evidence remains compatible or has a tested migration path;
- package access/install/share/publication remains owner/workspace-admin controlled;
- external-format fixtures are versioned so a future format change fails visibly rather than being guessed.

## v0.4 Phase 6 — Production Telemetry & Supply Chain

Proposed test families: `tests/test_v04_phase6_observability_*.py`, `tests/test_v04_phase6_supply_chain_*.py` plus CI contract tests.

Required behaviors:

- structured logs preserve project/request/correlation identifiers with deterministic redaction;
- no raw protected secret or private message body is emitted by default;
- Prometheus/OpenTelemetry adapters project existing telemetry without changing authoritative state;
- exporter timeout/network/failure is isolated and auditable;
- service/auth/GitHub/release failure paths produce required operational evidence;
- dependency inventory/SBOM generation succeeds from the committed package metadata;
- approved vulnerability gate fails on injected prohibited findings and passes the clean fixture;
- artifact provenance/attestation evidence is emitted/validated on the supported CI path;
- CI tests every currently released Python minor declared supported by compatibility policy and admitted by package metadata;
- predecessor extension trust/governance and ResourceWarning gates remain green.

## v0.4 Phase 7 — End-to-End Product Qualification

Proposed test families: `tests/test_v04_phase7_end_to_end_*.py`.

Required behaviors:

- operator API/CLI can onboard and approve a ProjectSpec without direct control-plane Python calls;
- a model-backed capability executes through the governed MODEL provider contract and the supported GitHub repository path is provisioned through its governed adapter contract;
- project reaches `FIRST_WORKING`, release preparation and `RELEASE_READY` through existing lifecycle authority;
- Plugin-native release assets validate in the same end-to-end lifecycle;
- required publication handoff opens and project enters the expected owner-wait state without automatic external publication;
- restart/reopen reconstructs Project, workflow, release, target, HumanAction and provider-operation state;
- backup/restore/upgrade qualification preserves the expanded v0.4 state;
- one owner-blocked project does not stop another independent project from progressing;
- provider/telemetry/service failure injection leaves authoritative state deterministic and recoverable;
- installed-wheel service path passes the complete operator smoke scenario;
- final exact implementation tree passes the complete v0.2 + v0.3 + v0.4 regression suite.

## Proposed Permanent v0.4 Quality Gates

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

Normal protected CI must remain deterministic and credential-free. Production OpenAI/GitHub adapter live smokes are separate owner-controlled workflows or procedures and are not ordinary pull-request merge gates. Where a phase explicitly requires live-smoke evidence for completion, failure or absence of that evidence blocks the phase completion claim without blocking unrelated PR validation.

## Approval Gate

This test matrix is a proposal. It becomes enforceable only after explicit ROADMAP v0.4 approval and protected-main synchronization of the canonical `TEST_MATRIX.md`.
