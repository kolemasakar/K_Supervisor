# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 3.1
Status: ACTIVE
Date: 2026-09-16

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `ROADMAP.md` - active ROADMAP v0.3 status and phase sequence.
4. `PROJECT_HANDOFF_2026_09_16_PHASE_6.md` - current new-chat transition handoff for Phase 6 preparation.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_5_COMPLETE.md` - Phase 5 completion evidence.
6. `PHASE5_PREIMPLEMENTATION_AUDIT.md` - Phase 5 service-boundary audit.
7. `SERVICE_API.md` - versioned Service/API contracts, auth/scopes, idempotency and error semantics.
8. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_4_COMPLETE.md` - Phase 4 completion evidence.
9. `PHASE4_PREIMPLEMENTATION_AUDIT.md` - Phase 4 runtime-isolation audit.
10. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_3_COMPLETE.md` - Phase 3 completion evidence.
11. `PHASE3_PREIMPLEMENTATION_AUDIT.md` - Phase 3 side-effect-path audit.
12. `HARDENING_BASELINE_V0_3.md` - frozen predecessor baseline and debt assignment.
13. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
14. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md` - Phase 1 completion evidence.
15. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md` - Phase 2 completion evidence.
16. `PERSISTENCE.md` - storage, durable control/replay state and recovery semantics.
17. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
18. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
19. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, release and Service/API boundary.
20. `ARCHITECTURE.md` - control plane and multi-agent core.
21. `AGENT_CONTRACT.md` - common agent execution contract.
22. `CAPABILITY_MODEL.md` - capability discovery and routing.
23. `MACHINE_CONTRACTS.md` - machine-readable baseline.
24. `NOTIFICATIONS.md` - intervention and email notifications.
25. `REGISTRIES.md` - agent and capability registries.
26. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
27. `PROJECT_FACTORY.md` - repository bootstrap.
28. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
29. `AGENT_RUNTIME.md` - runtime execution control and durable idempotency.
30. `PROJECT_SCHEDULER.md` - parallel project execution.
31. `INTEGRATIONS.md` - tools, providers, protected access and side-effect gateway.
32. `POLICY_AND_PERMISSIONS.md` - policy decisions, approval lifecycle, permissions and audit.
33. `AGENT_FACTORY.md` - agent blueprints, scaffolding and reference agents.
34. `RELEASE_MANAGER.md` - release state, readiness and publication handoff.
35. `REFERENCE_RESEARCH_CRITIC_WORKFLOW.md` - reference capability composition.
36. `OBSERVABILITY_AND_RELIABILITY.md` - current observability/reliability baseline and Phase 6 predecessor surface.
37. `TEST_MATRIX.md` - permanent regression floor and active v0.3 verification plan.
38. `PLATFORM_INTERFACES.md` - package, CLI, config, Service/API and extension discovery.
39. `DEVELOPER_GUIDE.md` - extension authoring/registration patterns.
40. `COMPATIBILITY_POLICY.md` - public package/API/CLI/config compatibility rules.
41. `NOTIFICATION_ADAPTER_INTERFACE.md` - future notification transport boundary.
42. `PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md` - v0.3 approval record.
43. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.
44. `ROADMAP_IMPLEMENTATION_AUDIT.md` - completed v0.2 audit with current successor reference.
45. `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` - v0.2 closure record.
46. `CHAT_HANDOFF.md` - compact current continuation context.
47. `PROJECT_FILE_STANDARD.md` - repository file standard.

Historical startup handoffs remain preserved, including `PROJECT_HANDOFF_2026_09_16.md` and `PROJECT_HANDOFF_2026_09_16_PHASE_5.md`.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0-5: COMPLETE
v0.3 Phase 6-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Continuation State

Phase 5 is complete. `PROJECT_HANDOFF_2026_09_16_PHASE_6.md` is the current transition handoff. Phase 6 remains PLANNED / NOT STARTED until explicit activation.

## Current Runtime Baseline

```text
Core Validation run: 35103131762
Implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Python workflow: 3.13
129 tests PASS
branch-aware coverage: 85.34%
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
