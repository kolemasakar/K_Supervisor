# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 2.5
Status: ACTIVE
Date: 2026-09-14

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `ROADMAP.md` - active ROADMAP v0.3 status and phase sequence.
4. `HARDENING_BASELINE_V0_3.md` - frozen predecessor baseline, debt assignment, migration and hardening rules.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
6. `PERSISTENCE.md` - current persistence boundary, schema migration and Phase 1 hardening baseline.
7. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_1_COMPLETE.md` - Phase 1 completion evidence.
8. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
9. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
10. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, access boundaries and release.
11. `ARCHITECTURE.md` - control plane and multi-agent core.
12. `AGENT_CONTRACT.md` - common agent execution contract.
13. `CAPABILITY_MODEL.md` - capability discovery and routing.
14. `MACHINE_CONTRACTS.md` - machine-readable baseline.
15. `NOTIFICATIONS.md` - intervention and email notifications.
16. `REGISTRIES.md` - agent and capability registries.
17. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
18. `PROJECT_FACTORY.md` - repository bootstrap.
19. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
20. `AGENT_RUNTIME.md` - runtime execution control.
21. `PROJECT_SCHEDULER.md` - parallel project execution.
22. `INTEGRATIONS.md` - tools, providers, protected access, provisioning and model-selection hooks.
23. `POLICY_AND_PERMISSIONS.md` - policy decisions, permissions, approvals and audit.
24. `AGENT_FACTORY.md` - agent blueprints, scaffolding and reference agents.
25. `RELEASE_MANAGER.md` - release state, readiness and publication handoff.
26. `REFERENCE_RESEARCH_CRITIC_WORKFLOW.md` - reference capability composition.
27. `OBSERVABILITY_AND_RELIABILITY.md` - structured audit, metrics and CI baseline.
28. `TEST_MATRIX.md` - permanent regression floor and active v0.3 verification plan.
29. `PLATFORM_INTERFACES.md` - public package, CLI, config and extension discovery.
30. `DEVELOPER_GUIDE.md` - extension authoring/registration patterns.
31. `COMPATIBILITY_POLICY.md` - public compatibility rules.
32. `NOTIFICATION_ADAPTER_INTERFACE.md` - future notification transport boundary.
33. `PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md` - v0.3 approval record.
34. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.
35. `ROADMAP_IMPLEMENTATION_AUDIT.md` - completed v0.2 audit with current v0.3 successor reference.
36. `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` - v0.2 closure record.
37. `CHAT_HANDOFF.md` - compact context for continuation.
38. `PROJECT_FILE_STANDARD.md` - repository file standard.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0: COMPLETE
v0.3 Phase 1: COMPLETE
Current approved phase: v0.3 Phase 2 - Durable Control State
v0.3 Phase 2: ACTIVE
v0.3 Phase 3-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Runtime Baseline

```text
Core Validation run: 34804141156
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Python: 3.13.15
95 tests PASS
branch-aware coverage: 85.66%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
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
