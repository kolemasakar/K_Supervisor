# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 1.5
Status: ACTIVE

## Reading Order

1. `VISION.md` - product direction and scope.
2. `PROJECT_CONTRACT.md` - ProjectSpec and approval contract.
3. `PROJECT_LIFECYCLE.md` - lifecycle and operational states.
4. `PROJECT_CONTROL_PLANE.md` - factory, registry, scheduler, intervention, notifications, secrets, release.
5. `ARCHITECTURE.md` - control plane and multi-agent core.
6. `AGENT_CONTRACT.md` - common agent execution contract.
7. `CAPABILITY_MODEL.md` - capability discovery and routing.
8. `MACHINE_CONTRACTS.md` - machine-readable baseline.
9. `PERSISTENCE.md` - durable project state and recovery.
10. `NOTIFICATIONS.md` - intervention and email notifications.
11. `REGISTRIES.md` - agent and capability registries.
12. `SUPERVISOR_KERNEL.md` - task orchestration and routing.
13. `PROJECT_FACTORY.md` - repository bootstrap.
14. `WORKFLOW_ENGINE.md` - multi-agent workflow composition.
15. `AGENT_RUNTIME.md` - runtime execution control.
16. `PROJECT_SCHEDULER.md` - parallel project execution.
17. `INTEGRATIONS.md` - tools, providers, protected access, provisioning, and model-selection hooks.
18. `POLICY_AND_PERMISSIONS.md` - Phase 11 policy decisions, risk, side effects, least privilege, approvals, and audit.
19. `ROADMAP.md` - phased implementation plan.
20. `PROJECT_FILE_STANDARD.md` - repository file standard.

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
Next: Phase 12 - Reference Agents and Agent Factory
```

Current automated validation:

```text
Python 3.13.15
63 tests PASS
```

Latest checkpoints:

```text
PROJECT_CHECKPOINT_PHASE_8_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_9_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_10_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_11_COMPLETE.md
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
