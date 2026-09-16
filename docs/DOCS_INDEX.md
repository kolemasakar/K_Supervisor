# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 3.2
Status: ACTIVE
Date: 2026-09-16

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `ROADMAP.md` - active ROADMAP v0.3 status and phase sequence.
4. `PROJECT_HANDOFF_2026_09_16_PHASE_7.md` - current transition handoff for Phase 7 preparation.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_6_COMPLETE.md` - Phase 6 completion evidence.
6. `PHASE6_PREIMPLEMENTATION_AUDIT.md` - Phase 6 production-observability audit.
7. `OBSERVABILITY_AND_RELIABILITY.md` - production observability/reliability boundary.
8. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_5_COMPLETE.md` - Phase 5 completion evidence.
9. `PHASE5_PREIMPLEMENTATION_AUDIT.md` - Phase 5 service-boundary audit.
10. `SERVICE_API.md` - versioned Service/API contracts.
11. `HARDENING_BASELINE_V0_3.md` - frozen predecessor baseline and debt assignment.
12. `PERSISTENCE.md` - storage, durable control/replay/telemetry state and recovery semantics.
13. `PROJECT_CONTROL_PLANE.md` - project control-plane boundaries.
14. `ARCHITECTURE.md` - control plane and multi-agent core.
15. `AGENT_RUNTIME.md` - runtime execution control and durable idempotency.
16. `INTEGRATIONS.md` - tools, providers, protected access and side-effect gateway.
17. `POLICY_AND_PERMISSIONS.md` - policy, approvals, permissions and audit.
18. `PLATFORM_INTERFACES.md` - package, CLI, config, Service/API and extension discovery.
19. `COMPATIBILITY_POLICY.md` - public compatibility rules.
20. `TEST_MATRIX.md` - permanent regression floor and active verification plan.
21. `CHAT_HANDOFF.md` - compact current continuation context.
22. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.

Historical startup handoffs remain preserved, including `PROJECT_HANDOFF_2026_09_16.md` and `PROJECT_HANDOFF_2026_09_16_PHASE_5.md`.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0-6: COMPLETE
v0.3 Phase 7-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Continuation State

Phase 6 is complete. `PROJECT_HANDOFF_2026_09_16_PHASE_7.md` is the current transition handoff. Phase 7 remains PLANNED / NOT STARTED until explicit activation.

## Current Runtime Baseline

```text
Core Validation run: 35110298258
Implementation SHA: 8f3d9a85abd68e1ab83dbf7ca87f3dadfe549883
Python workflow: 3.13
136 tests PASS
branch-aware coverage: 85.52%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples/service_api: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

## Completed v0.3 Runtime Checkpoints

```text
Phase 1 implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Phase 1 Core Validation:   34804141156
Phase 2 implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Phase 2 Core Validation:   34808287772
Phase 3 implementation SHA: 6868d595b66a6ada91a2e6f2f62866721d0f3560
Phase 3 Core Validation:   35086116020
Phase 4 implementation SHA: 34049f601fc8116aa12ee15023f1dc20bc25901a
Phase 4 Core Validation:   35092932820
Phase 5 implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Phase 5 Core Validation:   35103131762
Phase 6 implementation SHA: 8f3d9a85abd68e1ab83dbf7ca87f3dadfe549883
Phase 6 Core Validation:   35110298258
```

## Public Interface Baseline

```text
Python facade: ksupervisor
Service facade: ksupervisor.service
Service API: /api/v1
CLI: k-supervisor
Config version: 1
entry-point groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

## Historical Baseline

ROADMAP v0.2 remains immutable historical evidence. `HARDENING_BASELINE_V0_3.md` remains the frozen Phase 0 debt/compatibility contract; phase completion is recorded in separate checkpoints rather than rewriting that frozen record.
