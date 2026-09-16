# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 4.1
Status: ACTIVE
Date: 2026-09-16

## Reading Order

1. `PROJECT_STATE.md` - canonical current implementation and active roadmap state.
2. `ROADMAP.md` - approved active ROADMAP v0.4 phase sequence and scope.
3. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md` - current Phase 0 completion evidence and next gate.
4. `HARDENING_BASELINE_V0_4.md` - frozen v0.4 product/security/compatibility contract.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md` - explicit owner approval boundary.
6. `POST_V0_3_PRODUCT_GAP_AUDIT.md` - immutable pre-approval audit evidence that produced v0.4.
7. `TEST_MATRIX.md` - active v0.4 verification plan and permanent quality gates.
8. `TEST_MATRIX_V0_3_ARCHIVE.md` - immutable completed v0.2/v0.3 cumulative test evidence.
9. `VISION.md` - product direction and success definition.
10. `OPERATIONS_RUNBOOK.md` - current deployment, backup/restore/upgrade, recovery and publication procedures.
11. `COMPATIBILITY_POLICY.md` - public compatibility rules.
12. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
13. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
14. `ARCHITECTURE.md` - control plane and multi-agent core.
15. `PERSISTENCE.md` - storage and operational recovery semantics.
16. `AGENT_RUNTIME.md` - runtime execution control.
17. `INTEGRATIONS.md` - tools, providers, model-selection contracts and side-effect gateway.
18. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
19. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability and deployment qualification.
20. `SERVICE_API.md` - versioned Service/API contracts.
21. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - ChatGPT release-target compatibility decision.
22. `RELEASE_MANAGER.md` - release targets and owner/workspace publication boundary.
23. `ROADMAP_V0_3_ARCHIVE.md` - immutable completed predecessor roadmap snapshot.
24. `PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` - v0.3 final closure evidence.
25. `ROADMAP_V0_2_ARCHIVE.md` - completed v0.2 predecessor snapshot.

Historical phase checkpoints and transition handoffs remain preserved and are not rewritten to reflect later roadmap state.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: READY FOR PRE-IMPLEMENTATION AUDIT
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

## Current Runtime Baseline

```text
Implementation commit: f0c9bc30a5562c83803a861aafe6f669a2ae4730
Implementation tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Validated runtime main SHA: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Protected PR Core Validation: 35134961231 — PASS
Merged-main Core Validation: 35135133947 — PASS
Python workflow: 3.13
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

## Repository Governance

Ruleset `main-core-validation` (id `23556478`) is active on the default branch, requires pull requests and `Core Validation`, blocks deletion/non-fast-forward updates, and has no bypass actors.

## Compatibility / Publication Boundary

Preferred ChatGPT target remains `CHATGPT_PLUGIN`; legacy `GPT_STORE` remains a persisted compatibility path. External availability/publication remains owner/workspace controlled. Automatic external publication remains out of scope.

## Next Work Rule

The next work item is the v0.4 Phase 1 pre-implementation audit. Do not begin production MODEL-provider runtime code until the audit/activation gate is committed through protected `main` governance.
