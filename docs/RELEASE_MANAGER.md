# RELEASE_MANAGER
Керування підготовкою релізів, перевіркою готовності та передачею публікації власнику.

Version: 1.1
Status: ACTIVE
Phase: 13 baseline + v0.3 Phase 8 operational qualification

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

Phase 5 preserves the portable migration evidence and adds deterministic native package artifacts.

Always-generated release evidence:

```text
release/chatgpt_plugin/PLUGIN_PROFILE.json
release/chatgpt_plugin/SKILL.md
release/chatgpt_plugin/INTEGRATIONS.md
release/chatgpt_plugin/REGRESSION_PROMPTS.md
release/chatgpt_plugin/ACCESS_AND_MIGRATION_CHECKLIST.md
release/chatgpt_plugin/MIGRATION_INVENTORY.json
release/chatgpt_plugin/REGRESSION_CASES.json
release/chatgpt_plugin/package/plugin.json
release/chatgpt_plugin/package/skills/<slug>/SKILL.md
```

Conditional native artifacts:

```text
release/chatgpt_plugin/package/.app.json
release/chatgpt_plugin/package/skills/<slug>/references/...
release/chatgpt_plugin/marketplace/.agents/plugins/marketplace.json
release/chatgpt_plugin/marketplace/plugins/<slug>/...
```

`.app.json` is emitted only for explicitly configured validated registered app IDs. Marketplace export is emitted only when requested. Declared package references are copied through the repository read boundary after safe path/credential-like path validation; a missing required reference blocks readiness.

The machine-readable migration inventory keeps Custom Actions as `REBUILD_REQUIRED`, custom MCP inventory as `EXPLICIT_MAPPING_REQUIRED`, model pinning disabled, and prior sharing/access and conversation-history transfer disabled.

The structured regression evidence supports explicit positive/negative cases. When public-submission readiness is requested, the local validator requires at least five positive and three negative cases.

No bundled MCP configuration is generated implicitly. Plugin installation, app authorization, workspace import/sync, sharing and public submission remain external owner/workspace-admin actions.

`GPT_STORE` remains a supported legacy profile so persisted releases and active Custom GPT migration work stay resumable. New ChatGPT-oriented projects should prefer `CHATGPT_PLUGIN`.

Generated package artifacts contain configuration/reference content only and do not embed raw credentials.

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

Release asset generation uses the current `RepositoryAdapter` boundary. Phase 5 adds a read-only `read_text_file()` operation for declared reference packaging; the governed GitHub implementation keeps that read behind the existing policy/provider/access-reference path. Generated files remain conflict-protected and therefore do not silently overwrite different owner-authored content.

## Recovery

Release, ReleaseTarget, HumanActionRequest, notifications, lifecycle transitions, and operational transitions are durable. `ProjectRecoverySnapshot` now includes release targets in addition to releases.

## Current Limits

- external publication APIs are not invoked;
- plugin/GPT directory, sharing, installation and account/workspace actions remain owner- or administrator-controlled;
- arbitrary/project-specific readiness evidence remains explicit; only reserved Phase 8 operational criteria are derived from authoritative platform state;
- release preparation writes files through a repository adapter but does not create a Git commit or tag;
- multi-target transactional preparation is best-effort across target operations rather than one database transaction;
- publication expiry/revocation policy is not implemented.

## Phase 8 Operational Readiness Evidence

`OperationalReleaseEvidenceProvider` supplies only reserved criteria backed by authoritative runtime state:

```text
operational:schema-current
operational:store-integrity
operational:recovery-integrity
```

These criteria are combined with caller-supplied evidence before the existing `GenericReleaseReadinessChecker` runs. Project-specific, owner-specific or external criteria are never guessed. This preserves predecessor behavior while allowing ProjectSpec release gates to depend on verified persistence/recovery state.

Phase 8 end-to-end qualification proves an approved ProjectSpec can traverse the existing lifecycle to `FIRST_WORKING`, enter release preparation, reach `RELEASE_READY`, persist release-validation evidence, then stop at the existing blocking publication Human Intervention. Restart/reopen reconstructs that owner-gated state.

## Package-Index Publication Workflow

`.github/workflows/package-publish.yml` is an owner-controlled manual workflow only. It has no automatic push/tag/release/schedule trigger, requires explicit `confirm_owner_publication`, builds and validates distributions separately, and publishes from the protected `pypi` GitHub environment through OIDC Trusted Publishing. External publication still requires owner/workspace configuration and is never performed by normal Release Manager execution.
