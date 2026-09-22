# V0_4_PHASE5_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 5 — Plugin-Native ChatGPT/Codex Release Packaging.

Version: 1.0
Status: COMPLETE — ACTIVATION PENDING
Date: 2026-09-22
Baseline main: c9337ea8d22849a5e8895e7cb5b86e0c9f012112
Baseline tree: 5b50cd52d00c17c0d67c481d3d46ffc5df07e92d
Validated runtime predecessor main: 8ba51416c561e841ae7a43c5941426b681299e80
Validated runtime predecessor phase: v0.4 Phase 4 COMPLETE
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 5 is limited to the ROADMAP v0.4 assignment for current Plugin-native ChatGPT/Codex release packaging.

Authorized implementation scope after a separate protected owner activation checkpoint:

- evolve the existing `CHATGPT_PLUGIN` release profile from portable migration evidence into a valid current plugin package;
- generate a versioned portable Agent Plugins manifest and current OpenAI-specific metadata;
- generate one or more valid skill directories with `SKILL.md` metadata/instructions and declared supporting resources;
- package existing app references using current supported app mapping format when configured;
- preserve required/optional app intent and app-template inventory without inventing workspace apps;
- generate a deterministic GitHub-importable plugin marketplace catalog when requested by ProjectSpec;
- retain migration inventory for Custom GPT instructions, reference files, connected apps and legacy Custom Actions;
- validate package paths, manifests, skill metadata, app references, marketplace references and regression-evidence completeness before `RELEASE_READY`;
- preserve legacy persisted `GPT_STORE` compatibility without making it the preferred target;
- preserve explicit owner/workspace control over plugin installation, sharing, availability and public submission.

Explicitly outside Phase 5:

- automatically migrating or mutating an existing Custom GPT;
- automatically creating or registering ChatGPT apps, MCP servers or provider credentials;
- automatically importing a marketplace into a workspace;
- automatically installing, sharing, publishing or publicly submitting a plugin;
- automatically granting app access, workspace permissions or provider authorization;
- automatically converting legacy Custom Actions into apps/MCP tools;
- automatically selecting or pinning a ChatGPT model;
- Phase 6 telemetry/SBOM/provenance work;
- Phase 7 end-to-end product qualification;
- any paid-only development-validation dependency.

`DEVELOPMENT_RESOURCE_POLICY.md` remains authoritative.

## 2. Frozen Predecessor and Ancestry

Phase 4 completion is the current runtime predecessor.

```text
Phase 4 qualification main: 8ba51416c561e841ae7a43c5941426b681299e80
Phase 4 merged-main Core Validation: 35755228146 — PASS
Full regression: 279 passed
Branch-aware coverage: 81.54%
Installed-wheel Phase 4 repository Service/API/CLI smoke: PASS
```

Current `main` is:

```text
main: c9337ea8d22849a5e8895e7cb5b86e0c9f012112
tree: 5b50cd52d00c17c0d67c481d3d46ffc5df07e92d
```

The compare from the Phase 4 qualification main to current `main` is ahead-only by 10 commits and changes only `docs/*`. No runtime/source/test path changed after the validated Phase 4 qualification baseline.

Therefore `8ba51416...` remains the runtime predecessor for Phase 5.

## 3. Existing Release Compatibility Floor

The existing Release Manager already provides durable target-level release orchestration and the owner-publication boundary.

Current stable semantics:

- `CHATGPT_PLUGIN` is the preferred ChatGPT-facing target;
- `GPT_STORE` remains a legacy compatibility target;
- `ReleaseTarget` tracks target status, generated artifact paths, checklist and Human Intervention correlation;
- target preparation writes release assets through the configured `RepositoryAdapter`;
- generated files remain conflict-protected;
- `RELEASE_READY` transitions to `PUBLICATION_REQUIRED` where owner action is required;
- external publication/availability is confirmed back through the existing Release Manager instead of being performed automatically.

These semantics remain compatibility requirements.

## 4. Existing CHATGPT_PLUGIN Profile

`release_manager/chatgpt_plugin.py` currently generates portable migration evidence:

```text
release/chatgpt_plugin/PLUGIN_PROFILE.json
release/chatgpt_plugin/SKILL.md
release/chatgpt_plugin/INTEGRATIONS.md
release/chatgpt_plugin/REGRESSION_PROMPTS.md
release/chatgpt_plugin/ACCESS_AND_MIGRATION_CHECKLIST.md
```

The current profile already preserves important migration facts:

- reference-file inventory;
- required/optional app inventory;
- app-template inventory;
- legacy Custom Action dependency inventory;
- custom MCP integration inventory;
- regression prompts;
- `custom_actions_auto_migrated=false`;
- `selected_model_pinned=false`;
- access/sharing review required.

This evidence remains useful and should be retained or migrated into the new package, not discarded.

## 5. Current OpenAI Plugin Compatibility Snapshot

Official OpenAI plugin documentation was inspected on 2026-09-22.

Authoritative current references inspected:

- `https://developers.openai.com/plugins/build/plugins`
- `https://developers.openai.com/plugins/build/skills`
- `https://developers.openai.com/plugins/deploy/connect-chatgpt`
- `https://developers.openai.com/plugins/deploy/submission`
- `https://learn.chatgpt.com/docs/enterprise/plugin-management`
- OpenAI Help Center guidance for Plugins in ChatGPT/Codex and Custom GPT retirement/migration.

Current facts relevant to Phase 5:

### 5.1 Portable Agent Plugins package

OpenAI currently recommends the portable Agent Plugins package for new packages:

```text
plugin root/
  plugin.json
  skills/
  mcp.json                  optional
  .codex-plugin/plugin.json optional compatibility fallback
  hooks/                    optional
  assets/                   optional
```

The portable root manifest uses the Agent Plugins 1.0 schema:

```text
https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
```

OpenAI-specific presentation/app/hook settings belong under `extensions.com.openai` in the root `plugin.json`.

Existing `.codex-plugin/plugin.json` remains supported as a compatibility fallback. If root `extensions.com.openai` is present, it is the authoritative OpenAI-specific overlay rather than being merged with the compatibility manifest.

### 5.2 Skills

Each packaged skill lives in its own directory and requires:

```text
skills/<skill-name>/SKILL.md
```

The `SKILL.md` begins with YAML metadata containing at least `name` and `description`, followed by workflow instructions.

Supporting skill material belongs next to the skill:

```text
references/
assets/
scripts/
```

The skill description is used for triggering/selection, while detailed procedure, boundaries and output requirements belong in the body.

### 5.3 Existing app references

An existing registered app can be referenced through root `.app.json`.

Current documented app IDs may begin with:

```text
asdk_app_
connector_
templated_apps_
```

A plugin reference does not create the app and does not grant workspace/provider permissions.

For OpenAI-specific native packaging, the manifest points its apps field at:

```text
./.app.json
```

### 5.4 GitHub marketplace import

Workspace plugin import/sync currently supports GitHub marketplaces with:

```text
.agents/plugins/marketplace.json
```

A Codex marketplace contains `plugins[]` entries and may reference plugin folders in the same repository or supported GitHub sources.

A marketplace entry may also carry `pluginId` to move an existing workspace plugin to GitHub management. That ID belongs in the marketplace entry, not in the plugin manifest.

GitHub import/sync does not itself apply workspace installation/authentication policy or grant app access.

### 5.5 MCP packaging and web/desktop compatibility

Current workspace documentation states that an imported plugin declaring MCP servers through `mcp.json`, `.mcp.json` or equivalent inline server declarations is marked Desktop only.

Therefore Phase 5 must not blindly turn every Custom Action/custom MCP inventory item into bundled MCP configuration. For web-compatible packages, existing registered apps should be referenced through the supported app mapping surface when possible.

### 5.6 Custom GPT migration semantics

Current OpenAI migration guidance states:

- GPT instructions become a plugin skill;
- knowledge/reference files move into plugin reference material;
- connected apps are represented as plugin apps;
- selected GPT model does not transfer;
- Custom Actions do not transfer automatically;
- migration does not automatically preserve sharing/access;
- migrated personal plugins begin private;
- original GPT conversations do not transfer.

These facts align with the existing K_Supervisor compatibility decision and remain mandatory invariants.

### 5.7 Public submission remains separate

Current OpenAI public submission flow is explicitly separate from local/workspace package preparation.

Public review may require listing metadata, verified publisher identity, policy URLs, final skills, and at least five positive plus three negative test cases. A remote MCP submission additionally requires a production public MCP URL and reviewable authentication/test setup.

Phase 5 prepares deterministic package/evidence only. It does not submit or publish externally.

## 6. Current Gaps

### 6.1 No native plugin package

The current profile does not generate root `plugin.json`, a plugin directory structure, a portable Agent Plugins schema declaration or OpenAI-specific extension metadata.

### 6.2 Current SKILL.md is evidence, not a valid packaged skill

The current file is:

```text
release/chatgpt_plugin/SKILL.md
```

It does not live under `skills/<name>/SKILL.md` and does not begin with current required skill metadata.

### 6.3 Reference files are inventory-only

`reference_files` / `knowledge_files` are currently listed but not packaged into a skill `references/` directory.

The current `RepositoryAdapter` compatibility contract provides `prepare/apply_files/list_files` but no general text-content read operation. Phase 5 therefore needs an explicit additive source-resource resolution strategy rather than silently claiming reference assets were packaged.

### 6.4 App inventory is not an app mapping

Required/optional apps are currently arbitrary inventory values. There is no validated app ID, local app alias, required flag mapping or `.app.json` artifact.

Phase 5 must distinguish:

```text
human-readable dependency name
registered app ID
required vs optional
app template inventory
unresolved dependency
```

An unresolved dependency must remain a migration/setup blocker or owner checklist item; it must not be fabricated into a valid app mapping.

### 6.5 MCP inventory is not executable packaging

`mcp_integrations` is inventory only. No package-level distinction currently exists between:

- existing registered app backed by MCP;
- bundled portable MCP server;
- legacy Custom Action requiring rebuild;
- app template requiring workspace admin setup.

Phase 5 must preserve these distinctions.

### 6.6 No marketplace catalog

There is no `.agents/plugins/marketplace.json` generation and no deterministic linkage between a generated marketplace entry and the generated plugin folder.

### 6.7 Validator only checks file existence

`ChatGPTPluginPreparationProfile.validate()` currently verifies only that five evidence paths exist.

It does not validate:

- JSON syntax/schema;
- portable plugin identity/version;
- path containment;
- required OpenAI interface metadata;
- skill YAML metadata;
- unique skill/app names;
- app ID formats;
- marketplace source paths;
- package-to-marketplace name consistency;
- duplicate/unsafe references;
- unsupported Custom Action auto-migration claims;
- selected-model pinning;
- regression-evidence minimums.

### 6.8 No pinned compatibility/schema snapshot

The current profile has its own `schema_version=1.0`, but this is not tied to the upstream Agent Plugins schema or an explicit OpenAI compatibility profile.

Normal CI must not fetch a mutable network schema. Phase 5 needs local deterministic schema/validation data pinned to an audited compatibility snapshot.

### 6.9 No deterministic plugin package version contract

The release version is durable, but the generated plugin package currently has no native manifest version.

Phase 5 must derive/validate plugin package version deterministically from release configuration/version without inventing a separate untracked version stream.

### 6.10 No native migration manifest

The current `PLUGIN_PROFILE.json` is useful but not a complete structured migration map from legacy GPT semantics to native plugin artifacts.

Phase 5 should preserve explicit source-to-target mapping and unresolved dependencies so migration readiness is auditable.

## 7. Target Package Architecture

Preferred Phase 5 release output is a self-contained package root under the existing release directory.

Recommended deterministic layout:

```text
release/chatgpt_plugin/
  PLUGIN_PROFILE.json
  MIGRATION_INVENTORY.json
  REGRESSION_CASES.json
  ACCESS_AND_MIGRATION_CHECKLIST.md

  package/
    plugin.json
    .app.json                         only when registered app references exist
    skills/
      <skill-slug>/
        SKILL.md
        references/
          ...                         only validated copied/generated resources
        assets/                       optional
        scripts/                      optional only when explicitly declared

  marketplace/
    .agents/
      plugins/
        marketplace.json
    plugins/
      <plugin-slug>/                  deterministic mirror/package tree
        ...
```

Implementation may avoid duplicating the full plugin tree physically by choosing one canonical package location and making the marketplace source path reference it, provided the resulting marketplace path is valid for GitHub import and all path traversal checks pass.

The package must not include `mcp.json` unless the ProjectSpec explicitly requests a bundled MCP package and accepts the resulting surface constraints.

## 8. Native Manifest Contract

For the audited compatibility profile, the generated root `plugin.json` must:

- declare the pinned portable Agent Plugins schema;
- contain deterministic `name`, `version`, and `description`;
- contain safe publisher/project metadata when explicitly configured;
- use only relative package paths;
- keep OpenAI-specific settings under `extensions.com.openai`;
- point app references to `./.app.json` only when that file is generated;
- declare interface metadata required by the selected compatibility profile;
- never contain raw credentials;
- never contain a selected ChatGPT model;
- never claim public approval/publication.

A separate `.codex-plugin/plugin.json` compatibility fallback is optional. If generated, its relationship to root `extensions.com.openai` must be explicit and tests must prevent conflicting duplicated configuration.

Preferred implementation: root portable manifest is canonical; compatibility overlay is generated only when ProjectSpec explicitly requests it or current target compatibility requires it.

## 9. Skill Contract

Each generated skill must have:

- a safe deterministic slug;
- YAML metadata with `name` and `description`;
- a description that clearly identifies the trigger/use case;
- workflow body covering expected input, steps, output, boundaries, stop/clarification behavior and supporting resources;
- no hidden model pinning;
- no assumption that an unavailable app/MCP tool is present.

For the default single-skill migration path, the existing ProjectSpec purpose/problem/success criteria and portable skill source are used to build one canonical skill.

Phase 5 may support multiple explicitly declared skills additively, but it must not split one ProjectSpec into guessed skills without owner configuration.

## 10. Reference Resource Contract

Reference resources must be real package resources, not only names in a profile.

Implementation must choose one explicit source model:

1. copy validated text/reference files from the managed repository through an additive repository read contract; or
2. generate references from explicitly supplied ProjectSpec release assets.

Preferred approach is an additive repository text-read contract that is supported by both filesystem and governed GitHub repository adapters, because release preparation already operates against the authoritative managed repository.

Required safety:

- source path must be relative and normalized;
- no `..`, absolute path, symlink escape or hidden credential file inclusion;
- destination remains inside the skill resource tree;
- generated/copied content remains conflict-protected;
- missing declared required reference blocks plugin readiness;
- optional reference absence is recorded but does not become a fabricated asset.

## 11. App Mapping Contract

Phase 5 introduces an explicit structured app reference model in ProjectSpec release configuration.

Recommended semantic fields:

```text
alias
app_id
required
kind                 optional: app / connector / template
display_name         optional metadata only
```

Validation rules:

- `app_id` must use a currently supported audited prefix;
- aliases are unique and path-safe;
- required/optional semantics are explicit;
- unresolved human-readable app names stay in migration inventory only;
- app template declarations do not become registered app IDs until a workspace admin creates/publishes the app;
- no plugin/app ID is guessed.

The generated `.app.json` must contain only supported registered app references.

## 12. Marketplace Contract

When `github_marketplace.enabled=true` (or equivalent additive configuration), Phase 5 generates a deterministic Codex marketplace:

```text
.agents/plugins/marketplace.json
```

The catalog must:

- have a stable marketplace name;
- contain the generated plugin exactly once;
- use a safe source path;
- optionally include a configured existing `pluginId` for GitHub-management takeover;
- never put `pluginId` inside `plugin.json`;
- keep workspace installation/authentication policy as informational evidence only, because imported repository policy values are not authoritative workspace settings.

Marketplace generation does not import or sync the workspace.

## 13. Custom GPT Migration Inventory

The machine-readable migration inventory must distinguish at minimum:

```text
instructions                 -> generated skill
knowledge/reference files    -> skill references
connected registered apps    -> .app.json
app templates                -> workspace-admin setup required
legacy Custom Actions        -> unresolved / rebuild required
custom MCP integrations      -> explicit mapping mode required
selected GPT model           -> NOT TRANSFERRED / NOT PINNED
sharing/access               -> NOT TRANSFERRED / OWNER REVIEW REQUIRED
conversation history         -> NOT TRANSFERRED
```

Custom Action dependency presence must never be interpreted as migrated capability.

## 14. Regression Evidence Contract

Current free-form `REGRESSION_PROMPTS.md` remains useful but Phase 5 needs structured deterministic evidence.

The package should generate `REGRESSION_CASES.json` or equivalent with:

- stable case IDs;
- prompt;
- positive/negative type;
- expected skill/workflow behavior;
- expected result shape;
- required app/tool/resource dependencies;
- expected clarification/refusal/fallback for negative cases.

For a package intended to be public-submission ready, validation should require at least:

```text
positive cases >= 5
negative cases >= 3
```

For a private/local/workspace package, this public-submission minimum may be advisory unless the ProjectSpec explicitly requests public-submission readiness.

No live ChatGPT execution is required in protected CI. Local/private plugin testing remains separate evidence.

## 15. Publication and Availability Boundary

Phase 5 must preserve the existing Release Manager owner handoff.

```text
package valid
  -> target READY
  -> PUBLICATION_REQUIRED
  -> owner/workspace action
  -> explicit confirmation
  -> PUBLISHED
```

For `CHATGPT_PLUGIN`, `PUBLISHED` remains a K_Supervisor owner-confirmed availability state. It does not automatically mean universal public Plugins Directory listing.

External operations that remain owner/workspace controlled include:

- importing a GitHub marketplace;
- installing the plugin;
- enabling apps;
- connecting provider accounts;
- setting action approvals;
- sharing with users/groups;
- publishing to workspace directory;
- submitting for OpenAI public review;
- publishing publicly after review.

## 16. Backward Compatibility

`GPT_STORE` remains readable and resumable for legacy persisted releases.

Phase 5 must not:

- rewrite an existing persisted `GPT_STORE` target into `CHATGPT_PLUGIN`;
- silently change historical artifact paths;
- break current `ChatGPTPluginPreparationProfile` callers;
- remove existing migration evidence without an explicit deterministic replacement/mapping;
- require a schema migration unless durable state actually changes.

Preferred path: additive package artifacts and richer validation while preserving existing evidence files where useful.

## 17. Failure Semantics

New package validation failures should be safe, deterministic and operator-readable.

Minimum categories:

```text
PLUGIN_CONFIG_INVALID
PLUGIN_NAME_INVALID
PLUGIN_VERSION_INVALID
PLUGIN_SCHEMA_INVALID
PLUGIN_SKILL_INVALID
PLUGIN_REFERENCE_MISSING
PLUGIN_REFERENCE_UNSAFE
PLUGIN_APP_REFERENCE_INVALID
PLUGIN_MARKETPLACE_INVALID
PLUGIN_MIGRATION_UNRESOLVED
PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT
PLUGIN_PACKAGE_CONFLICT
```

No failure message may expose secret values or assume account/workspace access.

## 18. Deterministic Validation Strategy

Protected CI remains network-free for package validation.

Implementation should vendor or encode the audited schema constraints locally and validate generated fixtures without calling:

- ChatGPT;
- OpenAI plugin submission portal;
- a workspace marketplace;
- external MCP servers;
- provider OAuth endpoints.

A local/plugin-creator/private marketplace test can supplement Phase 5 evidence when available at no project-attributable cost, but it is not an ordinary merge gate.

## 19. Required Implementation Sequence

After a separate owner-approved Phase 5 activation checkpoint merges, implementation should proceed in this order:

1. additive native plugin package contracts and safe slug/version/path utilities;
2. local pinned manifest/app/marketplace validators;
3. valid skill directory generation and migration inventory;
4. explicit registered-app mapping generation;
5. reference-resource packaging with additive repository read support;
6. optional GitHub marketplace catalog generation;
7. structured regression-case generation/validation;
8. Release Manager target integration preserving current owner-publication state machine;
9. backward-compatibility tests for existing `CHATGPT_PLUGIN` evidence and legacy `GPT_STORE`;
10. installed-wheel/package-generation qualification and documentation update.

Runtime/service/provider work outside this sequence is not authorized by the audit.

## 20. Audited Verification Contract

After activation, deterministic Phase 5 verification must prove:

- root portable `plugin.json` is generated with the pinned Agent Plugins schema;
- OpenAI-specific metadata is deterministic and package-relative;
- package name/version/path validation rejects unsafe or ambiguous inputs;
- generated `skills/<slug>/SKILL.md` contains valid name/description metadata and instructions;
- required reference resources are actually packaged or readiness fails;
- path traversal and credential-file reference attempts fail closed;
- `.app.json` contains only validated registered app IDs and unique aliases;
- required/optional app intent is preserved;
- app-template inventory remains distinct from registered app references;
- Custom Action dependencies remain unresolved/rebuild-required unless an explicit replacement mapping is supplied;
- selected GPT model is not carried into the package;
- sharing/access state is not claimed to transfer;
- optional compatibility manifest cannot conflict with canonical root OpenAI extension settings;
- generated marketplace resolves exactly to the generated plugin;
- optional existing `pluginId` appears only in marketplace metadata;
- no bundled MCP configuration is generated implicitly;
- web/desktop compatibility implications are recorded when bundled MCP configuration is explicitly requested;
- structured regression cases validate deterministic syntax/content;
- public-submission readiness enforces at least five positive and three negative cases when requested;
- schema validation is local/network-free;
- `GPT_STORE` predecessor behavior remains compatible;
- Release Manager stops at owner publication/availability handoff;
- no external plugin installation/share/publication call occurs in protected CI;
- cumulative regression, branch-aware coverage >=80%, packaging, installed-wheel and protected `Core Validation` remain green.

## 21. Protected Governance Evidence

```text
Audit PR: #42
Initial audit head: 69bfd4be2e27c03915ec6bf366422b38b53e0410
Initial Core Validation: 35758209430 — PASS
Validation runner: kgm-e4-owner-pilot
Runtime/source/test paths changed: NONE
```

The exact final audit head, including this recorded evidence, must pass required `Core Validation` before merge. The merged audit remains documentation-only and does not activate Phase 5.

## 22. Audit Outcome

```text
PHASE_5_PREIMPLEMENTATION_AUDIT=COMPLETE
PHASE_5_ACTIVATION=NO
PHASE_5_RUNTIME_IMPLEMENTATION_AUTHORIZATION=NO
CURRENT_RUNTIME_PREDECESSOR=8ba51416c561e841ae7a43c5941426b681299e80
CURRENT_AUDIT_BASELINE=c9337ea8d22849a5e8895e7cb5b86e0c9f012112
ZERO_COST_DEVELOPMENT=REQUIRED
PUBLICATION_AUTOMATION=FORBIDDEN
GPT_STORE_COMPATIBILITY=RETAINED
NEXT_GATE=OWNER_PHASE_5_ACTIVATION_DECISION
```

This audit does not activate Phase 5. Runtime/source/test implementation may begin only after explicit owner approval, a separate Phase 5 activation checkpoint, protected `Core Validation` PASS, and merge to `main`.
