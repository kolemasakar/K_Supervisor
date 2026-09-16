# PROJECT_STATE
Canonical current snapshot of K_Supervisor after explicit ROADMAP v0.4 approval and Phase 0 activation.

Version: 4.0
Status: ACTIVE
Date: 2026-09-16

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Package: k-supervisor==0.1.0
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: ACTIVE — documentation/baseline only
v0.4 Phase 1-7: PLANNED
Current approved implementation phase: v0.4 Phase 0
Runtime implementation phase: NONE
v0.3 Phase 9: NOT DEFINED
```

## Current Validated Runtime Baseline

```text
Implementation commit: f0c9bc30a5562c83803a861aafe6f669a2ae4730
Implementation tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Validated main SHA: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Protected PR Core Validation: 35134961231 — PASS
Merged-main Core Validation: 35135133947 — PASS
Python workflow: 3.13
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Exact-tree local cumulative verification before v0.3 merge produced `163 passed` and branch-aware coverage `85.82%` on Python 3.12.3. GitHub Actions Python 3.13 remains authoritative. The v0.4 activation work changes documentation only and does not replace this runtime baseline.

## v0.4 Approval State

ROADMAP v0.4 was explicitly approved on 2026-09-16. Approval evidence: `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md`.

The approved product target is an owner-operable, production-deployable single-node K_Supervisor with a governed production model-inference path, complete operator API/CLI surface, a production GitHub repository/VCS adapter, current Plugin-native release packaging, concrete telemetry/supply-chain evidence, and final end-to-end product qualification.

The post-v0.3 audit is `POST_V0_3_PRODUCT_GAP_AUDIT.md`. The frozen v0.4 contract is `HARDENING_BASELINE_V0_4.md`.

## v0.4 Phase State

```text
Phase 0  Baseline Freeze & Operator Product Contract                 ACTIVE
Phase 1  Production Model Provider & AI Execution                   PLANNED
Phase 2  Operator Control API                                       PLANNED
Phase 3  Production Single-Node Service Host & Operator CLI         PLANNED
Phase 4  GitHub Repository Provider & Governed VCS Handoff          PLANNED
Phase 5  Plugin-Native ChatGPT/Codex Release Packaging              PLANNED
Phase 6  Production Telemetry & Supply-Chain Hardening              PLANNED
Phase 7  End-to-End Single-Node Product Qualification               PLANNED
```

Phase 0 authorizes documentation/baseline/hardening-contract work only. Runtime changes begin only after Phase 0 completion and the next active phase's pre-implementation audit/activation gate.

## Repository Governance

Repository ruleset `main-core-validation` (id `23556478`) protects the default branch, requires pull requests and GitHub Actions `Core Validation`, blocks deletion/non-fast-forward updates, and has no bypass actors. This remains the minimum v0.4 merge gate.

## ChatGPT Compatibility Boundary

```text
Preferred ChatGPT release target: CHATGPT_PLUGIN
Legacy migration compatibility: GPT_STORE
Custom Action auto-migration: NO
Selected ChatGPT model pinning: NO
External availability/publication: owner/workspace-admin controlled
```

v0.4 Phase 5 may evolve `CHATGPT_PLUGIN` packaging to the approved current native Plugin/marketplace format, but installation, sharing, authorization and publication remain owner/workspace-admin actions.

## Public Compatibility Baseline

```text
Python facade: ksupervisor
Service facade: ksupervisor.service
Service API: /api/v1
CLI: k-supervisor
Config version: 1
Extension groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

Additive compatible evolution is the default. Any intentional version break requires an explicit approved migration.

## v0.4 Deferred Boundary

v0.4 does not approve distributed worker clusters/remote-agent federation, distributed DB/consensus/cross-region replication, multi-tenant SaaS identity/billing, non-email owner transports, universal arbitrary-Python sandboxing, mandatory event-bus architecture, broad cloud provisioning, automatic certificate lifecycle, or automatic external publication.

## Validation Rule

Completed v0.2 and v0.3 suites remain the cumulative regression floor. Phase-specific v0.4 tests are additive. No runtime phase may claim completion without its committed implementation baseline, phase-specific evidence, required external live-smoke evidence where explicitly specified, and protected `Core Validation` PASS.
