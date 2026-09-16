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

`ReleaseTarget` tracks one target such as `CHATGPT_PLUGIN`, legacy `GPT_STORE`, or another deployment destination independently and stores:

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

## ChatGPT Plugin Profile

The preferred ChatGPT-facing target is `CHATGPT_PLUGIN`.

Automatically generated portable evidence:

```text
release/chatgpt_plugin/PLUGIN_PROFILE.json
release/chatgpt_plugin/SKILL.md
release/chatgpt_plugin/INTEGRATIONS.md
release/chatgpt_plugin/REGRESSION_PROMPTS.md
release/chatgpt_plugin/ACCESS_AND_MIGRATION_CHECKLIST.md
```

The profile records reusable skill guidance, reference assets, required/optional apps, app templates, Custom Action dependencies requiring rebuild, custom MCP integrations, regression prompts, and access/sharing review requirements. It does not pin a selected ChatGPT model or claim that Custom Actions migrated automatically.

`GPT_STORE` remains a supported legacy profile so persisted releases and active Custom GPT migration work stay resumable. New ChatGPT-oriented projects should prefer `CHATGPT_PLUGIN`.

Generated assets contain configuration data and references only. They do not embed raw credentials.

## Owner Publication Boundary

Release Manager does not publish to the Plugin Directory, GPT Store, or another external target automatically.

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
- plugin/GPT directory, sharing, installation and account/workspace actions remain owner- or administrator-controlled;
- readiness evidence is explicit and does not infer test success from CI providers automatically;
- release preparation writes files through a repository adapter but does not create a Git commit or tag;
- multi-target transactional preparation is best-effort across target operations rather than one database transaction;
- publication expiry/revocation policy is not implemented.
