# PROJECT_STATE
Канонічний знімок поточного стану реалізації K_Supervisor.

Version: 1.1
Status: ACTIVE
Date: 2026-09-13

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Completed roadmap phases: 0-11
Current roadmap phase: 12 - Reference Agents and Agent Factory
Core Validation: PASS
Python: 3.13.15
pytest baseline: 63 passed
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
- Policy, permissions, risk, approval and durable policy audit.

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

## Documentation Consistency

`PROJECT_CONTRACT.md` version 0.2 is aligned with the immutable ProjectSpec persistence model: a newly approved specification links the prior immutable record through `supersedes_spec_id`, while `Project.active_project_spec_id` identifies the authoritative specification. Existing approved historical records are not rewritten merely to mark them superseded.

## Known Baseline Limits

- SQLite remains the initial persistence backend, not a permanent storage architecture.
- In-process runtime cancellation is cooperative; hard process isolation is not implemented.
- Runtime idempotency storage is process-local and does not survive restart.
- Per-agent tool permission enforcement exists, but a universal centralized Tool Gateway is not yet implemented.
- Approval expiry and revocation are not implemented.
- SMTP transport does not provide exactly-once delivery guarantees.
- `ProjectRecoverySnapshot` does not yet aggregate all Phase 3+ intervention/notification/policy resources into one recovery object; records remain individually durable through persistence APIs.

## Phase Gate

Phase 12 may proceed from this baseline. Phase 13 must not be marked active until Phase 12 exit criteria are validated by Core Validation and a completion checkpoint is committed.
