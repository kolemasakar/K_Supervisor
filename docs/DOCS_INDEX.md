# DOCS_INDEX
Індекс основних документів K_Supervisor та рекомендований порядок їх читання.

Version: 0.2
Status: ACTIVE

## Reading Order

1. `VISION.md` - product direction, automation goal, scope, and non-goals.
2. `PROJECT_CONTRACT.md` - ProjectSpec and onboarding approval contract.
3. `PROJECT_LIFECYCLE.md` - project lifecycle, operational states, and release boundary.
4. `PROJECT_CONTROL_PLANE.md` - Project Factory, Registry, Scheduler, intervention, notifications, access protection, and release management.
5. `ARCHITECTURE.md` - Control Plane and Multi-Agent Core architecture.
6. `AGENT_CONTRACT.md` - common agent execution contract.
7. `CAPABILITY_MODEL.md` - capability discovery, compatibility, and routing model.
8. `ROADMAP.md` - phased implementation plan starting from Phase 0.
9. `PROJECT_FILE_STANDARD.md` - repository file and documentation standard.

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

## External References

```text
Production reference product:
kolemasakar/K_Research_Critic
Release baseline: v1.0.0

Canonical shared file standard:
kolemasakar/AI_general
```

External references are not implementation dependencies unless a later architecture decision explicitly creates one.
