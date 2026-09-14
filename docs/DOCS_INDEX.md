# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 2.0
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
10. `PERSISTENCE.md` - durable project state, observability events and recovery.
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
22. `REFERENCE_RESEARCH_CRITIC_WORKFLOW.md` - Phase 14 reference behavior mapping and capability composition.
23. `OBSERVABILITY_AND_RELIABILITY.md` - structured audit, metrics, reliability and CI quality baseline.
24. `TEST_MATRIX.md` - regression coverage by roadmap phase and reliability category.
25. `ROADMAP.md` - phased implementation plan.
26. `ROADMAP_IMPLEMENTATION_AUDIT.md` - implementation-to-roadmap compliance audit.
27. `PROJECT_FILE_STANDARD.md` - repository file standard.

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
Phase 14: COMPLETE
Phase 15: COMPLETE
Next: Phase 16 - Interfaces, Packaging, and Extensibility
```

Current automated validation:

```text
Python 3.13.15
81 tests PASS
branch-aware coverage: 85.57%
coverage gate: >= 80%
compileall: PASS
```

Latest checkpoints:

```text
PROJECT_CHECKPOINT_PHASE_12_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_13_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_14_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_15_COMPLETE.md
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

External references are not implementation dependencies unless an explicit architecture decision creates one. Phase 14 studies K-Research & Critic behavior as a reference but does not import or depend on its runtime.
