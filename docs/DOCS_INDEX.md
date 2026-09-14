# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 2.4
Status: ACTIVE
Date: 2026-09-14

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation/roadmap state.
3. `ROADMAP.md` - active ROADMAP v0.3 status and phase sequence.
4. `HARDENING_BASELINE_V0_3.md` - frozen predecessor baseline, debt assignment, migration and hardening rules.
5. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md` - Phase 0 completion evidence.
6. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
7. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
8. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, access boundaries and release.
9. `ARCHITECTURE.md` - control plane and multi-agent core.
10. `AGENT_CONTRACT.md` - common agent execution contract.
11. `CAPABILITY_MODEL.md` - capability discovery and routing.
12. `MACHINE_CONTRACTS.md` - machine-readable baseline.
13. `PERSISTENCE.md` - durable project state and recovery baseline.
14. `NOTIFICATIONS.md` - intervention and email notifications.
15. `REGISTRIES.md` - agent and capability registries.
16. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
17. `PROJECT_FACTORY.md` - repository bootstrap.
18. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
19. `AGENT_RUNTIME.md` - runtime execution control.
20. `PROJECT_SCHEDULER.md` - parallel project execution.
21. `INTEGRATIONS.md` - tools, providers, protected access, provisioning and model-selection hooks.
22. `POLICY_AND_PERMISSIONS.md` - policy decisions, permissions, approvals and audit.
23. `AGENT_FACTORY.md` - agent blueprints, scaffolding and reference agents.
24. `RELEASE_MANAGER.md` - release state, readiness and publication handoff.
25. `REFERENCE_RESEARCH_CRITIC_WORKFLOW.md` - reference capability composition.
26. `OBSERVABILITY_AND_RELIABILITY.md` - structured audit, metrics and CI baseline.
27. `TEST_MATRIX.md` - permanent regression floor and active v0.3 verification plan.
28. `PLATFORM_INTERFACES.md` - public package, CLI, config and extension discovery.
29. `DEVELOPER_GUIDE.md` - extension authoring/registration patterns.
30. `COMPATIBILITY_POLICY.md` - public compatibility rules.
31. `NOTIFICATION_ADAPTER_INTERFACE.md` - future notification transport boundary.
32. `PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md` - v0.3 approval record.
33. `ROADMAP_V0_2_ARCHIVE.md` - completed predecessor roadmap snapshot.
34. `ROADMAP_IMPLEMENTATION_AUDIT.md` - completed v0.2 audit and successor reference.
35. `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` - v0.2 closure record.
36. `CHAT_HANDOFF.md` - compact context for continuation.
37. `PROJECT_FILE_STANDARD.md` - repository file standard.

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0: COMPLETE
Current approved phase: v0.3 Phase 1
v0.3 Phase 1: ACTIVE
v0.3 Phase 2-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Runtime Baseline

Until Phase 1 produces a new validated implementation checkpoint:

```text
Core Validation run: 34793901147
Implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Python: 3.13.15
88 tests PASS
branch-aware coverage: 85.46%
coverage gate: >= 80% PASS
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

ROADMAP v0.2 remains immutable historical evidence in `ROADMAP_V0_2_ARCHIVE.md` and the v0.2 completion checkpoints. New implementation work proceeds only under the active v0.3 phase sequence.
