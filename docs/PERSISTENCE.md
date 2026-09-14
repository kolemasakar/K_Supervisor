# PERSISTENCE
Документ описує persistence boundary, SQLite hardening, durable control state, Project Registry та recovery semantics K_Supervisor.

Version: 1.4
Status: ACTIVE
Baseline: v0.3 Phase 2 COMPLETE
Date: 2026-09-14

## 1. Purpose

Persistence is platform-owned authoritative state. v0.3 Phase 1 hardened storage lifecycle/schema evolution; v0.3 Phase 2 moved critical control state onto durable restart-safe records and strengthened atomic state+audit writes.

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

The tested v1 -> v2 migration remains authoritative. Phase 2 required no new physical schema because durable control records use the existing generic `resources` / `events` layout.

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
```

`RuntimeIdempotencyRecord` stores the project-scoped semantic command scope, canonical input signature and prior successful `AgentRunResult`. This supports replay after supported store/process restart without invoking the handler again.

ProjectSpec, ArtifactReference and RuntimeIdempotencyRecord are immutable by identifier. Conflicting immutable payloads raise `PersistenceConflictError`.

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

Phase 2 adds/uses atomic persistence helpers for:

- Project snapshot + required audit;
- Project lifecycle transition + Project snapshot + required audit;
- Project operational transition + Project snapshot + required audit;
- HumanActionRequest + Project operational transition/snapshot + required audit where applicable;
- HumanActionRequest-only mutation + required audit;
- ApprovalRecord mutation + required audit.

ProjectSpec activation builds the audit record before committing the resulting active Project snapshot and audit together. The immutable ProjectSpec record itself remains independently durable history.

Failure-injection tests prove that an audit failure inside the lifecycle transaction rolls back both the transition event and resulting Project snapshot.

This is not a universal distributed transaction across repositories or external providers. Phase 3 owns centralized external side-effect enforcement.

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

Authoritative v0.3 Phase 2 implementation baseline:

```text
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Core Validation run: 34808287772
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

Phase-specific evidence is recorded in `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`.

## 13. Current Boundary

Persistence/resource hygiene and durable control-state scope are complete through Phase 2. Phase 3 must build centralized external side-effect enforcement on top of these durable policy/idempotency/audit primitives; it must not create a bypass around authoritative persistence.
