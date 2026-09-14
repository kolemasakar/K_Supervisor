# OBSERVABILITY_AND_RELIABILITY
Канонічний baseline спостережуваності, аудиту, reliability-перевірок і CI quality gates K_Supervisor.

Version: 1.0
Status: ACTIVE
Phase: 15

## Purpose

Phase 15 makes platform behavior diagnosable without creating a second business-state store. Project, Task, AgentRun, HumanAction, Notification, Release and policy records remain authoritative. Observability adds append-only normalized records and derived views.

## Structured Audit

`AuditEvent` contains:

```text
audit_event_id
project_id
category
event_type
occurred_at
resource_type
resource_id
severity
correlation_id
details
```

Audit payloads must contain identifiers and diagnostic state only. Raw credentials, protected access values, notification bodies and private chain-of-thought are not audit payloads.

The current audited boundaries are:

- ProjectSpec activation and Project lifecycle/operational transitions;
- HumanAction open, verify and cancel;
- notification record, suppression, duplicate suppression and delivery outcome;
- routing decisions through `ObservableSupervisorKernel`;
- release readiness validation;
- release publication-required and publication-confirmed target events.

`AuditTimeline` is an ordered view over the append-only audit stream and does not synthesize duplicate copies of authoritative events.

## Routing Records

`RoutingRecord` preserves capability requirement, candidate agent IDs, selected agent/version, Task/Workflow correlation and routing outcome. Phase 15 provides `ObservableSupervisorKernel`, a transparent wrapper around the stable Phase 5 kernel. Platform compositions that require normalized routing records use this wrapper; the underlying Supervisor API is unchanged.

## Release Validation Records

Every normal `TargetPreparer` readiness check appends `ReleaseValidationRecord` with passed and failed check IDs. Publication handoff and target publication also emit release audit events.

## Metrics

`MetricsCollector` derives a snapshot from persisted platform state. Current project metrics include transition, task, agent-run, routing, intervention, notification/delivery, release-validation and audit counts. Per-agent metrics include run outcome counts and success rate.

Metrics are derived and are not a second source of truth.

## Reliability Validation

`ReliabilityValidator` checks cross-record integrity for:

- AgentRun -> Task and WorkflowRun;
- RoutingRecord -> Task and WorkflowRun;
- selected routing agent membership in recorded candidates;
- NotificationDeliveryAttempt -> NotificationEvent;
- ReleaseTarget -> Release;
- ReleaseValidationRecord -> Release and ReleaseTarget.

The validator reports deterministic errors rather than repairing state implicitly.

## Failure Injection and Recovery

`DeterministicFailureInjector` provides call-number-based failure injection for integration tests. Phase 15 uses it to exercise notification-delivery failure behavior.

SQLite restart tests verify that observability event records, including release validation evidence, survive process restart.

## CI Quality Gates

Core Validation now includes:

```text
Python 3.13
compileall syntax gate
full pytest regression suite
branch-aware pytest-cov measurement
minimum total coverage: 80%
coverage.xml generation
routing performance baseline test
```

The performance baseline requires 10,000 deterministic provider selections to complete within 3 seconds on the GitHub-hosted CI runner. It is a regression guard, not a throughput guarantee.

## Reliability Boundaries

Normalized audit appends are adjacent to authoritative business writes but are not one cross-component atomic transaction in every path. The authoritative lifecycle, intervention, notification, policy and release records remain the recovery source if a normalized audit append fails.

Phase 15 does not add distributed tracing, OpenTelemetry/Prometheus exporters, remote log aggregation, SLO management, production latency histograms or distributed event streaming. These remain future extensions behind the current contracts.
