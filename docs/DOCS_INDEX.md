# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 2.7
Status: ACTIVE
Date: 2026-09-14

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `ROADMAP.md` - active ROADMAP v0.3 status and phase sequence.
4. `PROJECT_HANDOFF_2026_09_16.md` - frozen continuation point and new-chat startup protocol for Phase 3.
5. `HARDENING_BASELINE_V0_3.md` - frozen predecessor baseline, debt assignment, migration and hardening rules.
6. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
7. `PERSISTENCE.md` - persistence, schema migration, durable control state and recovery boundary.
8. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md` - Phase 1 completion evidence.
9. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md` - Phase 2 completion evidence.
10. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
11. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
12. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, access boundaries and release.
13. `ARCHITECTURE.md` - control plane and multi-agent core.
14. `AGENT_CONTRACT.md` - common agent execution contract.
15. `CAPABILITY_MODEL.md` - capability discovery and routing.
16. `MACHINE_CONTRACTS.md` - machine-readable baseline.
17. `NOTIFICATIONS.md` - intervention and email notifications.
18. `REGISTRIES.md` - agent and capability registries.
19. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
20. `PROJECT_FACTORY.md` - repository bootstrap.
21. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
22. `AGENT_RUNTIME.md` - runtime execution control and durable idempotency.
23. `PROJECT_SCHEDULER.md` - parallel project execution.
24. `INTEGRATIONS.md` - tools, providers, protected access, provisioning and model-selection hooks.
25. `POLICY_AND_PERMISSIONS.md` - policy decisions, approval lifecycle, permissions and audit.
26. `AGENT_FACTORY.md` - agent blueprints, scaffolding and reference agents.
27. `RELEASE_MANAGER.md` - release state, readiness and publication handoff.
28. `REFERENCE_RESEARCH_CRITIC_WORKFLOW.md` - reference capability composition.
29. `OBSERVABILITY_AND_RELIABILITY.md` - structured audit, metrics and CI baseline.
30. `TEST_MATRIX.md` - permanent regression floor and active v0.3 verification plan.
31. `PLATFORM_INTERFACES.md` - public package, CLI, config and extension discovery.
32. `DEVELOPER_GUIDE.md` - extension authoring/registration patterns.
33. `COMPATIBILITY_POLICY.md` - public compatibility rules.
34. `NOTIFICATION_ADAPTER_INTERFACE.md` - future notification transport boundary.
35. `PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md` - v0.3 approval record.
36. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.
37. `ROADMAP_IMPLEMENTATION_AUDIT.md` - completed v0.2 audit with current v0.3 successor reference.
38. `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` - v0.2 closure record.
39. `CHAT_HANDOFF.md` - compact context for continuation.
40. `PROJECT_FILE_STANDARD.md` - repository file standard.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0: COMPLETE
v0.3 Phase 1: COMPLETE
v0.3 Phase 2: COMPLETE
Current approved phase: v0.3 Phase 3 - Centralized Side-Effect Enforcement
v0.3 Phase 3: ACTIVE
v0.3 Phase 3 runtime implementation at handoff: NOT STARTED
v0.3 Phase 4-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Handoff State

```text
Prepared: 2026-09-14
Planned continuation: 2026-09-16 09:00 Europe/Kyiv
Canonical startup file: PROJECT_HANDOFF_2026_09_16.md
```

The pause is owner-directed and does not change the approved roadmap phase.

## Current Runtime Baseline

```text
Core Validation run: 34808287772
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Python: 3.13.15
103 tests PASS
branch-aware coverage: 85.23%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

## Completed v0.3 Runtime Checkpoints

```text
Phase 1 implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Phase 1 Core Validation:   34804141156

Phase 2 implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Phase 2 Core Validation:   34808287772
```

## Public Extension Baseline

```text
Python facade: ksupervisor
CLI: k-supervisor
Config version: 1
entry-point groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

## Historical Baseline

ROADMAP v0.2 remains immutable historical evidence in `ROADMAP_V0_2_ARCHIVE.md` and its completion checkpoints. `HARDENING_BASELINE_V0_3.md` remains the frozen Phase 0 debt/compatibility contract; phase completion is recorded in separate checkpoints rather than rewriting that frozen record.