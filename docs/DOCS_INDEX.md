# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 2.9
Status: ACTIVE
Date: 2026-09-16

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `ROADMAP.md` - active ROADMAP v0.3 status and phase sequence.
4. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_4_COMPLETE.md` - Phase 4 completion evidence.
5. `PHASE4_PREIMPLEMENTATION_AUDIT.md` - Phase 4 pre-implementation runtime-isolation audit.
6. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_3_COMPLETE.md` - Phase 3 completion evidence.
7. `PHASE3_PREIMPLEMENTATION_AUDIT.md` - Phase 3 pre-implementation side-effect-path audit.
8. `PROJECT_HANDOFF_2026_09_16.md` - frozen historical Phase 3 startup checkpoint.
9. `HARDENING_BASELINE_V0_3.md` - frozen predecessor baseline, debt assignment, migration and hardening rules.
10. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
11. `PERSISTENCE.md` - persistence, schema migration, durable control state and recovery boundary.
12. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md` - Phase 1 completion evidence.
13. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md` - Phase 2 completion evidence.
14. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
15. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
16. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, access boundaries and release.
17. `ARCHITECTURE.md` - control plane and multi-agent core.
18. `AGENT_CONTRACT.md` - common agent execution contract.
19. `CAPABILITY_MODEL.md` - capability discovery and routing.
20. `MACHINE_CONTRACTS.md` - machine-readable baseline.
21. `NOTIFICATIONS.md` - intervention and email notifications.
22. `REGISTRIES.md` - agent and capability registries.
23. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
24. `PROJECT_FACTORY.md` - repository bootstrap.
25. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
26. `AGENT_RUNTIME.md` - runtime execution control and durable idempotency.
27. `PROJECT_SCHEDULER.md` - parallel project execution.
28. `INTEGRATIONS.md` - tools, providers, protected access, provisioning and model-selection hooks.
29. `POLICY_AND_PERMISSIONS.md` - policy decisions, approval lifecycle, permissions and audit.
30. `AGENT_FACTORY.md` - agent blueprints, scaffolding and reference agents.
31. `RELEASE_MANAGER.md` - release state, readiness and publication handoff.
32. `REFERENCE_RESEARCH_CRITIC_WORKFLOW.md` - reference capability composition.
33. `OBSERVABILITY_AND_RELIABILITY.md` - structured audit, metrics and CI baseline.
34. `TEST_MATRIX.md` - permanent regression floor and active v0.3 verification plan.
35. `PLATFORM_INTERFACES.md` - public package, CLI, config and extension discovery.
36. `DEVELOPER_GUIDE.md` - extension authoring/registration patterns.
37. `COMPATIBILITY_POLICY.md` - public compatibility rules.
38. `NOTIFICATION_ADAPTER_INTERFACE.md` - future notification transport boundary.
39. `PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md` - v0.3 approval record.
40. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.
41. `ROADMAP_IMPLEMENTATION_AUDIT.md` - completed v0.2 audit with current v0.3 successor reference.
42. `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` - v0.2 closure record.
43. `CHAT_HANDOFF.md` - compact context for continuation.
44. `PROJECT_FILE_STANDARD.md` - repository file standard.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0: COMPLETE
v0.3 Phase 1: COMPLETE
v0.3 Phase 2: COMPLETE
v0.3 Phase 3: COMPLETE
v0.3 Phase 4: COMPLETE
v0.3 Phase 5-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Continuation State

Phase 4 is complete. `PROJECT_HANDOFF_2026_09_16.md` remains a frozen historical Phase 3 startup record. Phase 5 remains PLANNED / NOT STARTED.

## Current Runtime Baseline

```text
Core Validation run: 35092932820
Implementation SHA: 34049f601fc8116aa12ee15023f1dc20bc25901a
Python: 3.13.15
117 tests PASS
branch-aware coverage: 85.13%
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

Phase 3 implementation SHA: 6868d595b66a6ada91a2e6f2f62866721d0f3560
Phase 3 Core Validation:   35086116020

Phase 4 implementation SHA: 34049f601fc8116aa12ee15023f1dc20bc25901a
Phase 4 Core Validation:   35092932820
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
