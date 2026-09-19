# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 4.4
Status: ACTIVE
Date: 2026-09-19

## Reading Order

1. `PROJECT_STATE.md` - canonical current implementation and active roadmap state.
2. `DEVELOPMENT_RESOURCE_POLICY.md` - permanent zero-cost development/validation resource policy.
3. `PROJECT_CHECKPOINT_ROADMAP_V0_4_FREE_RESOURCE_AMENDMENT.md` - owner-approved v0.4 policy amendment and Phase 1 impact.
4. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_COMPLETE.md` - authoritative Phase 1 formal completion review.
5. `ROADMAP.md` - approved active ROADMAP v0.4 phase sequence and scope.
6. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md` - Phase 1 original implementation/CI evidence.
7. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
8. `HARDENING_BASELINE_V0_4.md` - frozen v0.4 product/security/compatibility contract.
9. `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md` - explicit owner approval boundary.
10. `POST_V0_3_PRODUCT_GAP_AUDIT.md` - immutable pre-approval audit evidence that produced v0.4.
11. `TEST_MATRIX.md` - active v0.4 verification plan and permanent quality gates.
12. `TEST_MATRIX_V0_3_ARCHIVE.md` - immutable completed v0.2/v0.3 cumulative test evidence.
13. `VISION.md` - product direction and success definition.
14. `OPERATIONS_RUNBOOK.md` - deployment, backup/restore/upgrade, recovery and publication procedures.
15. `COMPATIBILITY_POLICY.md` - public compatibility rules.
16. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
17. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
18. `ARCHITECTURE.md` - control plane and multi-agent core.
19. `PERSISTENCE.md` - storage and operational recovery semantics.
20. `AGENT_RUNTIME.md` - runtime execution control.
21. `INTEGRATIONS.md` - tools, providers, model-selection contracts and side-effect gateway.
22. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
23. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability and deployment qualification.
24. `SERVICE_API.md` - versioned Service/API contracts.
25. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - ChatGPT release-target compatibility decision.
26. `RELEASE_MANAGER.md` - release targets and owner/workspace publication boundary.
27. `ROADMAP_V0_3_ARCHIVE.md` - immutable completed predecessor roadmap snapshot.
28. `PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` - v0.3 final closure evidence.
29. `ROADMAP_V0_2_ARCHIVE.md` - completed v0.2 predecessor snapshot.

Historical phase checkpoints and transition handoffs remain preserved and are not rewritten to reflect later roadmap state.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: COMPLETE
v0.4 Phase 2-7: PLANNED
Runtime implementation phase: NONE
v0.3 Phase 9: NOT DEFINED
```

## Phase 0 Governance Evidence

```text
Activation PR: #10
Core Validation: 35143639772 — PASS
Activation/merged tree: c19e76192ab98003060bd86e5a193676029b358b
Merged main SHA: b559f3a6158566531e2896e91ced817484d6f152
Runtime paths changed: NONE
```

## Phase 1 Implementation Evidence

```text
Implementation PR: #14
Implementation tree: 7fabf5220d4370124bb245445c84f9ed77eb2041
Protected PR Core Validation: 35175344558 — PASS
Merged main SHA: 8f748e993737cebe45a6e8ebaac74d8c0e10d1b7
Merged-main Core Validation: 35175392964 — PASS
Live OpenAI Responses attempt: REACHED PROVIDER / credit_balance_exhausted
Paid retry for development validation: PROHIBITED
Phase 1 completion: COMPLETE
Gap-closure Core Validation: 35440664106 — PASS / 192 tests / 84.86% coverage
Phase 2 activation: NO
```

## Current Runtime Baseline

```text
Implementation PR: #14
Implementation head: 0d6a3ed863c687ec9461135a306180014c248312
Implementation tree: 7fabf5220d4370124bb245445c84f9ed77eb2041
Validated runtime main SHA: 8f748e993737cebe45a6e8ebaac74d8c0e10d1b7
Protected PR Core Validation: 35175344558 — PASS
Merged-main Core Validation: 35175392964 — PASS
Python workflow: 3.13
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
Live OpenAI Responses attempt: REACHED PROVIDER / credit_balance_exhausted
```

## Repository Governance

Ruleset `main-core-validation` (id `23556478`) is active on the default branch, requires pull requests and `Core Validation`, blocks deletion/non-fast-forward updates, and has no bypass actors.

## Compatibility / Publication Boundary

Preferred ChatGPT target remains `CHATGPT_PLUGIN`; legacy `GPT_STORE` remains a persisted compatibility path. External availability/publication remains owner/workspace controlled. Automatic external publication remains out of scope.

## Next Work Rule

Phase 1 is COMPLETE under the amended zero-cost criteria. The next permitted work is the Phase 2 pre-implementation audit. Phase 2 runtime remains inactive until its own audit/activation gate is approved and merged through protected governance.
