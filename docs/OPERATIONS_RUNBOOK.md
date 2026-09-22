# OPERATIONS_RUNBOOK

K_Supervisor single-node operational-readiness runbook.

Version: 1.1
Status: ACTIVE
Date: 2026-09-19

## Scope and invariants

This runbook covers the supported PRE-ALPHA single-node operational boundary: production Service/API hosting, operator CLI-over-HTTP, package deployment qualification, SQLite backup/restore/upgrade qualification, rollback, Project recovery and owner-controlled package-index publication. TLS termination/certificate lifecycle remains operator-owned. Distributed clusters, remote-agent federation and automatic external publication remain unsupported.

`RELEASE_READY` means prepared and validated. It does not mean published. External publication always remains an explicit owner/workspace action.

## Pre-deployment qualification

Before deployment or package promotion:

1. Use a commit that passed protected `Core Validation` on a pull request to `main`.
2. Use Python 3.13 and install the built wheel outside the source checkout.
3. Run `DeploymentQualifier` with required service probes and the Projects whose recovery/integrity must be qualified.
4. Require current SQLite schema and `PRAGMA integrity_check` success.
5. Create and verify an online backup before replacing an existing deployment or applying an upgrade.
6. Confirm release targets remain owner-controlled and no unresolved blocking state is being bypassed.

A failed required deployment check blocks promotion. Project lifecycle state is not used as a substitute for service health/readiness.

## Single-node Service/API host

The supported Phase 3 topology is:

```text
operator CLI / HTTP client
  -> HTTPS reverse proxy for non-loopback production exposure
  -> trusted local/private HTTP hop
  -> k-supervisor serve
  -> one ServiceRuntime / one authoritative SQLite store
```

Safe defaults and requirements:

- loopback binding is the default;
- non-loopback binding requires `proxy_mode=true` plus explicit trusted proxy addresses/CIDRs;
- in proxy mode, requests from untrusted proxy peers fail closed and trusted peers must forward `X-Forwarded-Proto: https`;
- certificate issuance/renewal is external to K_Supervisor;
- bearer tokens are configured only through `secret://...` references and resolved from the environment/secret backend at startup;
- bearer token contents must never be placed in CLI arguments, config files, logs or durable state;
- configured service extensions activate only through existing Extension Governance; strict mode fails startup on an unauthorized/incompatible configured extension.

Start with:

```text
k-supervisor validate-config service.json
k-supervisor serve --config service.json
```

The host exposes unauthenticated minimal `GET /healthz` and `GET /readyz`. Readiness is false while draining. Business/operator operations remain under `/api/v1` and require Bearer authentication plus the existing independent scopes.

## Online backup

Use an initialized `SQLitePersistenceStore` and its operational manager:

```python
from persistence import SQLiteOperationalManager

manifest = SQLiteOperationalManager(store).backup_to("backups/state.sqlite")
print(manifest.schema_version, manifest.sha256, manifest.integrity_ok)
```

The backup uses SQLite's online backup API, then validates SQLite integrity and records schema version, SHA-256 and size. Store the checksum next to operational backup metadata. Do not overwrite the authoritative database path with a backup operation.

## Backup verification

Before restore, transfer, or long-term retention verification:

```python
verified = SQLiteOperationalManager.verify_backup(
    "backups/state.sqlite",
    expected_sha256="<recorded-sha256>",
)
```

Checksum mismatch, an invalid SQLite file, failed integrity check or missing persistence schema metadata is a hard failure.

## Upgrade qualification

Qualify a backup before upgrading authoritative state:

```python
report = SQLiteOperationalManager.qualify_upgrade("backups/state.sqlite")
```

Qualification works on a temporary copy. Supported legacy schema `1` is migrated to current schema `2` only on that copy. The source backup must remain byte-for-byte unchanged. Unknown/future schema versions fail closed.

Schema version is not bumped merely for backup/restore tooling.

## Restore

Restore is an offline authoritative-store operation:

1. Stop writers and close the authoritative `SQLitePersistenceStore`.
2. Verify the candidate backup and recorded SHA-256.
3. Run upgrade qualification; the candidate is migrated on a temporary copy when required.
4. Invoke `restore_from` using the closed store object.
5. Reopen the store and run deployment/recovery qualification before resuming writes.

```python
manager = SQLiteOperationalManager(closed_store)
manager.restore_from("backups/state.sqlite", expected_sha256="<recorded-sha256>")
```

The restore path validates a temporary candidate before atomic replacement and preserves rollback copies of the existing database family during replacement. Corrupt or unsupported candidates must not modify authoritative state.

## Rollback

If deployment validation fails before authoritative replacement, continue using the existing store and artifact. If post-replacement verification fails during the supported restore operation, the restore boundary restores the prior database family automatically.

For an application/package rollback, reinstall the last validated wheel and reopen the same supported schema. Never downgrade a database to an unsupported schema. Restore a verified pre-change backup instead.

## Graceful shutdown and uncertain mutation outcomes

On SIGINT/SIGTERM or explicit host stop:

1. host state changes to `DRAINING` before listener shutdown;
2. `/readyz` returns 503 and new application requests are rejected;
3. accepted requests may finish within the configured drain interval;
4. SQLite is not closed beneath an active accepted request;
5. if an operation outlives the preferred drain interval, resource close is deferred until accepted work drains;
6. after clean shutdown, reopen SQLite and require `PRAGMA integrity_check = ok`.

A client timeout/disconnect after dispatch does **not** mean a material mutation was cancelled. For an uncertain mutation outcome, retry the same logical request with the same `Idempotency-Key` or query the supported recovery/status route. The CLI surfaces an auto-generated key even on transport uncertainty; preserve it for replay. Do not retry the logical mutation with a new key.

## Project restart and recovery

After process restart:

- reopen persistence;
- call `ProjectRegistry.recover(project_id)` for affected Projects;
- verify lifecycle/operational state, active ProjectSpec, release/target validation, Human Intervention and approval state;
- run `ReliabilityValidator` or `DeploymentQualifier` before resuming material operations;
- preserve `WAITING_FOR_OWNER` blockers. Other Projects may continue according to scheduler limits and their own operational state.

Do not clear owner-required state merely to make the service appear ready.

## Release readiness

Operational reserved release criteria are derived only from authoritative state:

- `operational:schema-current`;
- `operational:store-integrity`;
- `operational:recovery-integrity`.

Project-specific or external criteria are never guessed and must still be supplied explicitly. Reaching `RELEASE_READY` opens the existing publication Human Intervention when publication is required.

## Package-index publication

Package publication is defined by `.github/workflows/package-publish.yml` and is manual-only:

1. Configure the GitHub environment named `pypi` with appropriate owner/workspace protection.
2. Configure PyPI Trusted Publishing for this repository/workflow/environment.
3. In GitHub Actions, manually run **Package Publish**.
4. Set `confirm_owner_publication=true` only after owner review.
5. The build job creates distributions and runs metadata validation.
6. The publish job runs in the protected `pypi` environment and obtains an OIDC token through `id-token: write`; no long-lived PyPI password/token is required by the workflow.
7. After external publication succeeds, confirm publication back through the existing K_Supervisor release/publication boundary.

The workflow has no `push`, `tag`, `release` or scheduled trigger. A normal merge cannot publish a package.

## Incident and failure handling

- Failed backup: keep authoritative store online; discard incomplete candidate.
- Failed restore qualification: do not replace authoritative storage.
- Unsupported schema: stop and obtain a supported migration path; do not rewrite the schema version manually.
- Required service probe failure: deployment qualification fails even if Projects themselves are healthy.
- Project-specific corruption/referential failure: isolate the affected Project and recover from verified authoritative state; do not infer missing records.
- Owner intervention pending: leave the Project `WAITING_FOR_OWNER`; unrelated active Projects may proceed.
- Publication failure: keep release/target in the owner-controlled publication state and retry externally only after resolving the cause.

## Verification evidence

Phase 8 qualification is complete only when phase-specific tests, cumulative regressions, protected `Core Validation`, wheel build/install, public smoke, backup/restore/upgrade tests, lifecycle/recovery/concurrency tests and publication-workflow contract tests all pass on the committed implementation baseline.

## Phase 4 Governed Repository Operations

The production operator path for repository work is Service/API and the matching CLI. Operators must not call the raw GitHub adapter or transport directly.

Repository credentials are supplied only through protected references in the active approved ProjectSpec, for example:

```text
repository_credential_ref=secret://project/<project-id>/github
```

Do not place a GitHub token in ProjectSpec JSON, CLI arguments, repository files, logs or durable audit data.

Read the safe configured repository status with:

```text
k-supervisor repository status <project-id> --config <client-config>
```

Start or resume repository bootstrap with a stable idempotency key:

```text
k-supervisor repository bootstrap <project-id> --config <client-config> --idempotency-key <stable-key>
```

On an uncertain client outcome, retry with the same idempotency key. Do not generate a replacement key merely because the client timed out.

If the response reports `OWNER_ACTION_REQUIRED`:

- inspect the project's Human Actions and Policy Approvals through the supported Service/API or CLI surfaces;
- perform only the explicitly requested owner action;
- verify/approve through the existing owner controls;
- retry repository bootstrap with the same idempotency key.

Repository rulesets and protected branches remain authoritative. K_Supervisor must not force-update refs, bypass branch protection, automatically merge a protected pull request or treat VCS handoff as publication.

A GitHub repository operation that is blocked by credentials, repository policy, organization policy or conflicting owner-authored content remains owner-intervention state until the safe resume condition is satisfied.


