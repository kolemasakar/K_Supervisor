# PROJECT_STATE
Канонічний поточний знімок K_Supervisor після завершення ROADMAP v0.3 Phase 7.

Version: 2.9
Status: ACTIVE
Date: 2026-09-16

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Package: k-supervisor==0.1.0
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0-6: COMPLETE
v0.3 Phase 7: COMPLETE
v0.3 Phase 8: PLANNED / NOT ACTIVATED
Phase 17: NOT DEFINED
```

## Current Validated Runtime Baseline

```text
Implementation SHA: 97f454a11d1b5e5afb1334fb06d54d5abffdf004
Core Validation run: 35124348659
Python: 3.13.15
pytest: 149 passed
branch-aware coverage: 85.63%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

This baseline includes the validated Phase 7 runtime implementation plus the additive OpenAI Custom GPT -> Plugin compatibility correction.

## Phase 7 State

Phase 7 pre-implementation audit is complete and the extension-governance runtime is implemented and validated.

Validated Phase 7 implementation evidence before the later compatibility patch:

```text
Implementation SHA: 64c84ad6e6633c047416aca270d979e4ba5d36a0
Core Validation run: 35121930140
Core Validation: PASS
```

Delivered Phase 7 runtime/CI work includes:

- fail-closed installed-extension activation before `EntryPoint.load()`;
- exact extension identity/provenance/version/compatibility binding;
- durable enabled/trusted/signature-verification governance state;
- trust invalidation on identity-bearing metadata change;
- PR-triggered authoritative `Core Validation` and current GitHub Actions runtime lines.

Phase 7 repository governance is now complete: active repository ruleset `main-core-validation` (ruleset id `23556478`) targets the default branch, requires pull requests and the GitHub Actions check `Core Validation`, blocks deletion and non-fast-forward pushes, has no bypass actors, and does not require branches to be up to date before merge.

## OpenAI Platform Compatibility Correction

OpenAI's announced Custom GPT retirement requires ChatGPT-facing release preparation to be Plugin-first.

K_Supervisor now uses:

```text
Preferred ChatGPT release target: CHATGPT_PLUGIN
Legacy migration compatibility: GPT_STORE
Custom Action auto-migration: NO
Selected ChatGPT model pinning: NO
External availability/publication: owner/workspace-admin controlled
```

`CHATGPT_PLUGIN` generates portable skill, reference/integration inventory, regression prompts and access/migration evidence. `GPT_STORE` remains supported so historical/persisted release state stays resumable.

Authoritative impact record: `OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md`.

## Persistence

SQLite physical schema remains version `2`. Neither Phase 7 nor the Plugin compatibility correction activates Phase 8 migration/backup/restore qualification.

## Current Roadmap Boundary

```text
Phase 7: COMPLETE
Completion checkpoint: PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_7_COMPLETE.md
Phase 8: PLANNED / NOT ACTIVATED
```

The existing Phase 7 handoff remains historical start context. `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_7_COMPLETE.md`, this document, `ROADMAP.md` and `TEST_MATRIX.md` are authoritative for Phase 7 closure. Phase 8 is not activated.

## Public Compatibility Baseline

```text
Python facade: ksupervisor
Service facade: ksupervisor.service
Service API: /api/v1
CLI: k-supervisor
Config version: 1
Preferred ChatGPT release target: CHATGPT_PLUGIN
Legacy ChatGPT migration target: GPT_STORE
Extension groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

## Validation Rule

Completed v0.2 plus completed v0.3 phase tests remain cumulative. Runtime changes require successful Core Validation on the committed implementation SHA. Phase completion additionally requires all phase-specific non-code governance exit criteria.
