# PERSISTENCE
Документ описує persistence baseline, Project Registry та актуальні recovery semantics K_Supervisor.

Version: 1.1
Status: ACTIVE
Baseline Phase: 2
Updated through: Phase 13

## 1. Purpose

Phase 2 established durable project identity and reconstructable project state without relying on hidden process memory. Later phases extend the same platform-owned persistence boundary with additional durable resources and events.

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

Schema metadata is stored separately and the current SQLite schema version remains `1` because later logical resource kinds use the existing generic resources/events tables.

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
```

Lifecycle/operational transition helpers can commit a transition and resulting Project snapshot atomically in one SQLite transaction.

Human-intervention transitions can atomically store the HumanActionRequest, matching operational transition and resulting Project snapshot.

Other multi-resource workflows may use conservative ordered writes but are not automatically one transaction across external repository/provider effects.

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

The registry enforces:

- ProjectSpec/project identity matching;
- only APPROVED ProjectSpec may become active;
- explicit lifecycle transition validation;
- explicit operational transition validation;
- timezone-aware transition timestamps;
- project-scoped recovery.

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

The snapshot is derived entirely from persistence. No in-memory execution history is required for these fields.

HumanActionRequest, NotificationEvent/delivery, ApprovalRecord and PolicyDecision records are also durable, but they are currently accessed through their persistence APIs rather than aggregated into `ProjectRecoverySnapshot`.

## 8. Release Persistence

Phase 13 adds durable target-specific release state:

```text
Release
  +-- ReleaseTarget: GPT_STORE
  +-- ReleaseTarget: other declared target
```

Each ReleaseTarget can independently retain:

- target status;
- readiness criteria;
- generated artifact paths;
- release checklist;
- publication HumanActionRequest correlation;
- published timestamp.

This allows release preparation to survive restart without inferring target state from repository files alone.

## 9. Parallel Project Isolation

Every persisted resource and event carries `project_id`.

Queries used by platform recovery boundaries are project-scoped, so one project waiting, failing, or resuming does not overwrite another project's state.

Scheduler-owned concurrency and global resource limits remain outside persistence.

## 10. Local Data Location

Runtime databases are local runtime artifacts and must not be committed to Git.

Recommended default location:

```text
runtime/k_supervisor.db
```

The final platform configuration/packaging mechanism remains later roadmap work.

## 11. Validation Baseline

The persistence regression suite now runs as part of permanent Core Validation together with later platform layers.

Current validated platform baseline after Phase 13:

```text
Python 3.13.15
70 tests PASS
Core Validation run: 34780169394
```

Coverage includes restart/recovery, project isolation, immutable ProjectSpec history, state transitions, human intervention, policy audit persistence, release persistence, and ReleaseTarget recovery.

## 12. Baseline Limits

- SQLite is the initial backend, not a permanent storage commitment.
- `ProjectRecoverySnapshot` is not yet a universal aggregate of every durable resource/event type.
- Cross-system operations involving repository files or external providers are not one SQLite transaction.
- Migration/versioning beyond schema version `1` is deferred until the physical database schema requires a migration.

## 13. Phase 2 Exit Criteria

The original Phase 2 criteria remain satisfied:

- projects survive persistence store restart;
- current project state can be reconstructed from durable records;
- ProjectSpec history remains immutable;
- lifecycle and operational histories are retained;
- tasks, workflows, agent runs, artifacts, and releases have persistence boundaries;
- multiple projects are stored and recovered independently.
