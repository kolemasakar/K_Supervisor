# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 1.8
Status: ACTIVE

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_STATE.md` - canonical current implementation snapshot and known limits.
3. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
4. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
5. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, secrets, release.
6. `ARCHITECTURE.md` - control plane and multi-agent core.
7. `AGENT_CONTRACT.md` - common agent execution contract.
8. `CAPABILITY_MODEL.md` - capability discovery and routing.
9. `MACHINE_CONTRACTS.md` - machine-readable baseline.
10. `PERSISTENCE.md` - durable project state and recovery.
11. `NOTIFICATIONS.md` - intervention and email notifications.
12. `REGISTRIES.md` - agent and capability registries.
13. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
14. `PROJECT_FACTORY.md` - repository bootstrap.
15. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
16. `AGENT_RUNTIME.md` - runtime execution control.
17. `PROJECT_SCHEDULER.md` - parallel project execution.
18. `INTEGRATIONS.md` - tools, providers, protected access, provisioning, and model-selection hooks.
19. `POLICY_AND_PERMISSIONS.md` - policy decisions, risk, side effects, least privilege, approvals, and audit.
20. `AGENT_FACTORY.md` - agent blueprints, scaffolding, registry/runtime binding, and reference agents.
21. `RELEASE_MANAGER.md` - release state, readiness, GPT Store preparation, and publication handoff.
22. `ROADMAP.md` - phased implementation plan.
23. `ROADMAP_IMPLEMENTATION_AUDIT.md` - implementation-to-roadmap compliance audit.
24. `PROJECT_FILE_STANDARD.md` - repository file standard.

## Current Implementation Status

```text
Phase 0: COMPLETE
Phase 1: COMPLETE
Phase 2: COMPLETE
Phase 3: COMPLETE
Phase 4: COMPLETE
Phase 5: COMPLETE
Phase 6: COMPLETE
Phase 7: COMPLETE
Phase 8: COMPLETE
Phase 9: COMPLETE
Phase 10: COMPLETE
Phase 11: COMPLETE
Phase 12: COMPLETE
Phase 13: COMPLETE
Next: Phase 14 - Reference Research-Critic Workflow
```

Current automated validation:

```text
Python 3.13.15
70 tests PASS
```

Latest checkpoints:

```text
PROJECT_CHECKPOINT_PHASE_10_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_11_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_12_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_13_COMPLETE.md
```

## External References

```text
Production reference product:
kolemasakar/K_Research_Critic
Release baseline: v1.0.0

Canonical shared file standard:
kolemasakar/AI_general
```

External references are not implementation dependencies unless a later architecture decision explicitly creates one.
