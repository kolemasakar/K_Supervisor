# PROJECT_LIFECYCLE
Життєвий цикл проєкту K_Supervisor від ідеї та вступного обговорення до release-ready стану й супроводу.

Version: 0.1
Status: ACTIVE
Phase: 0

## 1. Purpose

This document defines project lifecycle semantics for K_Supervisor.

Project lifecycle state is separate from operational execution state, roadmap phase, release state, and task/workflow/run state.

## 2. Lifecycle States

```text
IDEA
ONBOARDING
SPEC_REVIEW
APPROVED
PROVISIONING
BOOTSTRAPPED
BUILDING
VALIDATING
FIRST_WORKING
RELEASE_PREPARATION
RELEASE_READY
MAINTENANCE
ARCHIVED
TERMINATED
```

## 3. Operational States

```text
ACTIVE
PAUSED
WAITING_FOR_OWNER
WAITING_FOR_EXTERNAL
BLOCKED
DEGRADED
FAILED
```

`WAITING_FOR_OWNER` is an operational state, not a lifecycle stage.

Example:

```text
project_lifecycle_state = BUILDING
project_operational_state = WAITING_FOR_OWNER
```

After the required owner action is verified, the project may return to `ACTIVE` without changing its lifecycle stage.

## 4. Onboarding Flow

```text
IDEA
 -> ONBOARDING
 -> SPEC_REVIEW
 -> APPROVED
```

ONBOARDING collects project purpose, target users, documentation expectations, repository requirements, integrations, infrastructure, access requirements, release targets, autonomy policy, notification policy, and success criteria.

Its primary output is a Draft ProjectSpec.

SPEC_REVIEW allows revision, approval, rejection, or termination.

Only an approved ProjectSpec authorizes normal automated provisioning.

## 5. Provisioning and Bootstrap

```text
APPROVED
 -> PROVISIONING
 -> BOOTSTRAPPED
```

PROVISIONING creates or connects approved project resources and verifies the minimum access required for bootstrap.

If owner action is required, the project keeps lifecycle state `PROVISIONING` and changes operational state to `WAITING_FOR_OWNER`.

BOOTSTRAPPED means the minimum managed project structure exists, normally including repository, baseline documentation, roadmap, architecture baseline, project registry entry, and initial automation configuration where required.

## 6. Build and Validation Loop

```text
BOOTSTRAPPED
 -> BUILDING
 -> VALIDATING
 -> BUILDING      when criteria are not met
 -> FIRST_WORKING when first-working criteria are met
```

BUILDING performs roadmap implementation, agent/workflow creation, integration work, tests, and documentation.

VALIDATING checks the current implementation against the active project criteria and records known limitations.

## 7. First Working Milestone

`FIRST_WORKING` means the primary intended function is demonstrably operational under the approved minimum criteria.

This milestone should normally produce:

- an audit record;
- an owner email notification;
- a checkpoint artifact;
- a release-target readiness assessment.

FIRST_WORKING is not equivalent to production-ready or published.

Possible next paths:

```text
FIRST_WORKING -> BUILDING
FIRST_WORKING -> RELEASE_PREPARATION
FIRST_WORKING -> MAINTENANCE
```

## 8. Release Preparation

```text
RELEASE_PREPARATION
 -> BUILDING       when further implementation is required
 -> RELEASE_READY  when target-specific readiness checks pass
```

Release preparation creates target-specific assets, validation results, checklists, and explicit owner-action requirements.

For ChatGPT-facing projects, `CHATGPT_PLUGIN` is the preferred target. K_Supervisor prepares portable skill/workflow, integration, regression and access evidence; legacy `GPT_STORE` remains available only for compatibility/migration. Actual external availability remains a per-project owner or workspace-admin action.

## 9. Release State

Release state is separate from project lifecycle because one project may have multiple releases or release targets.

```text
DRAFT
PREPARING
READY
PUBLICATION_REQUIRED
PUBLISHED
FAILED
WITHDRAWN
SUPERSEDED
```

For owner-published targets, the normal handoff is:

```text
READY -> PUBLICATION_REQUIRED
```

## 10. Maintenance and End States

MAINTENANCE covers continued support, fixes, improvements, dependency updates, and new releases.

A maintenance project may return to BUILDING for a new roadmap phase.

ARCHIVED means intentionally inactive while preserving history.

TERMINATED means project work has been intentionally ended and must not resume automatically.

## 11. Human Intervention

Human intervention does not erase project progress.

Example:

```text
Project A: lifecycle=PROVISIONING, operational=WAITING_FOR_OWNER
Project B: lifecycle=BUILDING, operational=ACTIVE
Project C: lifecycle=VALIDATING, operational=ACTIVE
```

Project Scheduler may continue Projects B and C while Project A waits.

## 12. Failure Semantics

Execution failure normally changes operational state first.

Example:

```text
lifecycle = BUILDING
operational = FAILED
```

Recovery may restore `ACTIVE` without changing lifecycle state.

A lifecycle transition to TERMINATED requires a project-level decision rather than an ordinary execution exception.

## 13. Parallel Projects

Project state is isolated per project.

Concurrent execution is subject to project and global limits for concurrency, providers, cost, compute, and shared resources.

A blocked project must not globally block unrelated project work.

## 14. Audit Requirements

Each lifecycle transition should record:

```text
project_id
from_state
to_state
reason
trigger
timestamp
related approval or artifact references
```

Operational state changes are recorded separately.

## 15. Machine State Model

Phase 0 defines lifecycle semantics.

Phase 1 must implement validated lifecycle and operational state models plus allowed transition rules.
