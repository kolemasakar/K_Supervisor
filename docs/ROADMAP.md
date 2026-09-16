# ROADMAP
K_Supervisor active development roadmap.

Version: 0.4
Status: ACTIVE
Approved: 2026-09-16
Roadmap start: 2026-09-16
Predecessor: ROADMAP v0.3 COMPLETE
Current phase: v0.4 Phase 0 — Baseline Freeze & Operator Product Contract
Phase 0 activation: YES
Runtime implementation authorized: NO — Phase 0 is documentation/baseline only

## Program Objective

Move K_Supervisor from a validated PRE-ALPHA local-first platform into an owner-operable, production-deployable **single-node** product boundary without introducing distributed execution, multi-tenant SaaS semantics or automatic external publication.

The v0.4 program will make the existing control plane practically operable through supported API/CLI surfaces, add a governed production model-inference adapter, one real remote repository provider, current Plugin-native release assets, and stronger operational telemetry/supply-chain evidence.

## Scope Rules

- revision-local phases are `v0.4 Phase 0` through `v0.4 Phase 7`;
- v0.3 Phase 9 remains undefined and must not be used;
- existing public compatibility is preserved unless a phase explicitly defines a versioned migration;
- owner-controlled publication remains a permanent boundary;
- each phase requires its own pre-implementation audit before runtime changes;
- completed v0.2 + v0.3 tests remain the cumulative regression floor.

## v0.4 Phase 0 — Baseline Freeze & Operator Product Contract

**Goal:** freeze the v0.3-complete runtime as the v0.4 predecessor and define the supported single-node product/security/deployment contract before code changes.

**Deliverables:**

- v0.4 baseline/hardening contract with exact predecessor SHA/tree and permanent gates;
- supported deployment topology and trust/threat boundaries;
- operator API/CLI scope and protected-data rules;
- repository-provider and credential boundary;
- current Plugin packaging compatibility snapshot;
- migration/rollback rules and explicit supported Python-version CI policy;
- approved v0.4 `TEST_MATRIX` additions.

**Exit criteria:**

- current `main` and v0.3 runtime ancestry verified;
- product gaps assigned to a phase or explicitly deferred;
- no runtime change in Phase 0;
- protected `Core Validation` PASS on the committed Phase 0 baseline.

**Deferred:** all runtime implementation assigned to Phases 1-7.

## v0.4 Phase 1 — Production Model Provider & AI Execution

**Goal:** connect the existing vendor-neutral MODEL provider contracts to at least one real production inference service while preserving provider independence, policy enforcement and protected credentials.

**Deliverables:**

- first production MODEL provider adapter, initially targeting the current OpenAI Responses API through the generic Provider contract;
- protected-reference API credential resolution with no secret persistence in normal project/audit state;
- vendor-neutral model discovery/profile projection and selection requirements;
- normalized request/response/usage/error metadata without persisting hidden chain-of-thought;
- capability/agent adapter path that can invoke the selected model through `SideEffectGateway` / policy controls rather than direct SDK calls;
- bounded timeout/cancellation/budget accounting and provider availability handling;
- deterministic fake provider for CI plus a separate owner-controlled live smoke path;
- documentation for adding another MODEL provider without Supervisor-core modification.

**Exit criteria:**

- at least one non-reference capability can execute against a real MODEL provider through the governed provider boundary;
- provider credentials remain protected and absent from durable ordinary state/logs;
- policy DENY/REQUIRE_APPROVAL prevents model invocation before the external call;
- timeout/rate-limit/provider failure is normalized, audited and recoverable;
- model selection remains provider-neutral and no specific model is hard-coded as a platform invariant;
- reference offline agents and predecessor provider tests remain compatible;
- a minimal owner-controlled live provider smoke succeeds before Phase 1 completion, without becoming an ordinary PR merge dependency;
- cumulative regression and protected `Core Validation` PASS.

**Deferred:** production-quality bespoke intelligence for every domain/reference agent, mandatory multi-provider routing, model fine-tuning/training and remote-agent federation.

## v0.4 Phase 2 — Operator Control API

**Goal:** let an authenticated owner/operator drive the approved control-plane lifecycle through one versioned service boundary instead of direct Python composition.

**Deliverables:**

- additive `/api/v1` endpoints for Project onboarding/registration and ProjectSpec version submission/approval/activation;
- Human Intervention / approval read and owner-verification operations;
- Task/Workflow execution start, status and cancellation operations through existing runtime authority;
- release/readiness/target status plus owner publication-confirmation operation;
- redacted recovery/status views that never expose protected secret contents;
- domain-specific scopes, idempotency and durable mutation receipts for all material writes;
- normalized conflict/error semantics and service telemetry for new operations.

**Exit criteria:**

- an approved ProjectSpec can be created/approved and advanced through supported lifecycle operations using only Service/API v1 plus existing owner-required external actions;
- denied scopes and invalid transitions fail before authoritative mutation;
- retries/restarts do not duplicate material mutations;
- protected references remain opaque;
- existing Phase 5 API contracts remain backward-compatible;
- cumulative regression and protected `Core Validation` PASS.

**Deferred:** raw secret retrieval, direct Tool/Provider invocation endpoints, administrator-wide multi-tenant RBAC.

## v0.4 Phase 3 — Production Single-Node Service Host & Operator CLI

**Goal:** provide a supported long-running service process and operator client for the Phase 2 API without creating a second control path.

**Deliverables:**

- production-capable service-host adapter/process around the versioned service boundary;
- explicit bind/port/configuration, startup validation, graceful drain/shutdown and bounded request handling;
- authentication configuration through protected references/environment injection;
- health/readiness endpoints wired to existing service/deployment qualification contracts;
- secure reverse-proxy/TLS termination contract and trusted-proxy rules; certificate lifecycle remains external;
- operator CLI commands that call the same Service/API rather than importing control-plane internals;
- installed-wheel service/CLI smoke path and deployment example/runbook update.

**Exit criteria:**

- an installed wheel can start, report readiness, serve authenticated API requests and shut down cleanly;
- CLI and HTTP operations produce equivalent authoritative state transitions;
- malformed/oversized/unauthorized requests fail closed without leaking internals;
- restart preserves durable state and does not create duplicate side effects;
- TLS/reverse-proxy deployment assumptions are explicit and testable at the configuration boundary;
- cumulative regression and protected `Core Validation` PASS.

**Deferred:** certificate issuance/renewal, Kubernetes/operator orchestration, horizontal scaling and multi-node service coordination.

## v0.4 Phase 4 — GitHub Repository Provider & Governed VCS Handoff

**Goal:** let K_Supervisor bootstrap and update a real GitHub repository through existing Project Factory/provisioning/policy boundaries.

**Deliverables:**

- production GitHub repository adapter behind existing repository/provisioning contracts;
- protected-reference credential resolution with no token persistence in normal state/audit;
- repository create/resolve, visibility validation, bootstrap file application and conflict protection;
- governed branch/commit/pull-request operations for project/release artifacts;
- optional release tag preparation when permitted by project policy;
- idempotent retry/recovery semantics for partial provider failures;
- normalized rate-limit/auth/conflict/provider errors and durable correlation/audit;
- owner intervention fallback when credentials, permissions or repository policy block automation.

**Exit criteria:**

- an approved ProjectSpec can bootstrap a new or pre-authorized GitHub repository without Supervisor-core changes;
- repeated/restarted provisioning does not duplicate repositories/commits/PRs unintentionally;
- protected-branch/policy denial cannot be bypassed by the adapter;
- release preparation can produce a governed VCS handoff while external merge/publication remains separate;
- provider failures are normalized, auditable and recoverable;
- cumulative regression and protected `Core Validation` PASS.

**Deferred:** broad cloud/server/database provisioning, GitLab/Bitbucket production adapters, automatic protected-branch merge and distributed repository transactions.

## v0.4 Phase 5 — Plugin-Native ChatGPT/Codex Release Packaging

**Goal:** evolve `CHATGPT_PLUGIN` from portable migration evidence into a versioned, currently importable Plugin package while preserving owner/workspace control.

**Deliverables:**

- versioned native plugin manifest/package generation aligned with the approved current OpenAI format snapshot;
- skill source/resources plus required/optional app and app-template declarations where applicable;
- GitHub marketplace catalog generation/validation for supported import/sync workflows;
- explicit `.app.json`/native app reference handling where supported and requested by ProjectSpec;
- migration inventory for legacy Custom Actions with no implicit conversion claim;
- deterministic package validator and regression-prompt/access evidence;
- retained legacy `GPT_STORE` compatibility path for persisted historical releases;
- compatibility policy for future OpenAI manifest/schema changes.

**Exit criteria:**

- a `CHATGPT_PLUGIN` release produces a self-consistent native package and, when configured, a valid marketplace entry;
- package validation catches missing/invalid skill, app and manifest references before `RELEASE_READY`;
- existing portable evidence remains available or migratable without breaking persisted release state;
- plugin installation/sharing/workspace access/public listing remain explicit owner/admin actions;
- no selected-model pinning or automatic Custom Action migration is introduced;
- cumulative regression and protected `Core Validation` PASS.

**Deferred:** automatic workspace import, automatic public directory publication, provider-account authorization on behalf of the owner.

## v0.4 Phase 6 — Production Telemetry & Supply-Chain Hardening

**Goal:** make the single-node product diagnosable and release artifacts independently inspectable without making external collectors mandatory.

**Deliverables:**

- production structured-log adapter with correlation/redaction rules;
- concrete optional Prometheus/OpenTelemetry exporter adapters behind existing projection contracts;
- exporter failure isolation so telemetry cannot corrupt business/control state;
- service/auth/provider/repository/release operational metrics and audit correlation;
- dependency-vulnerability and dependency-inventory/SBOM generation in CI;
- wheel/artifact provenance/attestation evidence where supported by the repository CI platform;
- explicit supported-Python test matrix matching package metadata claims;
- updated operations/security runbook and failure-injection tests.

**Exit criteria:**

- required platform/service events are observable without secret/private-content leakage;
- exporter/network failure is non-fatal to authoritative control flow and is itself diagnosable;
- package dependency inventory and vulnerability gate run deterministically in CI;
- release artifacts have verifiable build/provenance evidence under the supported CI path;
- every currently released Python minor declared supported by compatibility policy and admitted by package metadata is covered by the approved CI policy;
- cumulative regression and protected `Core Validation` PASS.

**Deferred:** mandatory remote collector infrastructure, full SIEM product integration, universal package-signature infrastructure and arbitrary-code sandboxing.

## v0.4 Phase 7 — End-to-End Single-Node Product Qualification

**Goal:** prove the complete v0.4 owner/operator journey on the supported topology without claiming distributed or automatic-publication capabilities.

**Deliverables:**

- end-to-end qualification from operator API/CLI ProjectSpec onboarding through approval, repository bootstrap, execution, `FIRST_WORKING`, release preparation and `RELEASE_READY`;
- model-backed capability and GitHub repository/VCS paths exercised through deterministic provider fixtures plus separately controlled live smoke evidence for the production adapters;
- Plugin-native package generation/validation in the same lifecycle;
- restart/recovery, backup/restore/upgrade and owner-intervention qualification across the expanded operator/service/provider state;
- concurrent-project qualification with one blocked/owner-waiting project and one progressing project;
- installed-wheel service qualification and final operations runbook;
- v0.4 completion checkpoint with exact implementation tree and protected CI evidence.

**Exit criteria:**

- owner can operate the supported lifecycle through API/CLI without direct control-plane Python calls;
- at least one model-backed capability executes through the governed MODEL provider path and one supported remote repository path is provisioned through governed adapters;
- a Plugin-native release reaches `RELEASE_READY` and stops at the explicit owner/workspace availability/publication boundary;
- restart/backup/restore preserve the expanded state and do not duplicate external actions;
- at least two independent projects remain isolated under concurrency and owner-wait conditions;
- full v0.2 + v0.3 + v0.4 regression suite, packaging, service smoke and protected CI gates PASS;
- roadmap completion does not claim actual PyPI/Plugin public publication.

**Deferred:** all roadmap-level deferred work below.

## Program-Wide Deferred Work

Unless a later explicit revision reapproves them, v0.4 does not include:

- distributed worker clusters, remote-agent federation or multi-node scheduling;
- distributed databases, consensus, cross-region replication or universal external exactly-once guarantees;
- multi-tenant SaaS identity/isolation/billing;
- WhatsApp, Viber, SMS or social notification transports;
- universal sandboxing of arbitrary untrusted Python;
- mandatory event-bus infrastructure;
- broad cloud/server/database provisioning beyond the GitHub repository-provider path;
- external vault products as required platform dependencies;
- certificate issuance/renewal infrastructure;
- automatic PyPI, Plugin Directory, GPT Store or other external publication;
- autonomous expansion of project scope without approved ProjectSpec/roadmap authority.

## Phase Order

```text
Phase 0  Baseline Freeze & Operator Product Contract
Phase 1  Production Model Provider & AI Execution
Phase 2  Operator Control API
Phase 3  Production Single-Node Service Host & Operator CLI
Phase 4  GitHub Repository Provider & Governed VCS Handoff
Phase 5  Plugin-Native ChatGPT/Codex Release Packaging
Phase 6  Production Telemetry & Supply-Chain Hardening
Phase 7  End-to-End Single-Node Product Qualification
```

## Activation Rule

ROADMAP v0.4 was explicitly approved by the owner on 2026-09-16. v0.4 Phase 0 is ACTIVE for documentation, baseline and hardening-contract work only. Runtime implementation remains unauthorized until Phase 0 completion is recorded and the next phase passes its required pre-implementation audit and activation gate.

Canonical approval evidence: `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md`. Phase 0 contract: `HARDENING_BASELINE_V0_4.md`.
