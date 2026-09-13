# RELEASE_MANAGER
Керування підготовкою релізів, перевіркою готовності та передачею публікації власнику.

Version: 1.0
Status: ACTIVE
Phase: 13

## Purpose

Release Manager turns a project that reached `FIRST_WORKING` into target-specific release readiness without taking ownership of external publication.

Core path:

```text
FIRST_WORKING
  -> RELEASE_PREPARATION
  -> generic readiness checks
  -> target preparation profile
  -> generated release assets
  -> target READY
  -> project RELEASE_READY
  -> PUBLICATION_REQUIRED
  -> explicit owner publication
  -> owner confirmation
  -> PUBLISHED
```

## Durable Contracts

`Release` tracks the project-level release state.

`ReleaseTarget` tracks one target such as `GPT_STORE` independently and stores:

- target type;
- state;
- readiness criteria;
- generated artifact paths;
- target checklist;
- owner-publication requirement;
- HumanActionRequest correlation;
- publication timestamp.

Release targets are persisted independently and are included in `ProjectRecoverySnapshot`.

## State Machines

Both Release and ReleaseTarget use explicit transitions:

```text
DRAFT -> PREPARING
PREPARING -> READY | FAILED
READY -> PUBLICATION_REQUIRED | PUBLISHED | FAILED
PUBLICATION_REQUIRED -> PUBLISHED | FAILED
FAILED -> PREPARING | WITHDRAWN
PUBLISHED -> SUPERSEDED
```

Invalid transitions fail deterministically.

## Generic Readiness

`GenericReleaseReadinessChecker` validates:

- project reached `FIRST_WORKING` or a later release lifecycle state;
- target is declared by the active approved ProjectSpec;
- required project documents are present;
- explicitly declared release readiness criteria have evidence.

A failed required check keeps the project in `RELEASE_PREPARATION`, marks the release/target failed, and does not open a publication owner action.

## GPT Store Profile

The initial target-specific profile is `GPT_STORE`.

Automatically generated assets:

```text
release/gpt_store/GPT_STORE_PROFILE.json
release/gpt_store/GPT_INSTRUCTIONS.md
release/gpt_store/GPT_STORE_LISTING.md
release/gpt_store/GPT_PUBLICATION_CHECKLIST.md
```

The profile normalizes/generates:

- name and description;
- instructions asset;
- conversation starters;
- declared knowledge-file references;
- declared capabilities/actions metadata;
- owner publication checklist.

The generated assets contain configuration data and references only. They do not embed raw credentials.

## Owner Publication Boundary

Phase 13 does not publish to the GPT Store or another external target automatically.

After automated readiness succeeds:

1. project lifecycle becomes `RELEASE_READY`;
2. each owner-controlled target becomes `PUBLICATION_REQUIRED`;
3. a blocking `HumanActionRequest` is opened;
4. project operational state becomes `WAITING_FOR_OWNER`;
5. a `RELEASE_READY` notification event is emitted;
6. publication occurs outside Release Manager using the owner account;
7. `confirm_publication()` verifies the HumanActionRequest and records `PUBLISHED`.

Publication delivery and owner publication completion are distinct states.

## Event Handling

Release Manager emits persisted transport-neutral events for:

- `FIRST_WORKING_REACHED`;
- `RELEASE_READY`.

When a NotificationBroker and owner email are configured, the same events can use the existing email delivery path.

## Repository Boundary

Release asset generation uses the existing Phase 6 `RepositoryAdapter` interface. Generated files are conflict-protected by the adapter and therefore do not silently overwrite different owner-authored content.

## Recovery

Release, ReleaseTarget, HumanActionRequest, notifications, lifecycle transitions, and operational transitions are durable. `ProjectRecoverySnapshot` now includes release targets in addition to releases.

## Current Limits

- external publication APIs are not invoked;
- GPT Store UI/account actions remain owner-controlled;
- readiness evidence is explicit and does not infer test success from CI providers automatically;
- release preparation writes files through a repository adapter but does not create a Git commit or tag;
- multi-target transactional preparation is best-effort across target operations rather than one database transaction;
- publication expiry/revocation policy is not implemented.
