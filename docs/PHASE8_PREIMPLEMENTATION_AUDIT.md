# PHASE8_PREIMPLEMENTATION_AUDIT

K_Supervisor ROADMAP v0.3 Phase 8 — Operational Readiness & Autonomous Lifecycle Qualification.

Date: 2026-09-16
Status: COMPLETE — implementation may begin after this audit is merged
Baseline main SHA: `097035263ded0213a1384bc10883d644e52ead45`
Validated runtime SHA: `97f454a11d1b5e5afb1334fb06d54d5abffdf004`
Phase 7 checkpoint: `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_7_COMPLETE.md`

## 1. Baseline Verification

`main` is three commits ahead and zero behind the current validated runtime baseline. The delta from `97f454…` to `097035…` is documentation-only Phase 7 state/checkpoint material. Runtime code therefore remains the validated 149-test / 85.63% baseline. Repository ruleset `main-core-validation` is active on the default branch and requires pull requests plus the GitHub Actions `Core Validation` check.

## 2. Approved Phase 8 Scope

Frozen debt assignment in `HARDENING_BASELINE_V0_3.md` is authoritative. Phase 8 owns exactly:

- owner-controlled package-index publication workflow;
- deployment/runbook/backup/restore/upgrade qualification;
- operational integration of release-readiness evidence;
- full approved ProjectSpec -> `RELEASE_READY` lifecycle qualification;
- concurrent-project qualification across restart/recovery and owner-intervention conditions.

Items explicitly deferred beyond v0.3 remain out of scope, including automatic external publication that bypasses the owner boundary, distributed clusters, remote-agent federation, mandatory event-bus infrastructure, multi-tenant SaaS isolation, non-email owner transports, and universal untrusted-Python sandboxing.

## 3. Existing Reusable Boundaries

The implementation must reuse rather than replace:

- `ProjectRegistry` lifecycle/operational transitions and `ProjectRecoverySnapshot`;
- `ReleaseManager`, `TargetPreparer`, durable `ReleaseValidationRecord`, and explicit `PublicationHandoff`;
- SQLite schema migration (`1 -> 2`) and transaction ownership;
- `ReliabilityValidator`, telemetry/health foundations, scheduler concurrency limits, Human Intervention, notification and approval state;
- Phase 7 protected-main / required-CI governance.

`RELEASE_READY` continues to mean prepared and validated, not externally published. Publication remains an owner action.

## 4. Gap Inventory

Current runtime has no supported hot backup API, verified atomic restore path, or non-destructive upgrade qualification. There is no operational runbook. Release readiness can persist validation reports, but arbitrary readiness criteria are still supplied directly by callers rather than by a standard operational evidence provider. There is no end-to-end v0.3 qualification exercising approved ProjectSpec through release readiness together with restart/recovery/owner intervention. Package-index publication has no workflow.

## 5. Implementation Decisions

### 5.1 SQLite operational safety

Add a persistence-owned operational boundary that:

- creates a SQLite online backup through the SQLite backup API;
- records/verifies schema version, SHA-256 and integrity status;
- restores only from a verified backup candidate;
- qualifies/migrates a temporary copy before replacing authoritative storage;
- uses atomic replacement after qualification and leaves the original database untouched on validation/migration failure;
- supports dry-run upgrade qualification without modifying the source database.

No new physical schema version is required solely for backup/restore qualification.

### 5.2 Operational release evidence

Add a standard evidence provider/qualifier that derives reserved operational readiness criteria from authoritative runtime state (schema/current-store integrity, recovery/referential integrity, and qualification evidence). Existing explicit criteria remain backward compatible; they are not silently guessed. Release readiness combines caller-supplied evidence with verified operational evidence.

### 5.3 Lifecycle qualification

Qualification tests will use the real registries/managers, valid lifecycle transitions, persisted release state, Human Intervention and restart/reopen recovery. Tests must prove ProjectSpec approval remains authoritative, `RELEASE_READY` does not auto-publish, and owner action remains resumable.

### 5.4 Concurrent-project qualification

At least two projects must make independent progress under scheduler limits; one project may wait for owner intervention while another progresses. After persistence reopen, both projects' lifecycle/operational/release/intervention state must reconstruct without cross-project leakage.

### 5.5 Package-index workflow

Add a manual GitHub Actions publication workflow. It must:

- be `workflow_dispatch` only;
- build and validate distributions before publication;
- publish through an explicit owner/workspace-controlled GitHub environment and OIDC/trusted-publishing path;
- never run automatically on push/tag/release;
- preserve the invariant that publication is an explicit owner action.

## 6. Required Phase 8 Verification

Phase 8 tests/evidence must cover:

- online backup, checksum/integrity verification and successful restore;
- corrupt/invalid restore rejection without damaging authoritative state;
- supported upgrade dry-run and unsupported-version failure without source mutation;
- operational release-evidence integration;
- full approved ProjectSpec -> `RELEASE_READY` path with owner publication still pending;
- restart/recovery of release and intervention state;
- concurrent-project progress/isolation with owner-wait conditions;
- package-publication workflow is manual-only and owner/environment gated;
- operations runbook documents backup, restore, upgrade, rollback, deployment checks and publication;
- full cumulative v0.2 + v0.3 regression suite and protected `Core Validation` PASS.

## 7. Exit Rule

Phase 8 may be marked COMPLETE only when the approved scope is implemented, phase-specific tests and full regression suite pass, the committed implementation passes protected `Core Validation`, operational/runbook evidence is synchronized, and a Phase 8 completion checkpoint is merged.
