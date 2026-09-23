# OBSERVABILITY_AND_RELIABILITY
Production observability and reliability boundary for K_Supervisor.

Version: 3.0
Status: ACTIVE
Baseline: ROADMAP v0.4 Phase 6 implementation through trusted-main attestations
Date: 2026-09-23

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

## Phase 8 Deployment Qualification

`DeploymentQualifier` composes existing reliability/health boundaries rather than creating a new deployment control plane. Qualification checks:

- current SQLite schema and SQLite integrity through `SQLiteOperationalManager`;
- required/optional service component probes through `ServiceHealthEvaluator`;
- `ProjectRegistry.recover()` for selected Projects;
- referential integrity through `ReliabilityValidator`.

A failed required service probe or Project/store integrity check makes the deployment candidate not ready. Project lifecycle state is not treated as service readiness. The qualifier performs validation only; it does not deploy hosts, configure TLS, publish packages or bypass owner actions.

Operational procedures are documented in `OPERATIONS_RUNBOOK.md`.


## v0.4 Phase 6 Production Boundary

Phase 6 extends the predecessor telemetry compatibility floor with:

- frozen production event schemas and schema-driven safe attributes;
- deterministic structured JSON logging;
- bounded low-cardinality production metric families;
- service/auth/provider/repository/release boundary instrumentation;
- bounded exporter queue/retry/timeout/drop accounting;
- optional OTLP/HTTP export and Prometheus-compatible exposition.

`ProductionObservability` fans one safe event into durable telemetry, structured logging and bounded metrics. Each sink is best-effort. Sink/export failure is never an alternate control plane and does not determine a business outcome.

## Production Privacy Contract

Production attributes are allowlisted per event. Unknown attributes fail closed.

Structured logs and exported telemetry must not contain raw authorization/token/cookie/secret/provider payload content. Project identifiers are omitted from structured logging by default. Dynamic route identifiers are normalized before metric labeling.

The supported production taxonomy covers:

- service request lifecycle;
- authentication accepted/rejected;
- policy decisions;
- provider call lifecycle;
- governed repository operations;
- release preparation and owner-publication-required boundaries;
- exporter success/failure/drop state.

## Export Runtime Contract

`BoundedExporterSupervisor` enforces finite queue size, finite batch size, finite timeout and bounded retry count. Queue overflow and failed export are accounted as drops. Exporter health can be `AVAILABLE`, `DEGRADED`, `UNAVAILABLE` or `DISABLED`.

OTLP is an optional adapter boundary. The default package does not require a collector/SaaS. Prometheus compatibility is a deterministic text exposition of approved metric families, not a requirement to deploy Prometheus/Grafana.

## Supply-chain Observability Evidence

Phase 6 protected CI additionally produces deterministic security evidence:

- per-Python exact dependency locks for 3.13 and 3.14;
- wheel SHA-256;
- deterministic SPDX 2.3 SBOM;
- machine-readable OSV vulnerability evidence;
- immutable full-SHA GitHub Action references;
- trusted-main build-provenance and SBOM attestations.

Vulnerability-data unavailability is explicitly different from a clean result. Attestation jobs are separated from untrusted PR validation and carry write/OIDC permissions only on the trusted-main workflow.
