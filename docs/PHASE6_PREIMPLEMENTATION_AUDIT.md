# PHASE6_PREIMPLEMENTATION_AUDIT
Pre-implementation audit for ROADMAP v0.3 Phase 6 - Production Observability.

Version: 1.0
Status: COMPLETE
Date: 2026-09-16
Roadmap: v0.3
Phase: 6

## Start Gate

- current `main`: `e5dd569d14b41047a344e9c52736534040acb9a9`;
- validated Phase 5 runtime SHA: `0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841`;
- commits after the validated runtime SHA are documentation-only;
- Phase 5 Core Validation run `35103131762` passed the cumulative 129-test baseline at 85.34% branch-aware coverage;
- Phase 6 is explicitly activated by the user's continuation instruction.

## Existing Observability Surface

The predecessor platform already provides:

- durable `AuditEvent`, `RoutingRecord` and `ReleaseValidationRecord` streams;
- derived `MetricsCollector` snapshots over authoritative persistence;
- ordered `AuditTimeline` views;
- `ReliabilityValidator` cross-record integrity checks;
- runtime `AgentRunRequest` / `AgentRunResult` correlation identifiers;
- Service/API project/operation/idempotency correlation at the mutation layer;
- Phase 3 side-effect correlation and durable attempt/outcome state;
- process-local `RuntimeHealthTracker` for agent availability.

## Gaps Assigned to Phase 6

The approved scope is not yet satisfied because the platform lacks:

- a generic persisted operational telemetry record suitable for service/runtime events;
- one telemetry timeline spanning those persisted records;
- a standard correlation envelope that can carry project/request/task/workflow/run/agent/capability/service-operation identifiers;
- an explicit recursive redaction boundary before telemetry persistence/export;
- exporter contracts for Prometheus/OpenTelemetry-compatible integrations without coupling core code to a concrete SDK;
- service-level liveness/readiness contracts distinct from Project lifecycle/operational state;
- durable telemetry reconstruction through `ProjectRecoverySnapshot`.

## Boundary Decisions

Phase 6 will:

- add append-only `TelemetryRecord` events to the existing persistence abstraction and SQLite generic event layout;
- keep SQLite physical schema version `2`;
- add a reusable `TelemetryRecorder` that redacts attributes before persistence;
- add optional telemetry hooks to `AgentRuntimeDispatcher` and `ServiceApiV1` without changing existing caller contracts;
- add a deterministic `TelemetryTimeline` over persisted telemetry records;
- add exporter protocols and SDK-neutral Prometheus/OpenTelemetry-style projection adapters;
- add service `HealthReport` / `ReadinessReport` evaluation based on explicit component probes;
- include telemetry records in `ProjectRecoverySnapshot`;
- preserve existing audit records as audit, not duplicate them into a second authoritative business-state stream.

Phase 6 will not:

- add external OpenTelemetry/Prometheus packages or remote collectors;
- add production hosting, TLS, deployment orchestration or backup/restore qualification;
- redesign `/api/v1` authorization, lifecycle transitions or idempotency;
- alter extension trust/signature governance;
- add distributed tracing infrastructure, consensus or a remote telemetry database;
- change Project lifecycle/operational states to represent service health.

## Correlation Contract

The persisted telemetry envelope will support optional identifiers:

```text
project_id
request_id
task_id
workflow_run_id
run_id
agent_id
capability_id
service_operation
correlation_id
```

Callers provide only identifiers already available at their execution boundary. Missing identifiers remain `None`; no synthetic business identifiers are invented.

## Redaction Contract

Telemetry persistence/export must redact recursively before data leaves the instrumentation call. Keys representing secrets, tokens, credentials, authorization, cookies and protected references are replaced with a stable redaction marker. Values beginning with `secret://` are also redacted. Redaction must not mutate caller-owned input objects.

## Health / Readiness Contract

Service health is distinct from project state:

- liveness answers whether the process/service health evaluator is operating;
- readiness answers whether explicitly configured required component probes are ready;
- optional component degradation is reported but does not automatically make readiness false;
- Project lifecycle/operational state is not used as a service readiness signal.

## Exporter Contract

Core code exposes exporter-neutral snapshots/projections. Prometheus/OpenTelemetry adapters produce deterministic data structures suitable for concrete integrations, but network transport and third-party SDK lifecycle remain outside Phase 6.

## Required Verification

Phase 6 tests must prove:

- correlation survives runtime/service instrumentation;
- telemetry is persisted and survives reopen/restart;
- telemetry timeline order is deterministic;
- redaction happens before persistence and export;
- exporter contracts project supported counters/events without exposing protected values;
- health/readiness semantics remain independent of Project lifecycle state;
- recovery includes telemetry records;
- all completed v0.2 + v0.3 Phase 0-5 tests remain green.

## Audit Result

Pre-implementation audit: PASS.

No blocker requires Phase 7 or Phase 8 work. Implementation may proceed within the Phase 6 scope above.
