# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 0.8
Status: ACTIVE

## Reading Order

1. `VISION.md` - product direction, automation goal, scope, and non-goals.
2. `PROJECT_CONTRACT.md` - ProjectSpec and onboarding approval contract.
3. `PROJECT_LIFECYCLE.md` - project lifecycle, operational states, and release boundary.
4. `PROJECT_CONTROL_PLANE.md` - Project Factory, Registry, Scheduler, intervention, notifications, access protection, and release management.
5. `ARCHITECTURE.md` - Control Plane and Multi-Agent Core architecture.
6. `AGENT_CONTRACT.md` - common agent execution contract.
7. `CAPABILITY_MODEL.md` - capability discovery, compatibility, and routing model.
8. `MACHINE_CONTRACTS.md` - Phase 1 machine-readable contract baseline.
9. `PERSISTENCE.md` - Phase 2 persistence, Project Registry, isolation, and recovery semantics.
10. `NOTIFICATIONS.md` - Phase 3 Human Intervention and email-first notification architecture.
11. `REGISTRIES.md` - Phase 4 Agent Registry, Capability Registry, availability, versioning, and provider discovery.
12. `ROADMAP.md` - phased implementation plan starting from Phase 0.
13. `PROJECT_FILE_STANDARD.md` - repository file and documentation standard.

## Current Concept Baseline

```text
K_Supervisor
= AI Project Lifecycle Supervisor
+ Modular Multi-Agent Platform
```

Initial owner notification transport:

```text
EMAIL
```

Additional messaging transports are deferred extension points.

## Current Implementation Status

```text
Phase 0: COMPLETE
Phase 1: COMPLETE
Phase 2: COMPLETE
Phase 3: COMPLETE
Phase 4: COMPLETE
Next: Phase 5 - Supervisor Orchestration Kernel
```

Current automated validation:

```text
Python 3.13.15
25 tests PASS
```

Checkpoints:

```text
PROJECT_CHECKPOINT_PHASE_1_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_2_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_3_IMPLEMENTATION_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_3_COMPLETE.md
PROJECT_CHECKPOINT_PHASE_4_COMPLETE.md
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
