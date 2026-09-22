# V0_4_PHASE4_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 4 — GitHub Repository Provider & Governed VCS Handoff.

Version: 1.0
Status: COMPLETE — ACTIVATION PENDING
Date: 2026-09-22
Baseline main: 08431e31d0f8b1ad61c6d69fd4038155f46f60e7
Baseline tree: 47858060dc9d92f1441496c1ea6713696f9bf008
Validated runtime predecessor main: a1791b607496edfaf84593d753f7d1d7662eede1
Validated runtime predecessor tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Predecessor phase: v0.4 Phase 3 COMPLETE
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 4 is limited to the approved ROADMAP v0.4 GitHub Repository Provider & Governed VCS Handoff assignment:

- production GitHub repository adapter behind existing Project Factory / provisioning boundaries;
- protected-reference credential resolution with no token persistence in ordinary state, audit, telemetry, release records or generated repository files;
- repository create/resolve and exact visibility/default-branch validation;
- bootstrap file application with conflict protection;
- governed branch, commit and pull-request operations for project/release artifacts;
- optional release-tag preparation only when explicitly permitted;
- idempotent retry/recovery for partial provider failures;
- normalized auth, permission, rate-limit, conflict and provider/network failures;
- durable correlation/audit for material external effects;
- explicit Human Intervention fallback when credentials, permissions, organization/repository policy or conflicts block automation.

Explicitly outside Phase 4:

- automatic protected-branch merge;
- bypass or weakening of repository rulesets / branch protection;
- broad GitHub administration unrelated to the target repository;
- GitLab/Bitbucket production adapters;
- automatic external publication;
- broad cloud/server/database provisioning;
- Phase 5 Plugin-native packaging changes;
- Phase 6 telemetry/SBOM/provenance work beyond correlation needed for the repository provider;
- paid development-validation dependencies.

`DEVELOPMENT_RESOURCE_POLICY.md` remains authoritative.

## 2. Frozen Predecessor and Ancestry

Phase 3 runtime completion remains the authoritative runtime predecessor:

```text
Phase 3 implementation PR: #29
Final runtime head: c73e4c5f24f958ebb1473d4c8d23f28244c9f799
Final runtime tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Final exact-head Core Validation: 35453258878 — PASS
Runtime merged main: a1791b607496edfaf84593d753f7d1d7662eede1
Merged-main Core Validation: 35453297160 — PASS
Full regression: 229 passed
Branch-aware coverage: 82.06%
```

Current main is:

```text
main: 08431e31d0f8b1ad61c6d69fd4038155f46f60e7
tree: 47858060dc9d92f1441496c1ea6713696f9bf008
```

The compare from the Phase 3 runtime merge to current main is ahead-only by 20 commits and changes only `.github/workflows/core-validation.yml`, `README.md`, and `docs/*`. No runtime/source/test path changed after the validated Phase 3 runtime merge.

The CI-only change moved protected `Core Validation` to the guarded repository-scoped ARM64 self-hosted runner. Completion authority is `PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_COMPLETE_2026_09_22.md`.

Therefore `a1791b60...` / tree `0f7b1ecb...` remains the runtime predecessor for Phase 4.

## 3. Existing Repository / Project Factory Compatibility Floor

The existing stable repository abstraction is intentionally small:

```text
RepositoryAdapter
  prepare(target) -> ManagedRepository
  apply_files(repository, files)
  list_files(repository)
```

Existing `FilesystemRepositoryAdapter` provides:

- local Git repository initialization;
- idempotent identical-file application;
- conflict rejection for different existing content;
- path traversal protection;
- deterministic file listing.

`ProjectFactory.bootstrap()` already enforces:

- project must be operationally ACTIVE;
- lifecycle must be APPROVED or PROVISIONING;
- active ProjectSpec must be APPROVED;
- lifecycle moves to PROVISIONING before repository side effects;
- unavailable repository handling may create a structured HumanActionRequest;
- generated bootstrap files are validated before BOOTSTRAPPED;
- bootstrap can resume from PROVISIONING.

These semantics remain compatibility requirements.

## 4. Existing Protected-Access and Side-Effect Floor

Reusable security primitives already exist:

- `AccessReference` requires `secret://<scope>/<name>`;
- `EnvironmentSecretBackend` resolves references at runtime;
- `ProtectedSecret` renders redacted;
- `ProjectSpec.repository` rejects plaintext credential-like values through `validate_access_references()`;
- `SideEffectGateway` provides policy re-evaluation, permission/reference enforcement, approval gating, durable idempotency, correlation and audit for Tool/Provider side effects;
- `ProviderExecutionError` is the normalized safe provider error boundary.

Permanent invariant:

```text
material external write
  -> policy / approval
  -> idempotency / durable correlation
  -> concrete provider call
```

A GitHub adapter must not create a parallel ungoverned network-write path.

## 5. Current Gaps

### 5.1 No production GitHub repository adapter

There is no GitHub repository/VCS implementation in the runtime. The only working repository adapter is local filesystem Git.

### 5.2 RepositoryAdapter is not a VCS handoff contract

The current interface has no explicit operations for:

- repository resolve by owner/name;
- branch create/resolve;
- atomic multi-file commit;
- pull-request create/resolve;
- tag preparation;
- remote head / expected base tracking;
- protected-branch policy failure.

Phase 4 must add these capabilities without breaking the existing filesystem adapter.

### 5.3 A naive GitHub RepositoryAdapter would bypass centralized external-side-effect governance

`ProjectFactory` currently calls `adapter.prepare()` and `adapter.apply_files()` directly. That is safe for the local filesystem baseline but is insufficient for a production external GitHub write path.

Also, `RepositoryProvisioningAdapter` currently delegates directly to its wrapped repository adapter, and `ProviderProvisioningAdapter` calls `provider.execute()` directly.

Phase 4 must ensure production GitHub writes traverse a governed repository side-effect boundary. Service/API authentication or Project lifecycle validation alone is not a substitute for policy/approval enforcement.

### 5.4 Repository credential resolution is not wired to the repository path

`RepositoryTarget` contains provider/owner/name/visibility/url/default_branch/ci_required/provisioning, but no explicit protected access reference.

`ProvisioningRequest` supports `access_refs`, but the current `RepositoryProvisioningAdapter` ignores request configuration and access references and hard-codes PRIVATE / owner=None / main.

This bridge is not sufficient for production GitHub provisioning.

### 5.5 No production VCS restart/recovery contract

Current local bootstrap recovery relies on filesystem idempotency and conflict checks. GitHub create/commit/branch/PR operations need deterministic remote reconciliation so restart/retry cannot create duplicate repositories, commits or PRs.

### 5.6 Production service composition does not include ProjectFactory / repository provider wiring

`build_service_runtime()` currently composes persistence, registries, kernel, human intervention, approvals, workflows, telemetry and Service/API, but not a production repository adapter or ProjectFactory.

Phase 4 must add repository-provider composition without introducing a second control plane.

### 5.7 No explicit operator repository-bootstrap operation

The current Service/API v1 surface has no repository/bootstrap/provisioning route. Changing an ordinary lifecycle transition so that it silently performs remote GitHub writes would make side effects less explicit.

If Phase 4 exposes repository bootstrap through the supported operator product boundary, it must be an additive explicit operation with a narrow scope and idempotency contract, and the matching CLI must call Service/API rather than GitHub directly.

### 5.8 Current generated CI scaffold targets GitHub-hosted Ubuntu

The bootstrap template generates `.github/workflows/validation.yml` using `ubuntu-latest`. Phase 4 implementation/validation must not require execution of that generated hosted workflow. A live GitHub smoke, if used, must avoid creating a paid development dependency.

## 6. Target Architecture

Preferred Phase 4 structure:

```text
ProjectFactory / ReleaseManager
        |
        v
Governed Repository/VCS Boundary
        |
        +--> policy / approval
        +--> access-reference authorization
        +--> durable idempotency / correlation
        +--> normalized provider errors
        |
        v
GitHubRepositoryAdapter / GitHubRestClient
        |
        v
GitHub REST API
```

The concrete implementation may refactor/reuse `SideEffectGateway` or introduce a repository-specific gateway that shares the same invariants. It must not permit ProjectFactory, ReleaseManager, Service/API or CLI to call the raw GitHub client directly for material writes.

Read-only repository inspection may use the same adapter boundary but must remain correlation-aware and credential-safe.

## 7. GitHub API Compatibility Snapshot

Official GitHub REST documentation was inspected on 2026-09-22. Current examples use the versioned REST header:

```text
X-GitHub-Api-Version: 2026-03-10
```

Relevant current API facts:

- Git references, trees and commits support repository `Contents` permissions;
- creating/updating references defaults to non-force / fast-forward-safe behavior when `force=false`;
- pull-request creation requires `Pull requests: write`;
- repository creation requires repository administration authority;
- modifying workflow files may require `Workflows: write` in addition to contents authority;
- primary rate-limit exhaustion can return 403 or 429 with `x-ratelimit-remaining: 0`;
- secondary rate limiting can return 403 or 429 and may provide `retry-after`;
- GitHub advises waiting for reset/retry-after rather than immediate retry;
- creating a Git reference cannot initialize an otherwise empty repository.

Implementation must pin an explicit supported GitHub REST API version rather than depending on an unversioned default.

## 8. Authentication and Least-Privilege Credential Contract

Phase 4 supports a token supplied through the existing `SecretBackend` boundary. The platform must not persist or print token contents.

Accepted credential forms may include a fine-grained PAT or GitHub App installation token, provided externally. K_Supervisor does not need to become a GitHub App authorization server in Phase 4.

ProjectSpec should carry only an opaque reference, for example:

```text
repository_provider=GITHUB
repository_owner=<explicit owner>
repository_name=<explicit name>
repository_credential_ref=secret://project/<project-id>/github
```

For AUTOMATABLE GitHub repository creation, owner and repository name must be explicit. Ambiguous owner inference must not be used as a durable project identity.

Least privilege is operation-specific:

```text
repository resolve/read        -> Metadata/Contents read as required
repository create              -> Administration write
commit/ref writes              -> Contents write
workflow-file bootstrap        -> Workflows write when GitHub requires it
pull-request creation          -> Pull requests write
tag/ref preparation            -> Contents write
```

The implementation must validate missing/insufficient authority and open Human Intervention rather than asking for a broad classic token scope as a platform invariant.

## 9. Repository Create / Resolve Contract

For a GitHub target, `prepare()` or its Phase 4 successor must:

1. canonicalize owner/name;
2. resolve the repository by exact owner/name;
3. if present, validate expected visibility, archived/disabled state and configured identity;
4. if absent and provisioning is AUTOMATABLE, perform governed create;
5. if absent and owner action is required, open Human Intervention;
6. after create, re-read canonical remote state instead of trusting only the create response;
7. return a `ManagedRepository` with stable provider/id/locator/default-branch facts.

Idempotency rule:

- retry after an uncertain create must first resolve exact owner/name;
- an existing repository that matches the intended target is a replay/recovery result, not a duplicate-create request;
- an existing repository with conflicting identity/visibility/configuration is a conflict, not implicit adoption.

## 10. Bootstrap and Commit Contract

Bootstrap must preserve the existing no-silent-overwrite rule.

For a newly created repository:

- implementation must establish the first branch/commit deterministically;
- because Git reference creation cannot initialize an empty GitHub repository, the adapter must use a documented bootstrap mechanism such as provider-side initialization or an initial content commit before normal Git Data ref operations;
- provider-created initialization content may be replaced only when the adapter can prove it created that repository in the same logical operation.

For an existing repository:

- generated paths are compared before write;
- identical content is a no-op/replay;
- differing existing owner-authored content is a `RepositoryConflictError` / normalized equivalent;
- no force-push is permitted.

Multi-file bootstrap should converge to one logical commit where practicable. The commit must be based on a known remote head/tree, and branch ref movement must use non-force fast-forward semantics.

## 11. Branch and Pull-Request Handoff

After initial creation/bootstrap, material updates to an existing governed repository should use a work branch plus pull request rather than silently writing the protected/default branch.

Required behavior:

- deterministic or recoverable branch naming tied to the logical operation/idempotency key;
- exact base branch validation;
- no branch overwrite by force;
- one logical commit or deterministic commit sequence per handoff;
- existing equivalent open PR is reused on retry;
- divergent existing branch/PR content produces conflict;
- protected-branch/ruleset refusal is surfaced and never bypassed;
- merge remains external/owner/repository-governance controlled.

This satisfies the ROADMAP boundary:

```text
governed VCS handoff != automatic merge/publication
```

## 12. Optional Release Tag Preparation

Release tag preparation is optional and must be explicitly enabled by project/release policy.

Rules:

- create only a new tag/ref for an exact expected commit;
- existing identical tag is idempotent replay;
- existing tag pointing elsewhere is conflict;
- never move/overwrite a tag automatically;
- tag creation does not imply GitHub Release publication or external publication.

## 13. Policy and Approval Mapping

Minimum side-effect mapping:

```text
repository create      -> CREATE_RESOURCE
branch create          -> CREATE_RESOURCE / WRITE_EXTERNAL
commit/ref update      -> WRITE_EXTERNAL / MODIFY_RESOURCE
pull-request create    -> CREATE_RESOURCE / WRITE_EXTERNAL
tag create             -> CREATE_RESOURCE
repository read        -> READ_EXTERNAL
```

The exact internal request model may be additive, but all material external operations must be evaluated before provider invocation.

Operator/API authorization and project lifecycle checks are additive defenses. They do not replace the repository side-effect policy gate.

## 14. Idempotency and Partial-Failure Recovery

Each logical repository operation needs a stable idempotency/correlation key scoped at least by:

```text
project_id
ProjectSpec id/version
repository owner/name
operation
logical payload/content signature
```

Required recovery examples:

- create returned transport timeout but repository exists -> resolve and continue;
- commit object created but branch ref not advanced -> detect intended commit/tree and finish or safely retry;
- branch created but PR call failed -> reuse branch and create/reuse exactly one PR;
- PR created but response lost -> query by head/base and reuse;
- rate-limit response -> preserve pending/retryable state; do not create a second logical effect;
- restart -> recover from durable correlation plus remote canonical state.

Same idempotency key with different material payload must fail as an idempotency conflict.

The audit does not require a new SQLite schema if existing durable side-effect records plus deterministic remote reconciliation satisfy these rules. If implementation needs new durable repository-operation state, schema migration/rollback/reopen tests become mandatory.

## 15. Error Normalization

The production adapter must translate provider/network failures into safe categories without token leakage.

Minimum categories:

```text
AUTHENTICATION            non-retryable until credential changes
PERMISSION                non-retryable until permission/policy changes
NOT_FOUND                 contextual; resolve vs create logic decides
CONFLICT                  non-retryable without reconciliation
RATE_LIMIT                retryable only after safe reset/retry-after
VALIDATION                non-retryable until request changes
NETWORK                   retryable with bounded backoff
PROVIDER_UNAVAILABLE      retryable for bounded 5xx/service failure
```

GitHub 403 must not be classified as a single generic permission error without checking safe rate-limit headers/context.

Provider error bodies must be allowlisted/sanitized before durable audit or operator display.

## 16. Human Intervention Contract

Automation must open a structured HumanActionRequest when any of these blocks progress:

- credential missing;
- credential lacks required GitHub permission;
- organization policy prevents repository creation;
- repository visibility or identity conflicts with ProjectSpec;
- repository/ruleset/branch protection refuses a material write;
- owner-authored bootstrap file conflict;
- manual authorization or repository creation is required;
- provider authentication requires owner action.

Human Intervention must state the exact safe action required and a verifiable resume condition. It must never include raw tokens.

## 17. Operator Service/API and CLI Boundary

The production single-node product must not require an owner to import ProjectFactory in Python.

Phase 4 may add a narrow explicit Service/API operation and matching CLI operation for repository bootstrap/handoff if needed to expose the existing Project Factory safely.

Rules:

- explicit repository/provisioning operation; do not hide remote writes behind an ordinary lifecycle transition;
- separate read/write scope(s) or an equally narrow compatible authorization boundary;
- material request requires an idempotency key / durable command receipt where applicable;
- Service/API calls ProjectFactory/governed repository orchestration, not the raw GitHub client;
- CLI calls Service/API only;
- no CLI argument containing a GitHub token;
- safe repository status may expose owner/name/url/branch/PR identifiers but never secret values.

This is an additive Phase 4 integration surface, not a second control plane.

## 18. Service Runtime Composition Contract

The production composition root must be able to wire:

```text
SecretBackend
GitHub REST transport/client
GitHub repository/VCS adapter
governed repository side-effect boundary
ProjectFactory
Human Intervention
ServiceApiV1 integration
```

The GitHub adapter should remain replaceable through the existing adapter/extension architecture. Supervisor core, WorkflowEngine and domain agents must not import GitHub-specific implementation modules.

No production credential is required merely to start the service when GitHub automation is not configured for a project.

## 19. Zero-Cost Validation Plan

Normal protected CI must remain credential-free.

Authoritative Phase 4 validation uses:

- injected deterministic fake GitHub HTTP transport/provider;
- local fixtures for response/status/header sequences;
- existing SQLite/policy/human-intervention infrastructure;
- exact content/tree/ref/PR replay simulations;
- installed-wheel import/composition smoke where the new adapter is public/configurable.

A real GitHub smoke is supplemental and owner-controlled. If used, it must:

- use only a pre-authorized disposable repository/account scope;
- require no paid GitHub feature;
- avoid triggering paid hosted Actions;
- not weaken K_Supervisor repository governance;
- use a short-lived/owner-controlled protected credential reference;
- clean up any disposable resource through a separately approved action.

Successful live external evidence is not an ordinary PR merge dependency.

## 20. Required Test Families

Planned Phase 4 test family:

```text
tests/test_v04_phase4_github_repository_*.py
tests/test_v04_phase4_repository_handoff_*.py
```

Required deterministic coverage:

- GitHub target parsing/canonicalization and explicit owner requirement for automatable create;
- protected credential reference only; plaintext token rejected/redacted;
- missing/insufficient credential -> safe normalized failure + Human Intervention;
- repository create success, uncertain create recovery and exact existing-repo reuse;
- visibility/default-branch/archive/disabled conflict checks;
- empty/new repository initial bootstrap;
- identical bootstrap replay/no-op;
- conflicting existing file rejected without overwrite;
- branch create/resolve idempotency;
- atomic/deterministic multi-file commit behavior;
- non-force ref update / concurrent-head conflict;
- protected-branch/ruleset denial cannot be bypassed;
- one PR per logical handoff; response-loss recovery reuses PR;
- optional tag identical replay and divergent-tag conflict;
- 401/403 permission normalization;
- 403/429 primary and secondary rate-limit backoff metadata;
- 404/409/422/5xx/network normalization;
- same idempotency key + different payload -> conflict;
- restart/reopen does not duplicate repo/commit/branch/PR;
- policy DENY and REQUIRE_APPROVAL block before GitHub call;
- Service/API/CLI path, if added, never calls raw GitHub transport directly;
- no token in ProjectSpec durable JSON, audit, telemetry, errors or CLI output;
- FilesystemRepositoryAdapter predecessor behavior remains compatible;
- release preparation still preserves explicit owner publication boundary;
- cumulative regression and permanent quality gates remain green.

## 21. Implementation Order Guard

After a separate owner-approved Phase 4 activation checkpoint passes protected governance and merges, implementation should proceed in this order:

1. additive GitHub repository configuration/access-reference contract and validation;
2. injectable GitHub REST transport with versioned headers and normalized errors;
3. read-only repository resolve/canonicalization;
4. governed repository side-effect boundary and policy/idempotency integration;
5. repository create/recovery;
6. first bootstrap plus conflict-safe file/tree/commit handling;
7. branch/commit/PR governed handoff;
8. optional tag preparation;
9. production ServiceRuntime / ProjectFactory wiring;
10. narrow Service/API + CLI initiation/status surface if required by the production composition path;
11. Human Intervention recovery flows;
12. deterministic failure/restart/replay tests and installed-wheel validation;
13. documentation/runbook update and full cumulative Core Validation.

If implementation requires bypassing policy, branch protection, rulesets, explicit owner publication, or protected-reference handling, stop and audit the change instead.

## 22. Permanent Compatibility / Non-Scope Invariants

Phase 4 must preserve:

- Python facade and config v1 compatibility unless an explicit migration is approved;
- Service/API v1 compatibility by additive evolution only;
- existing FilesystemRepositoryAdapter behavior;
- existing ProjectSpec approval/lifecycle authority;
- existing SideEffectGateway policy/approval semantics;
- release publication remains explicit owner action;
- no automatic protected-branch merge;
- no hidden GitHub credential persistence;
- zero-cost development validation;
- protected `Core Validation` merge governance.

## 23. Audit Outcome

The existing architecture is suitable for Phase 4 but requires a new governed external-repository layer rather than simply replacing the filesystem adapter with a network client.

Principal design conclusion:

```text
ProjectFactory contract can be preserved
Filesystem adapter remains compatible
GitHub adapter is additive
direct ProjectFactory -> raw GitHub writes are NOT allowed
material GitHub writes require policy/approval + idempotency/correlation
owner publication/merge remains external
```

Audit result:

```text
Phase 0: COMPLETE
Phase 1: COMPLETE
Phase 2: COMPLETE
Phase 3: COMPLETE
Phase 4 pre-implementation audit: COMPLETE
Phase 4 activation: NO / PENDING OWNER APPROVAL
Phase 4 runtime implementation authorized: NO
Phase 5-7: PLANNED / INACTIVE
```

This document does not activate Phase 4. Runtime/source/test changes may begin only after explicit owner approval, a separate Phase 4 activation checkpoint, protected `Core Validation` PASS, and merge to `main`.
