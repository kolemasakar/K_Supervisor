# PROJECT_STATE
Канонічний знімок поточного стану реалізації K_Supervisor.

Version: 1.5
Status: ACTIVE
Date: 2026-09-14

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Completed roadmap phases: 0-15
Current roadmap phase: 16 - Interfaces, Packaging, and Extensibility
Core Validation: PASS
Python: 3.13.15
pytest baseline: 81 passed
branch-aware coverage: 85.57%
coverage gate: >= 80%
compileall: PASS
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
- reference Research-Critic composition with mandatory profile approval and bounded autonomous review/revision;
- structured observability records, project/agent metrics, reliability validation, deterministic failure injection and permanent CI quality gates.

## Controlled-Autonomy Boundary

Production execution is expected to compose:

```text
Project / Workflow
  -> SupervisorKernel or ObservableSupervisorKernel wrapper
  -> PolicyEnforcedDispatcher
  -> Agent Runtime / concrete dispatcher
  -> Agent Contract result
```

Policy decisions are resolved before downstream execution. Material permission expansion requires explicit owner approval. Raw credentials are not part of normal project documentation, notifications, agent descriptors or normalized audit payloads.

## Observability and Reliability Boundary

Phase 15 adds append-only normalized records without replacing authoritative business state:

```text
AuditEvent
RoutingRecord
ReleaseValidationRecord
```

`MetricsCollector` derives project and per-agent metrics from durable records. `ReliabilityValidator` checks referential consistency across tasks, workflows, agent runs, routing, notification delivery and release validation. `AuditTimeline` is an ordered view of the canonical append-only audit stream.

Core Validation now enforces Python source compilation, the full pytest regression suite and branch-aware total coverage >= 80%. The validated Phase 15 implementation baseline reached 85.57% coverage.

## Documentation Consistency

`PROJECT_CONTRACT.md` remains aligned with immutable ProjectSpec persistence. `ROADMAP_IMPLEMENTATION_AUDIT.md` version 1.4 verifies Phase 0-15 against the published roadmap with no unmet published exit criteria.

## Known Baseline Limits

- SQLite remains the initial persistence backend, not a permanent storage architecture.
- In-process runtime cancellation is cooperative; runtime idempotency storage is process-local.
- A universal centralized Tool Gateway is not implemented; approval expiry/revocation is deferred.
- SMTP transport is best-effort and does not provide exactly-once remote delivery.
- `ProjectRecoverySnapshot` does not aggregate every intervention/notification/approval/policy/observability resource into one object.
- Reference agents are deterministic contract/integration examples rather than production-grade domain intelligence.
- Release readiness evidence is explicitly supplied; external publication and Git/package release automation are deferred.
- Phase 14 profile/final reference outputs live in durable WorkflowRun context rather than dedicated domain persistence/artifact records.
- The generic Task model has no `COMPLETED_WITH_LIMITATIONS`; exhausted reference iterations use `MAX_ITERATIONS_REACHED` and fail.
- Normalized routing records require `ObservableSupervisorKernel`; the stable base kernel remains unchanged. The current wrapper records selected routes, while a no-provider base path remains auditable through authoritative BLOCKED Task/Workflow state rather than a normalized RoutingRecord.
- Normalized audit appends are not one universal transaction with all authoritative state changes.
- Metrics are derived snapshots, not persisted time-series telemetry; distributed tracing/exporters are not implemented.
- Core Validation currently emits 14 `ResourceWarning` warnings from temporary SQLite connections in existing tests; warnings are visible and not suppressed.
- GitHub Actions still emits the Node 20 deprecation warning for checkout/setup-python actions while executing them with Node 24.

## Phase Gate

Phase 16 may proceed from this baseline. It is the final published roadmap phase and must not be marked complete until its exit criteria are validated by Core Validation and a dedicated completion checkpoint is committed.
