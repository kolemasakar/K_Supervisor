# PROJECT_SCHEDULER
Планувальник паралельного виконання незалежних проєктів із детермінованими лімітами та ізоляцією блокувань.

Version: 1.0
Status: ACTIVE
Phase: 9

## Purpose

ProjectScheduler coordinates concurrent work across multiple managed projects without coupling scheduler workers to persistence internals.

Core form:

```text
Project + ProjectSchedulePolicy
          |
          v
     SchedulerJob queue
          |
          v
priority / state / budget / concurrency / provider / resource checks
          |
          v
parallel worker execution
```

## Scheduler Contracts

`ProjectSchedulePolicy` defines:

```text
priority
max_concurrency
budget_limit
```

`SchedulerLimits` defines:

```text
global_max_concurrency
provider_concurrency{}
```

`SchedulerJob` carries:

```text
work_id
project_id
execute
priority
provider_key
shared_resources[]
estimated_cost
```

## ProjectSpec Mapping

A scheduler policy can be derived from an approved ProjectSpec.

Supported Phase 9 keys:

```text
parallel_execution.priority
parallel_execution.max_concurrency
parallel_execution.budget_limit
risk.budget_limit
```

`risk.budget_limit` takes precedence when both budget locations are present.

## Priority

Eligible work is selected deterministically by:

1. project priority;
2. job priority;
3. FIFO submission order.

Priority never bypasses hard concurrency, provider, resource, state, or budget limits.

## Operational-State Isolation

Only projects whose cached operational state is `ACTIVE` can start new work.

A project in `WAITING_FOR_OWNER`, `WAITING_FOR_EXTERNAL`, `PAUSED`, `BLOCKED`, `DEGRADED`, or `FAILED` does not consume a global worker slot while waiting.

Other ACTIVE projects remain eligible and can continue making progress.

`notify_state_changed()` is the explicit synchronization hook after a Project Registry operational-state change.

## Persistence Thread Boundary

The Phase 2 SQLite connection remains single-thread-owned.

Scheduler worker and dispatcher threads do not query SQLite or ProjectRegistry directly. Project operational state is read in the caller thread during scheduler registration or `notify_state_changed()` and cached inside the scheduler.

This prevents SQLite cross-thread access while preserving Project Registry as the authoritative state source.

## Concurrency Limits

The scheduler enforces:

```text
global worker limit
per-project worker limit
per-provider concurrency quota
```

Provider quotas are coordination primitives for provider/rate-limit adapters. Exact external API token/request windows belong to provider adapters in Phase 10.

## Shared Resources

A SchedulerJob may declare named shared resources.

A resource key can be held by only one running job at a time. Jobs blocked on one resource remain queued while unrelated jobs may execute.

Typical future resource keys may represent:

```text
repository write lock
GPU allocation
exclusive environment
service migration lock
provider account slot
```

## Project Budget

Phase 9 uses deterministic admission accounting based on `estimated_cost`.

When a job is accepted, its estimated cost is committed against the project budget. A submission that would exceed the configured budget is rejected before execution.

This is intentionally conservative. Provider-reported actual-cost reconciliation can be added behind later provider and accounting adapters without weakening the admission guarantee.

## Shutdown and Recovery Boundary

Pending work can be cancelled during scheduler shutdown. Running work is allowed to finish when graceful shutdown is requested.

Durable queue recovery across process restarts is not claimed in Phase 9. Persistent scheduler queues can be added later without changing SchedulerJob eligibility semantics.

## Phase 9 Guarantees

```text
two independent ACTIVE projects can execute concurrently
WAITING_FOR_OWNER in one project does not stop another project
project priority is deterministic
per-project concurrency is enforced
global concurrency is enforced
provider concurrency is enforced
shared-resource exclusion is enforced
project budget admission is enforced
scheduler threads do not share the SQLite connection
```

## Next Boundary

Phase 10 adds replaceable tools/providers, provisioning adapters, protected access references, service availability checks, and provider-independent integration hooks.
