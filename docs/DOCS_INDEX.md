# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 3.4
Status: ACTIVE
Date: 2026-09-16

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `ROADMAP.md` - active ROADMAP v0.3 status and phase sequence.
4. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_7_COMPLETE.md` - Phase 7 completion evidence.
5. `TEST_MATRIX.md` - permanent regression floor and current validation evidence.
6. `PHASE7_PREIMPLEMENTATION_AUDIT.md` - Phase 7 audit and trust/governance design.
7. `PROJECT_HANDOFF_2026_09_16_PHASE_7.md` - preserved Phase 7 start handoff.
8. `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md` - current ChatGPT Plugin release-target compatibility decision.
9. `RELEASE_MANAGER.md` - release targets and owner/workspace availability boundary.
10. `PLATFORM_INTERFACES.md` - package, CLI, Service/API and extension discovery.
11. `COMPATIBILITY_POLICY.md` - public compatibility rules.
12. `HARDENING_BASELINE_V0_3.md` - frozen predecessor baseline and debt assignment.
13. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
14. `ARCHITECTURE.md` - control plane and multi-agent core.
15. `PERSISTENCE.md` - storage and recovery semantics.
16. `AGENT_RUNTIME.md` - runtime execution control.
17. `INTEGRATIONS.md` - tools, providers and side-effect gateway.
18. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
19. `OBSERVABILITY_AND_RELIABILITY.md` - observability/reliability boundary.
20. `SERVICE_API.md` - versioned Service/API contracts.
21. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.

Historical phase checkpoints and startup handoffs remain preserved and are not rewritten to reflect later platform changes.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0-6: COMPLETE
v0.3 Phase 7: COMPLETE
v0.3 Phase 8: PLANNED / NOT ACTIVATED
Phase 17: NOT DEFINED
```

## Current Runtime Baseline

```text
Implementation SHA: 97f454a11d1b5e5afb1334fb06d54d5abffdf004
Core Validation run: 35124348659
Python: 3.13.15
149 tests PASS
branch-aware coverage: 85.63%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

## Phase 7 Runtime Evidence

```text
Phase 7 implementation SHA: 64c84ad6e6633c047416aca270d979e4ba5d36a0
Phase 7 Core Validation:   35121930140
Status: COMPLETE — runtime/CI and repository governance validated
```

## Phase 7 Governance Evidence

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

## Current ChatGPT Compatibility Boundary

```text
Preferred target: CHATGPT_PLUGIN
Legacy target: GPT_STORE
Custom Action auto-migration: NO
Selected-model coupling: NO
External availability: owner/workspace controlled
```

See `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md`.

## Historical Baseline

ROADMAP v0.2 remains immutable historical evidence. `HARDENING_BASELINE_V0_3.md` remains the frozen Phase 0 debt/compatibility contract; later runtime and compatibility changes are recorded in active state/roadmap documents rather than rewriting the frozen baseline.
