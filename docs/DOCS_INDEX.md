# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 4.2
Status: ACTIVE
Date: 2026-09-17

## Reading Order

1. `PROJECT_STATE.md` - canonical current implementation and active roadmap state.
2. `ROADMAP.md` - approved active ROADMAP v0.4 phase sequence and scope.
3. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md` - current Phase 1 implementation/CI evidence; live smoke pending.
4. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md` - current Phase 0 completion evidence and next gate.
5. `HARDENING_BASELINE_V0_4.md` - frozen v0.4 product/security/compatibility contract.
6. `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md` - explicit owner approval boundary.
7. `POST_V0_3_PRODUCT_GAP_AUDIT.md` - immutable pre-approval audit evidence that produced v0.4.
8. `TEST_MATRIX.md` - active v0.4 verification plan and permanent quality gates.
9. `TEST_MATRIX_V0_3_ARCHIVE.md` - immutable completed v0.2/v0.3 cumulative test evidence.
10. `VISION.md` - product direction and success definition.
11. `OPERATIONS_RUNBOOK.md` - current deployment, backup/restore/upgrade, recovery and publication procedures.
12. `COMPATIBILITY_POLICY.md` - public compatibility rules.
13. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
14. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
15. `ARCHITECTURE.md` - control plane and multi-agent core.
16. `PERSISTENCE.md` - storage and operational recovery semantics.
17. `AGENT_RUNTIME.md` - runtime execution control.
18. `INTEGRATIONS.md` - tools, providers, model-selection contracts and side-effect gateway.
19. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
20. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability and deployment qualification.
21. `SERVICE_API.md` - versioned Service/API contracts.
22. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - ChatGPT release-target compatibility decision.
23. `RELEASE_MANAGER.md` - release targets and owner/workspace publication boundary.
24. `ROADMAP_V0_3_ARCHIVE.md` - immutable completed predecessor roadmap snapshot.
25. `PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` - v0.3 final closure evidence.
26. `ROADMAP_V0_2_ARCHIVE.md` - completed v0.2 predecessor snapshot.

Historical phase checkpoints and transition handoffs remain preserved and are not rewritten to reflect later roadmap state.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: ACTIVE — IMPLEMENTED / LIVE SMOKE PENDING
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
Live OpenAI Responses smoke: PENDING
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
Live OpenAI Responses smoke: PENDING
```

## Repository Governance

Ruleset `main-core-validation` (id `23556478`) is active on the default branch, requires pull requests and `Core Validation`, blocks deletion/non-fast-forward updates, and has no bypass actors.

## Compatibility / Publication Boundary

Preferred ChatGPT target remains `CHATGPT_PLUGIN`; legacy `GPT_STORE` remains a persisted compatibility path. External availability/publication remains owner/workspace controlled. Automatic external publication remains out of scope.

## Next Work Rule

Phase 1 runtime is merged and CI-validated. The next required gate is the owner-controlled live OpenAI Responses smoke using an approved protected credential reference. Do not mark Phase 1 COMPLETE or activate Phase 2 until that smoke evidence is recorded through protected governance.
