# PERSISTENCE
Документ описує persistence boundary, SQLite hardening baseline, Project Registry та recovery semantics K_Supervisor.

Version: 1.3
Status: ACTIVE
Baseline Phase: v0.3 Phase 1 COMPLETE
Date: 2026-09-14

## 1. Purpose

Persistence is platform-owned authoritative state. Phase 2 of ROADMAP v0.2 established durable project identity and restart recovery. ROADMAP v0.3 Phase 1 hardened the storage lifecycle, transaction behavior and schema evolution boundary without changing domain contracts.

Agents do not access SQLite directly.

## 2. Persistence Boundary

The backend-neutral persistence contract is defined by:

```text
persistence/base.py
```

The current local implementation is:

```text
persistence/sqlite_store.py
```

SQLite remains an implementation backend, not a public storage-layout contract. Consumers must use persistence interfaces rather than depend on SQLite table/index names. A later backend can replace SQLite behind the approved persistence boundary without changing Project/Agent/Workflow contracts.

## 3. SQLite Ownership and Lifecycle

`SQLitePersistenceStore` now has explicit connection ownership:

- `initialize()` is idempotent;
- `close()` is idempotent;
- the store supports `with SQLitePersistenceStore(path) as store:`;
- failed initialization closes the connection before propagating the error;
- closing a store rolls back any still-open transaction before closing;
- a best-effort finalizer prevents abandoned connection objects from remaining open, but explicit close/context-manager ownership remains the normal contract.

Connection configuration includes WAL mode, foreign-key enforcement, normal synchronous mode and a bounded SQLite busy timeout for supported concurrent writers.

## 4. Storage Model

The backend retains two generic logical storage classes:

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

Schema metadata is stored in `schema_meta`. Physical SQLite layout remains internal.

## 5. Schema Version and Migration

Current SQLite schema version:

```text
2
```

Phase 1 introduced a deterministic migration path from schema version `1` to `2`.

The migration:

- preserves existing resource/event data;
- creates the Phase 1 supporting resource index;
- records a storage-layout metadata marker;
- advances `schema_version` only inside the migration transaction.

Initialization of a v1 database automatically migrates it to v2. Unknown/future schema versions fail closed with an explicit error. A failed/unsupported migration does not rewrite the stored version.

New physical schema changes must add an explicit forward migration and tests. Silent reinterpretation of an incompatible layout is prohibited.

## 6. Transaction Boundary

The SQLite backend exposes an internal explicit transaction context used by authoritative writes.

Top-level transactions use `BEGIN IMMEDIATE`, commit on success and roll back on failure. Nested store operations participate in the existing transaction instead of committing independently.

This preserves atomic helpers such as:

- lifecycle transition + resulting Project snapshot;
- operational transition + resulting Project snapshot;
- HumanActionRequest + operational transition + resulting Project snapshot.

Phase 1 additionally verifies rollback of a write when the surrounding authoritative transaction fails.

Cross-system operations involving repositories or external providers are still not one universal distributed transaction; later roadmap phases own those control-state and side-effect boundaries.

## 7. Persisted Resources

The durable resource boundary includes:

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

ProjectSpec and ArtifactReference snapshots remain immutable by identifier. Re-saving the same snapshot is idempotent; changing an existing immutable identifier raises `PersistenceConflictError`.

## 8. Persisted Events

Append-only event records include:

```text
ProjectLifecycleTransition
ProjectOperationalTransition
NotificationDeliveryAttempt
PolicyDecision
AuditEvent
RoutingRecord
ReleaseValidationRecord
```

Normalized observability events do not replace authoritative business state.

## 9. Project Registry and Recovery

`registry/project_registry.py` remains the project identity and primary recovery boundary.

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

`ProjectRecoverySnapshot` reconstructs the baseline Project aggregate used by Project Registry. Later v0.3 Phase 2 is responsible for richer durable control-state aggregation; Phase 1 intentionally does not expand that domain contract.

Restart/reopen recovery remains deterministic after the v1 -> v2 migration.

## 10. Supported SQLite Concurrency

Phase 1 validates separate store instances using independent SQLite connections writing to the same WAL database concurrently.

The boundary is intentionally local-process/local-file SQLite concurrency, not distributed database coordination. `busy_timeout` provides bounded contention handling while SQLite serializes writers.

Distributed clustering, cross-region replication and mandatory PostgreSQL remain outside Phase 1.

## 11. Resource Hygiene Gate

Core Validation now executes pytest with:

```text
-W error::ResourceWarning
```

A Python `ResourceWarning`, including an unclosed SQLite connection, fails CI. The previous known SQLite connection warnings are therefore eliminated as a regression class rather than merely hidden.

Tests should still prefer explicit context-manager or `close()` ownership.

## 12. Validation Baseline

Authoritative v0.3 Phase 1 implementation baseline:

```text
Implementation SHA: 661ee7d0ce973a862d9605df18e1b1f52c48aa02
Core Validation run: 34804141156
Python: 3.13.15
pytest: 95 passed
branch-aware coverage: 85.66%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Phase-specific verification covers:

- context-manager connection lifecycle;
- idempotent initialize/close;
- v1 -> v2 forward migration with data preservation;
- fail-closed unsupported schema handling;
- authoritative transaction rollback;
- concurrent writers using independent connections;
- no unclosed SQLite `ResourceWarning`;
- existing restart/recovery behavior.

## 13. Phase 1 Exit Result

ROADMAP v0.3 Phase 1 exit criteria are satisfied:

- zero known SQLite ResourceWarning leaks under Core Validation;
- deterministic restart/reopen recovery remains intact;
- unsupported schema versions fail safely;
- forward migration from the predecessor schema is tested;
- SQLite physical layout remains behind the persistence abstraction;
- all predecessor regression gates pass.

The next persistence-related control-state work belongs to v0.3 Phase 2, not to this completed storage-hygiene phase.
