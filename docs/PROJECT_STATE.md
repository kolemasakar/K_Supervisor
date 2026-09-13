# PROJECT_STATE
Канонічний знімок поточного стану реалізації K_Supervisor.

Version: 1.4
Status: ACTIVE
Date: 2026-09-13

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Completed roadmap phases: 0-14
Current roadmap phase: 15 - Observability, Reliability, CI, and Test Matrix
Core Validation: PASS
Python: 3.13.15
pytest baseline: 75 passed
```

## Implemented Platform Layers

- Project lifecycle control plane and approved ProjectSpec contract;
- durable SQLite persistence and Project Registry;
- Human Intervention Broker and email Notification Broker;
- Agent and Capability Registries plus dynamic Supervisor routing;
- Project Factory, Workflow Engine, Agent Runtime and Project Scheduler;
- Tool/Provider/Provisioning boundaries and protected access references;
- policy, permissions, risk, approval and durable policy audit;
- AgentFactory, reusable agent scaffolding and deterministic reference agents;
- Release Manager, ReleaseTarget readiness, GPT Store preparation and owner publication handoff;
- reference Research-Critic composition with mandatory profile approval and bounded autonomous review/revision.

## Controlled-Autonomy Boundary

Production execution is expected to compose:

```text
Project / Workflow
  -> SupervisorKernel
  -> PolicyEnforcedDispatcher
  -> Agent Runtime / concrete dispatcher
  -> Agent Contract result
```

Policy decisions are resolved before downstream execution. Material permission expansion requires explicit owner approval. Raw credentials are not part of normal project documentation, notifications or agent descriptors.

## Reference Research-Critic Boundary

Phase 14 re-composes the essential K-Research & Critic v1.0.0 control behavior without importing its runtime:

```text
task-specific profile REVIEW_REQUIRED
  -> explicit owner approve/edit
  -> approved profile fingerprint
  -> research.reference
  -> factcheck.reference
  -> critique.reference
  -> REVISE loop or accepted PASS
  -> report.reference
  -> final report + review protocol
```

No AgentRun occurs before profile approval. The loop is bounded, and exhausted iterations cannot become false approval. Audit history contains structured run IDs, selected agent IDs, verdicts and reliability values rather than private chain-of-thought.

## Documentation Consistency

`PROJECT_CONTRACT.md` version 0.2 remains aligned with immutable ProjectSpec persistence. `ROADMAP_IMPLEMENTATION_AUDIT.md` version 1.3 verifies Phase 0-14 against the published roadmap with no unmet published exit criteria.

## Known Baseline Limits

- SQLite remains the initial persistence backend, not a permanent storage architecture.
- In-process runtime cancellation is cooperative; runtime idempotency storage is process-local.
- A universal centralized Tool Gateway is not yet implemented; approval expiry/revocation is also deferred.
- SMTP transport is best-effort and does not provide exactly-once remote delivery.
- `ProjectRecoverySnapshot` still does not aggregate every intervention/notification/approval/policy resource into one object.
- Reference agents are deterministic contract/integration examples rather than production-grade domain intelligence.
- Release readiness evidence is explicitly supplied; external publication and Git/package release automation are deferred.
- Phase 14 stores its task-specific profile and final reference outputs in durable WorkflowRun context rather than dedicated domain persistence/artifact records.
- Phase 14 does not implement the legacy DomainResolver/ProfileManager subsystem or material profile-amendment flow.
- The generic Task model has no `COMPLETED_WITH_LIMITATIONS`; exhausted reference iterations therefore record `MAX_ITERATIONS_REACHED` and fail rather than approximating the legacy state.

## Phase Gate

Phase 15 may proceed from this baseline. Phase 16 must not be marked active until Phase 15 exit criteria are validated by Core Validation and a completion checkpoint is committed.
