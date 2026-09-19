# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 4.9
Status: ACTIVE
Date: 2026-09-19

## Reading Order

1. `PROJECT_STATE.md` - canonical current implementation and active roadmap state.
2. `PROJECT_HANDOFF_2026_09_19_V0_4_PHASE3_ACTIVATION.md` - current transition handoff for the next chat and Phase 3 activation decision.
3. `DEVELOPMENT_RESOURCE_POLICY.md` - permanent zero-cost development/validation resource policy.
4. `V0_4_PHASE3_PREIMPLEMENTATION_AUDIT.md` - completed v0.4 Phase 3 service-host/operator-CLI pre-implementation audit.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_COMPLETE.md` - authoritative Phase 2 completion evidence.
6. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_ACTIVATED.md` - owner-approved Phase 2 activation checkpoint.
7. `V0_4_PHASE2_PREIMPLEMENTATION_AUDIT.md` - completed Phase 2 Operator Control API pre-implementation audit.
8. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_COMPLETE.md` - authoritative Phase 1 completion review.
9. `PROJECT_CHECKPOINT_ROADMAP_V0_4_FREE_RESOURCE_AMENDMENT.md` - owner-approved zero-cost v0.4 policy amendment.
10. `ROADMAP.md` - approved active ROADMAP v0.4 sequence and scope.
11. `TEST_MATRIX.md` - active cumulative v0.4 verification contract.
12. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md` - Phase 1 original implementation evidence.
13. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
14. `HARDENING_BASELINE_V0_4.md` - frozen v0.4 product/security/compatibility contract.
15. `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md` - explicit owner approval boundary.
16. `POST_V0_3_PRODUCT_GAP_AUDIT.md` - immutable audit that produced v0.4.
17. `TEST_MATRIX_V0_3_ARCHIVE.md` - immutable completed v0.2/v0.3 regression evidence.
18. `VISION.md` - product direction and success definition.
19. `OPERATIONS_RUNBOOK.md` - deployment, backup/restore/upgrade and recovery procedures.
20. `COMPATIBILITY_POLICY.md` - public compatibility rules.
21. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
22. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
23. `ARCHITECTURE.md` - control plane and multi-agent core.
24. `PERSISTENCE.md` - storage and recovery semantics.
25. `AGENT_RUNTIME.md` - runtime execution control.
26. `INTEGRATIONS.md` - tools/providers/model-selection/side-effect gateway.
27. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
28. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability and deployment qualification.
29. `SERVICE_API.md` - currently implemented v1 Service/API contract.
30. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - ChatGPT release-target compatibility decision.
31. `RELEASE_MANAGER.md` - release targets and owner publication boundary.
32. `ROADMAP_V0_3_ARCHIVE.md` - immutable completed predecessor roadmap.
33. `PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` - v0.3 closure evidence.
34. `ROADMAP_V0_2_ARCHIVE.md` - completed v0.2 predecessor snapshot.

Historical phase checkpoints and transition handoffs remain preserved and are not rewritten to reflect later roadmap state.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: COMPLETE
v0.4 Phase 2: COMPLETE
v0.4 Phase 3: PLANNED — AUDIT COMPLETE / ACTIVATION PENDING
v0.4 Phase 4-7: PLANNED
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
Phase 2 activation: YES — PR #23 / Core Validation 35442514671 — PASS
```

## Current Runtime Baseline

```text
Phase 2 implementation PR: #24
Validated code/test head: f9f7284c407734fc2a3286f755c6827229142514
Validated code/test tree: abf48bbbfc2fe5e69c08fb7f6c8f3e9faee1b7ea
Code/test Core Validation: 35443690831 — PASS
Final PR head: 067828dfb6618ab412dfdfc64045cff9e8ea9cef
Final exact-head Core Validation: 35443735846 — PASS
Merged main SHA: 9b532e4dd7c3aaaaaab2beaea97a3b017b7fff56
Merged-main Core Validation: 35443778180 — PASS
Full regression: 214 passed
Branch-aware coverage: 83.21%
```

## Phase 3 Audit Evidence

```text
Audit PR: #26
Final audit head: 31eff0be47afdbc5837aa08595f3553d9bf022ca
Final audit tree: 241b9588ecbaf8f9ec02c31f71562d0a0867cf96
Final exact-head Core Validation: 35445489807 — PASS
Audit merged main: 31e39bf44e43ca241fb2536aa30bdfc519e0f020
Runtime/source/test paths changed: NONE
```

## Repository Governance

Ruleset `main-core-validation` (id `23556478`) is active on the default branch, requires pull requests and `Core Validation`, blocks deletion/non-fast-forward updates, and has no bypass actors.

## Compatibility / Publication Boundary

Preferred ChatGPT target remains `CHATGPT_PLUGIN`; legacy `GPT_STORE` remains a persisted compatibility path. External availability/publication remains owner/workspace controlled. Automatic external publication remains out of scope.

## Next Work Rule

Phase 0, Phase 1 and Phase 2 are COMPLETE. Phase 3 pre-implementation audit is COMPLETE, but Phase 3 remains PLANNED / INACTIVE pending explicit owner approval and a separate protected activation checkpoint. Phase 4-7 remain inactive.
