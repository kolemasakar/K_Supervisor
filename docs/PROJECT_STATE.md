# PROJECT_STATE
Канонічний знімок поточного стану реалізації K_Supervisor.

Version: 1.3
Status: ACTIVE
Date: 2026-09-13

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Completed roadmap phases: 0-13
Current roadmap phase: 14 - Reference Research-Critic Workflow
Core Validation: PASS
Python: 3.13.15
pytest baseline: 70 passed
```

## Implemented Platform Layers

- Project lifecycle control plane and ProjectSpec approval contract;
- durable SQLite persistence and Project Registry;
- Human Intervention Broker and email Notification Broker;
- Agent and Capability Registries;
- Supervisor orchestration kernel and dynamic capability routing;
- Project Factory and repository bootstrap;
- Workflow Engine with multi-agent composition and approval gates;
- Agent Runtime with execution control, timeout/cancellation and idempotency hooks;
- Project Scheduler with parallel-project isolation and shared limits;
- Tool/Provider/Provisioning interfaces and protected access references;
- Policy, permissions, risk, approval and durable policy audit;
- AgentFactory, reusable agent scaffolding and deterministic reference agent catalog;
- Release Manager, durable ReleaseTarget state, generic readiness checks, GPT Store preparation and owner publication handoff.

## Controlled-Autonomy Boundary

Production execution is expected to compose:

```text
Project / Workflow
  -> SupervisorKernel
  -> PolicyEnforcedDispatcher
  -> Agent Runtime / concrete dispatcher
  -> Agent Contract result
```

Policy decisions are resolved before downstream execution. Material permission expansion requires an explicit owner approval record. Raw credentials are not part of normal project documentation, notifications or agent descriptors.

## Agent Creation Boundary

Phase 12 adds a declarative creation path without changing Supervisor core:

```text
AgentBlueprint
  -> AgentFactory
  -> CapabilityRegistry + AgentRegistry
  -> runtime binding
  -> normal Supervisor/Runtime execution
```

`AgentScaffolder` generates a minimum `agent.py`, `test_agent.py`, and README starting point with syntax validation, idempotent writes and conflict protection.

## Release Boundary

Phase 13 adds controlled release preparation without taking ownership of publication:

```text
FIRST_WORKING
  -> RELEASE_PREPARATION
  -> readiness checks
  -> target-specific assets
  -> RELEASE_READY
  -> PUBLICATION_REQUIRED
  -> owner publication
  -> explicit publication confirmation
  -> PUBLISHED
```

`ReleaseTarget` is durable and included in `ProjectRecoverySnapshot`. The GPT Store profile automatically prepares machine-readable configuration, instructions, listing text and publication checklist. External publication itself remains an explicit owner action.

## Documentation Consistency

`PROJECT_CONTRACT.md` version 0.2 is aligned with the immutable ProjectSpec persistence model: a newly approved specification links the prior immutable record through `supersedes_spec_id`, while `Project.active_project_spec_id` identifies the authoritative specification. Existing approved historical records are not rewritten merely to mark them superseded.

`ROADMAP_IMPLEMENTATION_AUDIT.md` version 1.2 verifies Phase 0-13 against the published roadmap with no unmet published exit criteria.

## Known Baseline Limits

- SQLite remains the initial persistence backend, not a permanent storage architecture.
- In-process runtime cancellation is cooperative; hard process isolation is not implemented.
- Runtime idempotency storage is process-local and does not survive restart.
- Per-agent tool permission enforcement exists, but a universal centralized Tool Gateway is not yet implemented.
- Approval expiry and revocation are not implemented.
- SMTP transport does not provide exactly-once delivery guarantees.
- `ProjectRecoverySnapshot` includes releases and release targets but still does not aggregate HumanActionRequest, notification/delivery, approval, or policy-decision records into the same snapshot; those records remain durable through their persistence APIs.
- Reference agents are deterministic contract/integration examples rather than production-grade domain intelligence.
- Agent scaffolding does not infer domain-specific tools, prompts, schemas, evaluations or permissions.
- Release readiness evidence is explicitly supplied; CI-provider evidence ingestion is not automatic.
- Release preparation does not publish externally, create Git tags/releases, or package artifacts automatically.
- Multi-target release preparation is not one atomic transaction across repository and persistence operations.

## Phase Gate

Phase 14 may proceed from this baseline. Phase 15 must not be marked active until Phase 14 exit criteria are validated by Core Validation and a completion checkpoint is committed.
