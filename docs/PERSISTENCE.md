# PERSISTENCE
Документ описує persistence baseline, Project Registry та recovery semantics K_Supervisor Phase 2.

Version: 1.0
Status: ACTIVE
Phase: 2

## 1. Purpose

Phase 2 establishes durable project identity and reconstructable project state without relying on hidden process memory.

The persistence layer is platform-owned. Agents do not access SQLite directly.

## 2. Persistence Boundary

The initial contract is defined by:

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
- append-only transition history
- ordered by event_id
- isolated by project_id
```

Schema metadata is stored separately and the initial database schema version is `1`.

SQLite WAL mode is enabled.

## 4. Persisted Resources

Phase 2 persists:

```text
Project
ProjectSpec
Task
WorkflowRun
AgentRunResult
ArtifactReference
Release
```

ProjectSpec and ArtifactReference snapshots are immutable by identifier. Re-saving the identical snapshot is idempotent; changing an existing immutable identifier raises `PersistenceConflictError`.

## 5. Persisted Events

Phase 2 persists append-only records for:

```text
ProjectLifecycleTransition
ProjectOperationalTransition
```

A state transition and the resulting Project snapshot are committed atomically in one SQLite transaction.

This prevents a crash from leaving a transition record without the matching current state, or a current state without its transition record.

## 6. Project Registry

`registry/project_registry.py` is the Phase 2 project identity and recovery boundary.

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

`ProjectRecoverySnapshot` reconstructs the durable platform view for one project:

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
```

The snapshot is derived entirely from persistence. No in-memory execution history is required.

## 8. Parallel Project Isolation

Every persisted resource and event carries `project_id`.

Queries used for recovery are project-scoped, so one project waiting, failing, or resuming does not overwrite another project's state.

Global scheduling and resource quotas remain a later Project Scheduler responsibility.

## 9. Local Data Location

Runtime databases are local runtime artifacts and must not be committed to Git.

Recommended default location:

```text
runtime/k_supervisor.db
```

The concrete configuration mechanism is deferred to later platform configuration work.

## 10. Validation Baseline

Phase 2 integration tests cover:

```text
restart recovery
multiple project isolation
immutable ProjectSpec history
invalid lifecycle transition rejection
```

Validated local result:

```text
4 passed
```

Phase 1 model/schema tests remain part of the repository regression suite.

## 11. Exit Criteria

Phase 2 is complete when:

- projects survive persistence store restart;
- current project state can be reconstructed from durable records;
- ProjectSpec history remains immutable;
- lifecycle and operational histories are retained;
- tasks, workflows, agent runs, artifacts, and releases have persistence boundaries;
- multiple projects are stored and recovered independently.
