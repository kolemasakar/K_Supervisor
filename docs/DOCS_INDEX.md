# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 6.4
Status: ACTIVE
Date: 2026-09-23

## Reading Order

1. `PROJECT_STATE.md` - canonical current implementation and active roadmap state.
2. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_6_ACTIVATED.md` - owner-approved protected activation checkpoint for the audited Phase 6 telemetry/supply-chain implementation scope.
3. `V0_4_PHASE6_PREIMPLEMENTATION_AUDIT.md` - completed Phase 6 telemetry/supply-chain pre-implementation audit and activation boundary.
4. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_5_COMPLETE.md` - authoritative Phase 5 completion and qualification evidence for native Plugin packaging.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_5_ACTIVATED.md` - owner-approved protected activation checkpoint for the audited Phase 5 implementation scope.
6. `V0_4_PHASE5_PREIMPLEMENTATION_AUDIT.md` - completed Phase 5 Plugin-native packaging pre-implementation audit and activation boundary.
7. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_4_COMPLETE.md` - authoritative Phase 4 completion evidence for the governed GitHub repository/VCS provider and operator surface.
8. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_4_ACTIVATED.md` - owner-approved protected activation checkpoint for the audited Phase 4 implementation scope.
9. `V0_4_PHASE4_PREIMPLEMENTATION_AUDIT.md` - completed Phase 4 GitHub repository/VCS pre-implementation audit and activation boundary.
10. `PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_COMPLETE_2026_09_22.md` - authoritative completion evidence for the guarded ARM64 self-hosted Core Validation migration and recovery cleanup.
11. `PROJECT_CHECKPOINT_SELF_HOSTED_CI_PREFLIGHT_2026_09_20.md` - completed read-only bootstrap/VM preflight, verified artifact digest and approved resource guardrails.
12. `PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_APPROVED_2026_09_19.md` - approved zero-cost self-hosted Core Validation migration architecture, security boundaries, acceptance criteria and rollback.
13. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_COMPLETE.md` - authoritative Phase 3 completion evidence.
14. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_IMPLEMENTED.md` - Phase 3 implementation evidence.
15. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_ACTIVATED.md` - owner-approved Phase 3 activation checkpoint and protected merge gate.
16. `PROJECT_HANDOFF_2026_09_19_V0_4_PHASE3_ACTIVATION.md` - transition handoff that led to the Phase 3 activation decision.
17. `DEVELOPMENT_RESOURCE_POLICY.md` - permanent zero-cost development/validation resource policy.
18. `V0_4_PHASE3_PREIMPLEMENTATION_AUDIT.md` - completed v0.4 Phase 3 service-host/operator-CLI pre-implementation audit.
19. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_COMPLETE.md` - authoritative Phase 2 completion evidence.
20. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_ACTIVATED.md` - owner-approved Phase 2 activation checkpoint.
21. `V0_4_PHASE2_PREIMPLEMENTATION_AUDIT.md` - completed Phase 2 Operator Control API pre-implementation audit.
22. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_COMPLETE.md` - authoritative Phase 1 completion review.
23. `PROJECT_CHECKPOINT_ROADMAP_V0_4_FREE_RESOURCE_AMENDMENT.md` - owner-approved zero-cost v0.4 policy amendment.
24. `ROADMAP.md` - approved active ROADMAP v0.4 sequence and scope.
25. `TEST_MATRIX.md` - active cumulative v0.4 verification contract.
26. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md` - Phase 1 original implementation evidence.
27. `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
28. `HARDENING_BASELINE_V0_4.md` - frozen v0.4 product/security/compatibility contract.
29. `PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED.md` - explicit owner approval boundary.
30. `POST_V0_3_PRODUCT_GAP_AUDIT.md` - immutable audit that produced v0.4.
31. `TEST_MATRIX_V0_3_ARCHIVE.md` - immutable completed v0.2/v0.3 regression evidence.
32. `VISION.md` - product direction and success definition.
33. `OPERATIONS_RUNBOOK.md` - deployment, backup/restore/upgrade, Phase 6 observability, vulnerability evidence and trusted-main attestation procedures.
34. `SUPPLY_CHAIN_SECURITY.md` - Phase 6 dependency locks, SPDX SBOM, vulnerability evidence, immutable Action pins and trusted-main attestation security contract.
35. `COMPATIBILITY_POLICY.md` - public compatibility rules.
36. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
37. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
38. `ARCHITECTURE.md` - control plane and multi-agent core.
39. `PERSISTENCE.md` - storage and recovery semantics.
40. `AGENT_RUNTIME.md` - runtime execution control.
41. `INTEGRATIONS.md` - tools/providers/model-selection/side-effect gateway.
42. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
43. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability and deployment qualification.
44. `SERVICE_API.md` - currently implemented v1 Service/API contract.
45. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - ChatGPT release-target compatibility decision.
46. `RELEASE_MANAGER.md` - release targets and owner publication boundary.
47. `ROADMAP_V0_3_ARCHIVE.md` - immutable completed predecessor roadmap.
48. `PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` - v0.3 closure evidence.
49. `ROADMAP_V0_2_ARCHIVE.md` - completed v0.2 predecessor snapshot.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: COMPLETE
v0.4 Phase 2: COMPLETE
v0.4 Phase 3: COMPLETE
v0.4 Phase 4: COMPLETE
v0.4 Phase 5: COMPLETE
v0.4 Phase 6: ACTIVATED — IMPLEMENTATION AUTHORIZED
v0.4 Phase 7: PLANNED / INACTIVE
Runtime implementation phase: v0.4 Phase 6 — audited scope only
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
Phase 3 implementation PR: #29
Final PR head: c73e4c5f24f958ebb1473d4c8d23f28244c9f799
Final PR tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Final exact-head Core Validation: 35453258878 — PASS
Merged main SHA: a1791b607496edfaf84593d753f7d1d7662eede1
Merged-main Core Validation: 35453297160 — PASS
Full regression: 229 passed
Branch-aware coverage: 82.06%
Installed-wheel Phase 3 service/CLI smoke: PASS
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

## CI Migration State

```text
Migration: COMPLETE
Completion checkpoint: PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_COMPLETE_2026_09_22.md
Migration PR: #32
Merged main: 2945871da17531552ff36f7e22e5cdf19afe1375
Self-hosted pre-PR push run: 35729485398 — PASS
Protected PR Core Validation: 35729696043 — PASS
Merged-main Core Validation: 35731755438 — PASS
Runner: kgm-e4-owner-pilot
Runner selector: [self-hosted, linux, arm64, k-supervisor-ci]
Runner account: ghrunner
Required check context: Core Validation — UNCHANGED
Public-repo external contributor approval: REQUIRE ALL EXTERNAL
Recovery surface cleanup: COMPLETE
ROADMAP Phase 4 activation: NO
```

## Compatibility / Publication Boundary

Preferred ChatGPT target remains `CHATGPT_PLUGIN`; legacy `GPT_STORE` remains a persisted compatibility path. External availability/publication remains owner/workspace controlled. Automatic external publication remains out of scope.

## Next Work Rule

Phase 0 through Phase 5 are COMPLETE. Phase 6 pre-implementation audit is COMPLETE and Phase 6 is ACTIVATED. Runtime implementation may proceed only within the audited Phase 6 scope after the protected activation checkpoint merges.
