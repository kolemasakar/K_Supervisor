# PERSISTENCE
Документ описує persistence baseline, Project Registry та актуальні recovery semantics K_Supervisor.

Version: 1.2
Status: ACTIVE
Baseline Phase: 2
Updated through: Phase 15

## 1. Purpose

Phase 2 established durable project identity and reconstructable project state without relying on hidden process memory. Later phases extend the same platform-owned persistence boundary with additional durable resources and append-only events.

Agents do not access SQLite directly.

## 2. Persistence Boundary

The persistence contract is defined by:

```text
persistence/base.py
```

The initial local implementation is:

```text
persistence/sqlite_store.py
```

SQLite is a baseline backend, not a permanent architectural requirement.

## 3. Storage Model

The local backend uses two logical storage classes:

```text
resources
- current entity snapshots
- keyed by kind + resource_id
- isolated by project_id

events
- append-only histories
- ordered by event_id
- isolated by project_id
```

Schema metadata is stored separately. The current SQLite schema version remains `1` because later logical resource/event kinds reuse the generic `resources` and `events` tables without requiring a physical schema migration.

SQLite WAL mode is enabled.

## 4. Persisted Resources

The durable resource boundary currently includes:

```text
Project
ProjectSpec
Task
WorkflowRun
AgentRunResult
ArtifactReference
Release
ReleaseTarget
HumanActionRequest
NotificationEvent
ApprovalRecord
```

ProjectSpec and ArtifactReference snapshots are immutable by identifier. Re-saving the identical snapshot is idempotent; changing an existing immutable identifier raises `PersistenceConflictError`.

Release and ReleaseTarget are mutable state records with explicit state machines enforced by the release layer.

## 5. Persisted Events

Append-only event records currently include:

```text
ProjectLifecycleTransition
ProjectOperationalTransition
NotificationDeliveryAttempt
PolicyDecision
AuditEvent
RoutingRecord
ReleaseValidationRecord
```

Phase 15 observability records use the existing append-only event table and remain project-scoped.

Lifecycle/operational transition helpers can commit a transition and resulting Project snapshot atomically in one SQLite transaction. Human-intervention transitions can atomically store the HumanActionRequest, matching operational transition and resulting Project snapshot.

Normalized observability events are adjacent audit records. They do not replace authoritative business state and are not guaranteed to be part of the same transaction as every cross-component business write.

## 6. Project Registry

`registry/project_registry.py` is the project identity and primary recovery boundary.

Primary operations:

```text
register
get
list
add_spec
activate_spec
transition_lifecycle
transition_operational
recover
```

The registry enforces ProjectSpec/project matching, APPROVED activation, explicit lifecycle/operational transitions, timezone-aware timestamps and project-scoped recovery. Phase 15 additionally records normalized audit events for ProjectSpec activation and project state transitions.

## 7. Recovery Snapshot

`ProjectRecoverySnapshot` currently reconstructs:

```text
Project
active ProjectSpec
ProjectSpec history
lifecycle transitions
operational transitions
Tasks
WorkflowRuns
AgentRunResults
ArtifactReferences
Releases
ReleaseTargets
```

HumanActionRequest, NotificationEvent/delivery, ApprovalRecord, PolicyDecision, AuditEvent, RoutingRecord and ReleaseValidationRecord are durable through persistence APIs but are not all aggregated into `ProjectRecoverySnapshot`.

## 8. Release and Observability Persistence

ReleaseTarget persists target-specific release state, artifacts, checklist, HumanAction correlation and publication timestamp.

Phase 15 additionally persists each automated release readiness evaluation as a `ReleaseValidationRecord` containing target/release correlation and passed/failed check IDs. These records survive SQLite restart and support reliability diagnostics without inferring historical readiness solely from current repository files.

`AuditEvent` and `RoutingRecord` provide structured project-level diagnostics. Metrics are derived from persisted records and are not stored as a second source of truth.

## 9. Parallel Project Isolation

Every persisted resource and event carries `project_id`. Queries used by platform recovery and observability boundaries are project-scoped, so one project waiting, failing, or resuming does not overwrite another project's state.

Scheduler-owned concurrency and global resource limits remain outside persistence.

## 10. Local Data Location

Runtime databases are local runtime artifacts and must not be committed to Git.

Recommended default location:

```text
runtime/k_supervisor.db
```

The final platform configuration and packaging mechanism belongs to Phase 16.

## 11. Validation Baseline

Current validated platform baseline after Phase 15 implementation:

```text
Python 3.13.15
81 tests PASS
branch-aware coverage: 85.57%
coverage gate: >= 80%
Core Validation run: 34792502459
head SHA: e68c7f3d61302a4b5bf494e392586cf09522e8e1
```

Coverage includes restart/recovery, project isolation, immutable ProjectSpec history, state transitions, human intervention, policy audit persistence, release persistence, ReleaseTarget recovery, Phase 15 release-validation recovery and normalized audit/routing records.

## 12. Baseline Limits

- SQLite is the initial backend, not a permanent storage commitment.
- `ProjectRecoverySnapshot` is not a universal aggregate of every durable resource/event type.
- Cross-system operations involving repository files, providers or normalized audit append are not one universal transaction.
- Migration/versioning beyond schema version `1` is deferred until the physical database schema requires it.
- Metrics are derived snapshots rather than persisted time-series telemetry.

## 13. Phase 2 Exit Criteria

The original Phase 2 criteria remain satisfied:

- projects survive persistence store restart;
- current project state can be reconstructed from durable records;
- ProjectSpec history remains immutable;
- lifecycle and operational histories are retained;
- tasks, workflows, agent runs, artifacts and releases have persistence boundaries;
- multiple projects are stored and recovered independently.
