# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 4.3
Status: ACTIVE
Date: 2026-09-19

## Reading Order

1. `PROJECT_STATE.md` - canonical current implementation and active roadmap state.
2. `DEVELOPMENT_RESOURCE_POLICY.md` - permanent zero-cost development/validation resource policy.
3. `PROJECT_CHECKPOINT_ROADMAP_V0_4_FREE_RESOURCE_AMENDMENT.md` - owner-approved v0.4 policy amendment and Phase 1 impact.
4. `ROADMAP.md` - approved active ROADMAP v0.4 phase sequence and scope.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md` - Phase 1 implementation/CI evidence.
6. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md` - Phase 0 completion evidence and predecessor gate.
7. `HARDENING_BASELINE_V0_4.md` - frozen v0.4 product/security/compatibility contract.
8. `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md` - explicit owner approval boundary.
9. `POST_V0_3_PRODUCT_GAP_AUDIT.md` - immutable pre-approval audit evidence that produced v0.4.
10. `TEST_MATRIX.md` - active v0.4 verification plan and permanent quality gates.
11. `TEST_MATRIX_V0_3_ARCHIVE.md` - immutable completed v0.2/v0.3 cumulative test evidence.
12. `VISION.md` - product direction and success definition.
13. `OPERATIONS_RUNBOOK.md` - deployment, backup/restore/upgrade, recovery and publication procedures.
14. `COMPATIBILITY_POLICY.md` - public compatibility rules.
15. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
16. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
17. `ARCHITECTURE.md` - control plane and multi-agent core.
18. `PERSISTENCE.md` - storage and operational recovery semantics.
19. `AGENT_RUNTIME.md` - runtime execution control.
20. `INTEGRATIONS.md` - tools, providers, model-selection contracts and side-effect gateway.
21. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
22. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability and deployment qualification.
23. `SERVICE_API.md` - versioned Service/API contracts.
24. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - ChatGPT release-target compatibility decision.
25. `RELEASE_MANAGER.md` - release targets and owner/workspace publication boundary.
26. `ROADMAP_V0_3_ARCHIVE.md` - immutable completed predecessor roadmap snapshot.
27. `PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` - v0.3 final closure evidence.
28. `ROADMAP_V0_2_ARCHIVE.md` - completed v0.2 predecessor snapshot.

Historical phase checkpoints and transition handoffs remain preserved and are not rewritten to reflect later roadmap state.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: ACTIVE — IMPLEMENTED / FREE-RESOURCE COMPLETION REVIEW
v0.4 Phase 2-7: PLANNED
Runtime implementation phase: v0.4 Phase 1
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

Phase 1 runtime is merged and CI-validated. Under `DEVELOPMENT_RESOURCE_POLICY.md`, paid OpenAI credits must not be purchased for development validation and successful paid live inference is no longer a blocking gate. The next required step is a formal Phase 1 completion review against the amended zero-cost criteria. Phase 2 remains inactive until that completion is merged through protected governance.
