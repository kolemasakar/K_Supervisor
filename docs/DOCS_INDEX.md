# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 2.3
Status: ACTIVE

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation and roadmap snapshot.
3. `ROADMAP.md` - active ROADMAP v0.3.
4. `PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md` - approval/start checkpoint for v0.3.
5. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
6. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
7. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, secrets, release.
8. `ARCHITECTURE.md` - control plane and multi-agent core.
9. `AGENT_CONTRACT.md` - common agent execution contract.
10. `CAPABILITY_MODEL.md` - capability discovery and routing.
11. `MACHINE_CONTRACTS.md` - machine-readable baseline.
12. `PERSISTENCE.md` - durable project state, observability events and recovery.
13. `NOTIFICATIONS.md` - intervention and email notifications.
14. `REGISTRIES.md` - agent and capability registries.
15. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
16. `PROJECT_FACTORY.md` - repository bootstrap.
17. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
18. `AGENT_RUNTIME.md` - runtime execution control.
19. `PROJECT_SCHEDULER.md` - parallel project execution.
20. `INTEGRATIONS.md` - tools, providers, protected access, provisioning, model-selection hooks.
21. `POLICY_AND_PERMISSIONS.md` - policy decisions, risk, side effects, least privilege, approvals and audit.
22. `AGENT_FACTORY.md` - agent blueprints, scaffolding, registry/runtime binding and reference agents.
23. `RELEASE_MANAGER.md` - release state, readiness, GPT Store preparation and publication handoff.
24. `REFERENCE_RESEARCH_CRITIC_WORKFLOW.md` - reference behavior mapping and capability composition.
25. `OBSERVABILITY_AND_RELIABILITY.md` - structured audit, metrics, reliability and CI baseline.
26. `TEST_MATRIX.md` - v0.2 regression floor plus v0.3 verification plan.
27. `PLATFORM_INTERFACES.md` - public package, CLI, configuration, extension discovery and packaging.
28. `DEVELOPER_GUIDE.md` - extension authoring and registration patterns.
29. `COMPATIBILITY_POLICY.md` - contract/package/CLI/config compatibility rules.
30. `NOTIFICATION_ADAPTER_INTERFACE.md` - future transport adapter design boundary.
31. `ROADMAP_IMPLEMENTATION_AUDIT.md` - completed v0.2 Phase 0-16 compliance audit and successor reference.
32. `PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md` - predecessor roadmap closure checkpoint.
33. `ROADMAP_V0_2_ARCHIVE.md` - full archived v0.2 roadmap text.
34. `CHAT_HANDOFF.md` - compact current context for continuing in a new conversation.
35. `PROJECT_FILE_STANDARD.md` - repository file standard.

## Current Roadmap Status

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
Current approved phase: v0.3 Phase 0
v0.3 Phase 0: ACTIVE
v0.3 Phase 1-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

## Current Runtime Baseline

Runtime remains the validated v0.2 predecessor implementation until replaced by a later v0.3 implementation checkpoint.

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

## ROADMAP v0.3 Phase Sequence

```text
v0.3 Phase 0  Baseline Freeze & Hardening Contract
v0.3 Phase 1  Persistence & Resource Hygiene
v0.3 Phase 2  Durable Control State
v0.3 Phase 3  Centralized Side-Effect Enforcement
v0.3 Phase 4  Runtime Isolation & Cancellation
v0.3 Phase 5  Service/API Boundary
v0.3 Phase 6  Production Observability
v0.3 Phase 7  Extension Trust & Platform Governance
v0.3 Phase 8  Operational Readiness & Autonomous Lifecycle Qualification
```

## Closure / Approval Checkpoints

```text
PROJECT_CHECKPOINT_PHASE_13_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_14_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_15_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_16_COMPLETE.md
PROJECT_CHECKPOINT_ROADMAP_V0_2_COMPLETE.md
PROJECT_CHECKPOINT_ROADMAP_V0_3_APPROVED.md
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

## External References

```text
Production reference product:
kolemasakar/K_Research_Critic
Release baseline: v1.0.0
Reference commit: 815ddc35ea2c90304119fb3f7d5e8741848cc88b

Canonical shared file standard:
kolemasakar/AI_general
```

External references are not implementation dependencies unless an explicit architecture decision creates one.

ROADMAP v0.3 uses revision-local numbering. It does not create or imply a Phase 17.
