# PERSISTENCE
Документ описує persistence boundary, SQLite hardening, durable control state, Project Registry та recovery semantics K_Supervisor.

Version: 1.8
Status: ACTIVE
Baseline: ROADMAP v0.3 COMPLETE — Phase 8 operational persistence qualified
Date: 2026-09-16

## 1. Purpose

Persistence is platform-owned authoritative state. v0.3 Phase 1 hardened storage lifecycle/schema evolution; Phase 2 moved critical control state onto durable restart-safe records and strengthened atomic state+audit writes; Phase 3 added authoritative side-effect attempt/outcome state; Phase 5 adds durable Service/API mutation replay receipts and uses the same transaction boundary as Project lifecycle writes.

Agents do not access SQLite directly.

## 2. Persistence Boundary

Backend-neutral contract:

```text
persistence/base.py
```

Current local backend:

```text
persistence/sqlite_store.py
```

SQLite remains an implementation backend, not a public physical-layout contract. Consumers use persistence interfaces rather than table/index names.

## 3. SQLite Lifecycle and Schema

`SQLitePersistenceStore` provides explicit lifecycle ownership, idempotent initialize/close, context-manager use, rollback on abandoned transactions, WAL mode, foreign-key enforcement and bounded busy timeout.

Current physical schema version remains:

```text
2
```

The tested v1 -> v2 migration remains authoritative. Phases 2, 3 and 5 use the existing generic `resources` / `events` layout, so physical schema version remains `2`.

Unknown/future schema versions fail closed.

## 4. Storage Model

```text
resources
- current authoritative snapshots
- keyed by kind + resource_id
- project scoped

events
- append-only histories
- ordered by event_id
- project scoped
```

Schema metadata is stored in `schema_meta`; physical SQLite layout remains internal.

## 5. Durable Resources

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
RuntimeIdempotencyRecord
ServiceMutationRecord
SideEffectExecutionRecord
```

`RuntimeIdempotencyRecord` stores the project-scoped semantic command scope, canonical input signature and prior successful `AgentRunResult`. This supports replay after supported store/process restart without invoking the handler again.

`ServiceMutationRecord` stores the project/API/operation/idempotency-key scope, canonical request signature and resulting `Project` snapshot for completed Service/API mutations. It is immutable by deterministic identifier and supports restart-safe replay without a second lifecycle transition.

`SideEffectExecutionRecord` stores the normalized Tool/Provider attempt identity, project/request/agent/capability/component correlation, idempotency key, canonical input signature, policy decision, status, normalized output/error and completion time.

ProjectSpec, ArtifactReference, RuntimeIdempotencyRecord and ServiceMutationRecord are immutable by identifier. Conflicting immutable payloads raise `PersistenceConflictError`.

## 6. Durable Events

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

Notification SENT attempt history is authoritative for restart-safe duplicate suppression in the standard Notification Broker path.

## 7. Atomic Control-State Boundary

Top-level SQLite transactions use `BEGIN IMMEDIATE`, commit on success and roll back on failure. Nested store operations participate in the existing transaction.

Phase 2/3/5 add and use atomic persistence helpers for:

- Project snapshot + required audit;
- Project lifecycle transition + Project snapshot + required audit;
- Project operational transition + Project snapshot + required audit;
- HumanActionRequest + Project operational transition/snapshot + required audit where applicable;
- HumanActionRequest-only mutation + required audit;
- ApprovalRecord mutation + required audit;
- side-effect PENDING claim + `SIDE_EFFECT_ATTEMPTED` audit;
- side-effect terminal outcome + `SIDE_EFFECT_SUCCEEDED` / `SIDE_EFFECT_FAILED` audit;
- Service/API lifecycle/operational transition + resulting Project snapshot + transition audit + immutable ServiceMutationRecord receipt through one outer transaction.

ProjectSpec activation builds the audit record before committing the resulting active Project snapshot and audit together. The immutable ProjectSpec record itself remains independently durable history.

Failure-injection tests prove that an audit failure inside the lifecycle transaction rolls back both the transition event and resulting Project snapshot.

This is not a universal distributed transaction across repositories or external providers. Phase 3 owns centralized external side-effect enforcement; Phase 5 only extends local authoritative transactionality to Service/API mutation receipts.

## 8. Approval Control State

Approval records now support:

```text
PENDING
APPROVED
REJECTED
EXPIRED
REVOKED
```

Durable fields cover expiry, expiration time, revocation time and revocation reason. Expiry/revocation changes are persisted with normalized audit records.

Existing historical approval records remain compatible because new lifecycle fields are optional/defaulted.

## 9. Runtime Idempotency

The standard runtime can use `PersistenceIdempotencyStore` when platform persistence is supplied to `AgentRuntimeDispatcher`.

The durable scope includes project, agent, capability/version, operation and idempotency key. Input signature mismatch is rejected. Same-key commands in different projects remain isolated.

`MemoryIdempotencyStore` remains a backward-compatible standalone fallback but does not claim restart durability.

Concurrent durable claims use immutable persistence semantics; a conflicting concurrent claim is accepted only when the already-authoritative record has the same signature.

## 10. Project Recovery Aggregate

`ProjectRecoverySnapshot` now reconstructs:

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
HumanActionRequests
NotificationEvents
NotificationDeliveryAttempts
ApprovalRecords
RuntimeIdempotencyRecords
ServiceMutationRecords
TelemetryRecords
SideEffectExecutionRecords
PolicyDecisions
AuditEvents
RoutingRecords
ReleaseValidationRecords
```

This is the authoritative project-scoped reconstruction boundary for currently persisted control records.

Phase 2 verifies a project waiting for owner intervention with an active Task/WorkflowRun survives restart and can resume through the normal Human Intervention Broker without hidden process memory.

## 11. Resource Hygiene and Concurrency

Core Validation treats `ResourceWarning` as an error. Supported SQLite concurrency remains independent local connections against the WAL database with bounded contention handling.

Distributed database coordination, cross-region replication and mandatory PostgreSQL remain outside the current roadmap requirement.

## 12. Validation Baseline

Authoritative v0.3 Phase 6 runtime baseline:

```text
Implementation SHA: 8f3d9a85abd68e1ab83dbf7ca87f3dadfe549883
Core Validation run: 35110298258
Python workflow: 3.13
pytest: 136 passed
branch-aware coverage: 85.52%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples/service_api: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Phase 5 persistence verification covers durable service mutation replay, restart continuity, immutable replay conflicts and failure-injection rollback of Project transition + audit when the service receipt cannot be persisted.

## 13. Current Boundary

Phase 5 adds restart-visible Service/API mutation receipts without introducing a second project state store or new physical schema. A completed receipt is authoritative for same-key replay; a different request signature under the same deterministic scope fails closed. The receipt is committed in the same supported SQLite transaction as the underlying Project transition/audit.

Universal distributed transactions, multi-node consensus, distributed databases and exactly-once guarantees across external systems remain outside this persistence boundary.

## 14. Phase 6 Telemetry Persistence

`TelemetryRecord` is append-only operational telemetry stored in the existing generic `events` layout as `telemetry_record`. It carries project-scoped correlation and redacted attributes, survives reopen/restart and is reconstructed through `ProjectRecoverySnapshot.telemetry_records`. Phase 6 requires no physical schema migration; schema version remains `2`.

## 15. Phase 8 Operational Backup, Restore and Upgrade Qualification

`SQLiteOperationalManager` is the supported persistence-owned operational safety boundary. It does not change the authoritative physical schema version, which remains `2`.

Supported operations:

- `backup_to()` uses the SQLite online backup API and verifies the resulting database before atomic placement at the requested backup path;
- `verify_backup()` validates SHA-256 when supplied, SQLite `integrity_check`, and persistence schema metadata;
- `qualify_upgrade()` migrates a temporary copy through the normal `SQLitePersistenceStore` initialization path and proves the source backup remains byte-for-byte unchanged;
- `restore_from()` requires the authoritative store to be closed, qualifies/migrates a temporary candidate before replacement, performs atomic replacement, and keeps rollback copies of the prior SQLite database family for replacement/post-verify failure recovery.

Unknown/future schemas and corrupt candidates fail closed. A restore candidate never becomes authoritative merely because it is a syntactically valid SQLite file.

Operational procedure and rollback guidance are maintained in `OPERATIONS_RUNBOOK.md`.
