# OBSERVABILITY_AND_RELIABILITY
Production observability and reliability boundary for K_Supervisor.

Version: 2.0
Status: ACTIVE
Baseline: v0.3 Phase 6 COMPLETE
Date: 2026-09-16

## Observability Model

The platform preserves structured audit/routing/release-validation records and now adds append-only operational `TelemetryRecord` events. Audit remains authoritative decision/control history; telemetry is operational instrumentation and does not replace business state.

## Correlation

Telemetry can carry project, request, task, workflow-run, run, agent, capability, service-operation and correlation identifiers. Runtime instrumentation propagates its existing request/task/workflow/run/agent/capability identities. Service/API instrumentation records project-scoped operation/status context without redesigning API authorization or idempotency.

## Persistence and Recovery

Telemetry is stored through `PersistenceStore.append_telemetry_record()` in the generic append-only event layout. SQLite schema remains `2`. `ProjectRecoverySnapshot.telemetry_records` reconstructs project-scoped operational telemetry after reopen/restart.

## Timeline

`TelemetryTimeline` returns deterministic project-scoped order by event time and telemetry identifier. Existing `AuditTimeline` remains separate for audit semantics.

## Redaction

`TelemetryRecorder` recursively redacts recognized secret/token/credential/authorization/cookie fields and `secret://...` values before persistence. Export projections apply the same redaction boundary. Caller input objects are not mutated.

## Exporter Boundary

`TelemetryExporter` is SDK-neutral. `PrometheusProjectionExporter` and `OpenTelemetryProjectionExporter` provide deterministic projection structures compatible with future concrete integrations. Phase 6 does not introduce third-party SDK/network collector dependencies.

## Health and Readiness

`ServiceHealthEvaluator` evaluates explicit required/optional component probes. Liveness/readiness is separate from Project lifecycle and operational state. Optional component degradation does not fail readiness; a failed required probe does.

## Failure Semantics

Optional Runtime and Service/API telemetry hooks fail non-fatally. Observability failure does not convert otherwise valid business execution into a new failure path.

## Existing Reliability Baseline

`MetricsCollector`, `ReliabilityValidator`, failure injection, structured audit and release/routing records remain supported. Phase 6 extends rather than replaces those predecessor surfaces.

## Validation Baseline

```text
Implementation SHA: 8f3d9a85abd68e1ab83dbf7ca87f3dadfe549883
Core Validation run: 35110298258
pytest: 136 passed
branch-aware coverage: 85.52%
Core Validation: PASS
```

Completion evidence: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_6_COMPLETE.md`.
