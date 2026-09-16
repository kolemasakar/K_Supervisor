# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 3.7
Status: ACTIVE
Date: 2026-09-16

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `PROJECT_CHECKPOINT_ROADMAP_V0_3_COMPLETE.md` - ROADMAP v0.3 final closure evidence.
4. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_8_COMPLETE.md` - Phase 8 completion evidence.
5. `ROADMAP.md` - completed ROADMAP v0.3 phase sequence and evidence.
6. `TEST_MATRIX.md` - permanent regression floor and final v0.3 validation evidence.
7. `OPERATIONS_RUNBOOK.md` - deployment, backup/restore/upgrade, recovery and package-publication procedures.
8. `PHASE8_PREIMPLEMENTATION_AUDIT.md` - Phase 8 implementation boundary.
9. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_7_COMPLETE.md` - Phase 7 completion evidence.
10. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - ChatGPT Plugin release-target compatibility decision.
11. `RELEASE_MANAGER.md` - release targets and owner/workspace availability boundary.
12. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
13. `COMPATIBILITY_POLICY.md` - public compatibility rules.
14. `HARDENING_BASELINE_V0_3.md` - frozen v0.3 predecessor baseline and debt assignment.
15. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
16. `ARCHITECTURE.md` - control plane and multi-agent core.
17. `PERSISTENCE.md` - storage and operational recovery semantics.
18. `AGENT_RUNTIME.md` - runtime execution control.
19. `INTEGRATIONS.md` - tools, providers and side-effect gateway.
20. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
21. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability and deployment qualification.
22. `SERVICE_API.md` - versioned Service/API contracts.
23. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.

Historical phase checkpoints and startup handoffs remain preserved and are not rewritten to reflect later platform changes.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
v0.3 Phase 0-8: COMPLETE
Current approved implementation phase: NONE
Phase 9: NOT DEFINED
Phase 17: NOT DEFINED
```

## Current Runtime Baseline

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

Exact-tree local cumulative verification before merge: `163 passed`, branch-aware coverage `85.82%` on Python 3.12.3. GitHub Actions Python 3.13 is authoritative and passed on PR and merged `main`.

## Repository Governance

```text
Ruleset: main-core-validation
Ruleset id: 23556478
Target: default branch
Enforcement: active
Pull request required: YES
Required status check: Core Validation
Deletion blocked: YES
Non-fast-forward / force push blocked: YES
Bypass actors: NONE
```

## Current Compatibility / Publication Boundary

```text
Preferred ChatGPT target: CHATGPT_PLUGIN
Legacy ChatGPT target: GPT_STORE
Package-index workflow: manual owner-confirmed only
External availability/publication: owner/workspace controlled
Automatic external publication: NO
```

ROADMAP completion is not a claim that the package was actually published or that explicitly deferred post-v0.3 scope is implemented. A future implementation cycle requires a new explicitly approved roadmap/revision.

## Historical Baseline

ROADMAP v0.2 remains immutable historical evidence. `HARDENING_BASELINE_V0_3.md` remains the frozen Phase 0 debt/compatibility contract; later validated implementation and closure evidence is recorded in the v0.3 checkpoints and active state documents.
