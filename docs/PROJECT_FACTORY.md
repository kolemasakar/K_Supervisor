# PROJECT_FACTORY
Опис автоматизованого створення та bootstrap керованих проєктів із затвердженого ProjectSpec.

Version: 1.0
Status: ACTIVE
Phase: 6

## 1. Purpose

Project Factory turns an approved `ProjectSpec` into a managed project repository baseline.

Core flow:

```text
structured onboarding
-> DRAFT ProjectSpec
-> owner approval
-> APPROVED ProjectSpec
-> Project Factory
-> repository prepare/connect
-> template generation
-> bootstrap validation
-> BOOTSTRAPPED
```

The factory does not interpret an unstructured chat directly. Onboarding must first be converted into structured fields and a versioned ProjectSpec.

## 2. Scope

Phase 6 implements:

- structured onboarding-to-ProjectSpec handoff;
- repository adapter contract;
- working local filesystem Git repository adapter;
- reusable bootstrap templates;
- generated README, VISION, ARCHITECTURE, ROADMAP, and CI scaffold;
- initial `src/`, `tests/`, `agents/`, and `workflows/` structure;
- bootstrap validation;
- Project Registry lifecycle updates;
- explicit human intervention for unavailable external repository provisioning;
- conflict protection for existing owner-authored files.

## 3. Approval Boundary

Only an `APPROVED` ProjectSpec may authorize automated bootstrap.

A draft produced from onboarding never authorizes repository provisioning or file generation by itself.

## 4. Repository Adapter Boundary

Project Factory depends on a stable `RepositoryAdapter` interface rather than GitHub-specific APIs.

The adapter is responsible for:

```text
prepare repository
apply generated files
list repository files
```

The Phase 6 working adapter is `FilesystemRepositoryAdapter`.

External repository/service provisioning, including a production GitHub provisioning adapter, is deferred to Phase 10.

## 5. Repository Provisioning Modes

Repository intent is represented as one of these modes:

```text
AUTOMATABLE
OWNER_ACTION_REQUIRED
UNKNOWN
```

`AUTOMATABLE` may proceed only when a matching adapter is available.

`OWNER_ACTION_REQUIRED` means the owner must create or authorize the external resource. Project Factory creates a structured `HumanActionRequest` instead of silently waiting.

`UNKNOWN` must not be treated as authorization for autonomous provisioning.

## 6. Generated Baseline

The default bootstrap template produces at least:

```text
README.md
docs/VISION.md
docs/ARCHITECTURE.md
docs/ROADMAP.md
.github/workflows/validation.yml
src/.gitkeep
tests/.gitkeep
agents/.gitkeep
workflows/.gitkeep
```

Templates are reusable and ProjectSpec-driven. They are not hard-coded for one domain.

## 7. Conflict Safety

Generated bootstrap is idempotent for identical content.

If a target file already exists with different content, Project Factory raises a repository conflict instead of overwriting the file silently.

This protects owner-authored or pre-existing repository content.

## 8. Recovery Semantics

Project lifecycle moves to `PROVISIONING` before repository bootstrap side effects begin.

The project moves to `BOOTSTRAPPED` only after generated content passes bootstrap validation.

If execution stops during provisioning, a later run may resume from `PROVISIONING`. The repository adapter and conflict checks prevent blind duplicate writes.

## 9. Validation

Bootstrap validation checks required generated files and repository structure before the lifecycle transition to `BOOTSTRAPPED`.

Phase 6 tests cover:

- onboarding creates a DRAFT ProjectSpec;
- approved ProjectSpec produces a valid managed Git repository;
- generated minimum documentation and structure exist;
- explicit owner intervention is created for an unavailable external repository provider;
- conflicting pre-existing content is rejected rather than overwritten.

## 10. Deferred Work

The following remain outside Phase 6:

- production GitHub repository creation API;
- cloud/service provisioning;
- secret backends;
- full environment provisioning;
- workflow execution;
- agent runtime execution;
- policy enforcement for external side effects.

These belong to later roadmap phases.
