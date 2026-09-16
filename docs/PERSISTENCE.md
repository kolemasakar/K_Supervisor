# PERSISTENCE
Документ описує persistence boundary, SQLite hardening, durable control state, Project Registry та recovery semantics K_Supervisor.

Version: 1.5
Status: ACTIVE
Baseline: v0.3 Phase 3 implementation
Date: 2026-09-16

## 1. Purpose

Persistence is platform-owned authoritative state. v0.3 Phase 1 hardened storage lifecycle/schema evolution; v0.3 Phase 2 moved critical control state onto durable restart-safe records and strengthened atomic state+audit writes. v0.3 Phase 3 adds authoritative side-effect attempt/outcome state for the centralized Tool/Provider gateway.

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

The tested v1 -> v2 migration remains authoritative. Phase 2 required no new physical schema because durable control records use the existing generic `resources` / `events` layout. Phase 3 also uses that generic layout, so physical schema version remains `2`.

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
SideEffectExecutionRecord
```

`RuntimeIdempotencyRecord` stores the project-scoped semantic command scope, canonical input signature and prior successful `AgentRunResult`. This supports replay after supported store/process restart without invoking the handler again.

`SideEffectExecutionRecord` stores the normalized Tool/Provider attempt identity, project/request/agent/capability/component correlation, idempotency key, canonical input signature, policy decision, status, normalized output/error and completion time.

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

Phase 2/3 add and use atomic persistence helpers for:

- Project snapshot + required audit;
- Project lifecycle transition + Project snapshot + required audit;
- Project operational transition + Project snapshot + required audit;
- HumanActionRequest + Project operational transition/snapshot + required audit where applicable;
- HumanActionRequest-only mutation + required audit;
- ApprovalRecord mutation + required audit;
- side-effect PENDING claim + `SIDE_EFFECT_ATTEMPTED` audit;
- side-effect terminal outcome + `SIDE_EFFECT_SUCCEEDED` / `SIDE_EFFECT_FAILED` audit.

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

The predecessor authoritative v0.3 Phase 2 baseline remains:

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

Phase-specific Phase 2 evidence is recorded in `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`. Phase 3 completion evidence is recorded only after Core Validation passes on its committed implementation SHA.

## 13. Current Boundary

Phase 3 adds restart-visible side-effect execution records and atomic attempt/outcome audit without claiming a distributed transaction with an external provider. A PENDING record after interruption is authoritative evidence that the platform cannot safely infer whether an external system completed the operation; supported-path retries therefore fail closed/replay the authoritative state rather than silently issuing a duplicate. Universal exactly-once external delivery remains out of scope.
