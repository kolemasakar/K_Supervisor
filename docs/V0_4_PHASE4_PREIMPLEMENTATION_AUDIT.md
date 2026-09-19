# V0_4_PHASE4_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 4 — GitHub Repository Provider & Governed VCS Handoff.

Version: 1.0
Status: LOCAL AUDIT COMPLETE — PROTECTED MERGE DEFERRED / ACTIVATION NOT APPROVED
Date: 2026-09-19
Baseline main: `db37da2a1a8210fd45d3bf8dcb716d6fbfba7624`
Baseline tree: `6215ab22dcd0c2daf820168ab2b9d1706be6f650`
Validated runtime predecessor main: `a1791b607496edfaf84593d753f7d1d7662eede1`
Validated runtime predecessor tree: `0f7b1ecba724623996c7e6e84414c029adcc63c7`
Predecessor phase: v0.4 Phase 3 COMPLETE
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 4 is limited to the approved ROADMAP v0.4 GitHub Repository Provider & Governed VCS Handoff assignment:

- production GitHub repository adapter behind existing repository/provisioning contracts;
- protected-reference credential resolution with no token persistence in ordinary state/audit;
- deterministic repository create-or-resolve with owner/name/visibility/default-branch validation;
- conflict-safe bootstrap file application;
- governed branch, commit and pull-request operations for project/release artifacts;
- optional release tag preparation when explicitly permitted;
- idempotent retry/recovery for partial GitHub failures;
- normalized auth/rate-limit/not-found/conflict/provider failures;
- durable correlation/audit plus owner-intervention fallback.

Explicitly out of Phase 4 scope:

- automatic merge of protected/default branches;
- branch-protection/ruleset weakening, bypass, deletion or force-push;
- arbitrary GitHub administration, organization membership or billing management;
- GitHub Actions secrets management;
- broad cloud/server/database provisioning;
- GitLab/Bitbucket production adapters;
- Plugin-native release packaging (Phase 5);
- automatic external publication;
- paid external development resources.

`DEVELOPMENT_RESOURCE_POLICY.md` remains authoritative. The owner-reported GitHub Actions included quota is exhausted; no new hosted Actions run is authorized until no-cost capacity is confirmed.

## 2. Frozen Predecessor and Ancestry

Phase 3 runtime completion is the predecessor:

```text
Implementation PR: #29
Final PR head: c73e4c5f24f958ebb1473d4c8d23f28244c9f799
Final PR tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Final exact-head Core Validation: 35453258878 — PASS
Runtime merged main: a1791b607496edfaf84593d753f7d1d7662eede1
Runtime merged tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Merged-main Core Validation: 35453297160 — PASS
Full regression: 229 passed
Branch-aware coverage: 82.06%
Installed-wheel Phase 3 service/CLI smoke: PASS
```

Phase 3 closure is also complete:

```text
Closure PR: #30
Final closure head: 661b40077369231baa3e21e558b8be61848ca9e8
Final closure Core Validation: 35453726120 — PASS
Current main: db37da2a1a8210fd45d3bf8dcb716d6fbfba7624
Current tree: 6215ab22dcd0c2daf820168ab2b9d1706be6f650
```

The delta from the validated Phase 3 runtime merge to current main is documentation-only closure material. No runtime/source/test path changed after `a1791b60...`; it remains the authoritative runtime predecessor for Phase 4.

## 3. Existing Reusable Repository Boundaries

The current repository architecture already provides the correct provider-neutral seams:

- `RepositoryTarget.from_spec()` projects repository intent from the active approved ProjectSpec;
- `RepositoryAdapter` defines prepare/apply/list behavior without GitHub-specific imports in ProjectFactory;
- `FilesystemRepositoryAdapter` is the working local adapter and compatibility floor;
- `ProjectFactory` enters PROVISIONING before repository work and reaches BOOTSTRAPPED only after generated-file verification;
- `RepositoryProvisioningAdapter` bridges the repository adapter into the generic provisioning abstraction;
- `HumanInterventionBroker` already converts unavailable external repository work into a durable owner action;
- `ProjectSpec` access validation already rejects plaintext values under credential-like keys;
- `AccessReference` / `SecretBackend` provide the protected-reference boundary;
- `ProviderRegistry`, `Provider`, `PolicyEngine` and `SideEffectGateway` provide a governed external-provider invocation pattern with durable idempotency/audit.

The Phase 4 implementation must reuse these seams rather than place GitHub API calls in Supervisor core or Service/API route handlers.

## 4. Current Gaps

### 4.1 No production GitHub repository adapter

`RepositoryAdapter` has only a filesystem implementation. A ProjectSpec declaring `GITHUB` currently blocks or requires owner intervention because no runtime adapter exists.

### 4.2 RepositoryTarget does not carry an explicit protected credential reference

The ProjectSpec can safely contain a credential-like `secret://...` value, but `RepositoryTarget` currently discards it. Phase 4 needs one explicit optional protected reference carried to the adapter/provider boundary.

### 4.3 Remote VCS semantics exceed the local apply/list contract

The existing adapter is sufficient for local file creation but remote GitHub work needs additional concepts:

- canonical remote repository identity;
- current default-branch head;
- deterministic working branch;
- one logical bootstrap/change commit;
- pull-request handoff;
- optional tag preparation;
- durable correlation to recover after partial provider success.

The base `RepositoryAdapter` must remain backward-compatible. Remote VCS operations therefore require an additive protocol/service rather than making every filesystem adapter implement GitHub-specific concepts.

### 4.4 ProjectFactory cannot directly bypass the side-effect governance invariant

The v0.4 hardening baseline requires material external operations to traverse policy/permission/approval enforcement. A GitHub adapter must not call the network directly from ProjectFactory without the existing governed provider boundary.

### 4.5 No GitHub-specific error normalization or rate-limit behavior

Current repository errors distinguish conflict/unavailable only. GitHub adds authentication/authorization, not-found, validation/conflict, primary/secondary rate-limit, timeout and transient-server cases that require deterministic normalization and bounded retry rules.

### 4.6 No durable GitHub repository/commit/PR/tag recovery contract

Filesystem idempotency is content-based. Remote operations can succeed externally while the client loses the response. Phase 4 therefore needs deterministic operation identities and provider reconciliation before any retry can create a second repository, commit, PR or tag.

## 5. Current GitHub REST Contract Snapshot

The implementation target is the current versioned GitHub REST API, with an injectable transport so CI remains credential-free and network-free.

Audit-time official GitHub documentation confirms:

- repository creation requires repository Administration write permission for fine-grained tokens;
- Git data commit/ref/tag creation requires Contents write permission;
- pull-request creation requires Pull requests write permission;
- modifying files under `.github/workflows` may additionally require Workflows write permission;
- primary rate-limit exhaustion is signaled by 403/429 plus `x-ratelimit-remaining = 0` and `x-ratelimit-reset`;
- secondary rate limiting can use 403/429 plus `retry-after`, and repeated requests while limited must not continue blindly.

The adapter must send an explicit GitHub API version header and recommended JSON media type. API-version selection is configuration/implementation detail, not a persisted ProjectSpec compatibility invariant.

Reference documentation reviewed on 2026-09-19:

- https://docs.github.com/en/rest/repos/repos
- https://docs.github.com/en/rest/repos/contents
- https://docs.github.com/en/rest/git/commits
- https://docs.github.com/en/rest/git/refs
- https://docs.github.com/en/rest/git/tags
- https://docs.github.com/en/rest/pulls/pulls
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

## 6. Repository Target and Credential Contract

Phase 4 may add one backward-compatible optional protected-reference field to `RepositoryTarget`, populated from an explicitly credential-like ProjectSpec repository key such as `credential`.

Required rules:

- GitHub automation requires a valid `AccessReference`; plaintext token material is rejected by existing ProjectSpec validation;
- the same reference must be inside the active ProjectSpec policy `allowed_access_refs` when a governed operation requests it;
- GitHub owner and repository name must be explicit for deterministic create/resolve behavior;
- visibility must normalize to the declared ProjectSpec value and mismatch must fail closed;
- if a repository URL is supplied, it is a validation hint/constraint, never a source of embedded credentials;
- default branch is explicit and validated against the remote repository;
- repository credential contents are resolved only inside the concrete GitHub provider immediately before transport use.

Token type is intentionally opaque. Fine-grained personal access tokens and GitHub App installation/user tokens may be supported when their granted permissions satisfy the requested operation. K_Supervisor does not persist, inspect or infer the raw token beyond using it as a bearer credential.

## 7. GitHub Provider and Adapter Architecture

The production path should be layered:

```text
ProjectFactory / Release handoff
    -> GitHubRepositoryAdapter / VCS handoff service
        -> SideEffectGateway
            -> PolicyEngine + approval/access checks
            -> GitHubRepositoryProvider
                -> SecretBackend.resolve()
                -> GitHubTransport
                -> GitHub REST API
```

### 7.1 GitHubRepositoryProvider

Add a provider registered behind `ProviderRegistry`, with a narrow provider id such as `github.repository`.

Authorized operation vocabulary should remain explicit and finite, for example:

```text
repository.get
repository.create
contents.inspect
commit.create
branch.create
branch.update
pull_request.get_or_create
tag.get_or_create
```

No generic arbitrary-method/arbitrary-URL operation is permitted.

### 7.2 Transport

Use an injectable `GitHubTransport` protocol and a small production HTTPS implementation. Normal CI uses a deterministic fake transport.

Transport requirements:

- HTTPS only for github.com;
- bounded connect/request/response sizes;
- explicit User-Agent, Accept and API-version headers;
- bearer token added only at request dispatch;
- authorization headers never appear in exceptions, logs or metadata;
- response headers expose only safe request/rate-limit correlation metadata;
- retry sleeps are bounded and injectable/testable.

A mandatory third-party GitHub SDK is not required for Phase 4.

### 7.3 Repository adapter compatibility

`FilesystemRepositoryAdapter` remains unchanged in behavior.

The base `RepositoryAdapter` prepare/apply/list contract remains supported. GitHub-specific VCS handoff behavior should be exposed through an additive protocol/service so existing adapters are not forced to implement branch/PR/tag methods.

## 8. Policy and Side-Effect Enforcement Contract

GitHub mutations are material external side effects and must use `SideEffectGateway.execute_provider()`.

To preserve existing policy semantics without creating a second policy engine, Phase 4 should register a small internal platform automation capability/agent used only by ProjectFactory/repository handoff composition.

Recommended internal identifiers are stable implementation details, for example:

```text
agent_id: platform.project_factory
capability_id: platform.repository.github
capability_version: 1.0
```

The capability declares the maximum repository side effects. Each operation requests only the narrow subset required:

- remote reads: `READ_EXTERNAL`;
- repository creation: `CREATE_RESOURCE`;
- branch/commit/PR/tag writes: `WRITE_EXTERNAL` and/or `MODIFY_RESOURCE` as appropriate;
- no delete operation is required in Phase 4.

The ProjectSpec policy remains authoritative:

- denied/unsupported side effects never reach GitHub;
- the credential reference must be allowed;
- default material-write policy may require explicit approval;
- `PolicyApprovalBroker` / `HumanInterventionBroker` remain the owner-approval path;
- resumption reuses the exact permission scope and deterministic operation identity.

The repository adapter must not expose a direct network method that production ProjectFactory can invoke around this gateway.

## 9. Repository Create-or-Resolve Contract

Repository preparation is deterministic:

1. resolve `owner/name`;
2. if found, validate canonical owner/name, visibility and default branch;
3. if not found, distinguish a genuine absence from an authentication/permission-masked 404 using the configured operation/credential context and fail safely;
4. create only when ProjectSpec provisioning is `AUTOMATABLE` and policy allows `CREATE_RESOURCE`;
5. if automation is not authorized, open/retain owner intervention instead of creating;
6. after create, re-read and validate the canonical repository projection before returning success.

A repeated prepare call must resolve the same repository and return `created=False`; it must never create a name-suffixed duplicate.

The adapter must not rename, transfer, delete, archive or change visibility of an existing repository in Phase 4.

## 10. Bootstrap File and Commit Contract

Conflict protection from `FilesystemRepositoryAdapter` remains mandatory.

For every generated bootstrap path:

- absent path: eligible to add;
- existing byte-identical content: no-op;
- existing different content: fail with repository conflict;
- path traversal and unsafe generated paths remain prohibited.

Remote bootstrap should produce one logical commit rather than one commit per file.

### 10.1 New empty repository

GitHub cannot create a branch reference in an empty repository before a commit exists. For a repository newly created by K_Supervisor, Phase 4 may create exactly one root bootstrap commit and establish the declared default branch.

The root commit must be deterministic from the approved bootstrap file set and correlation metadata. Retry must first resolve the repository/default-branch state and recognize an already-created equivalent root commit.

### 10.2 Existing repository

For an existing non-empty repository, K_Supervisor must not write directly to the protected/default branch.

It should:

1. resolve current default-branch head;
2. create or resolve a deterministic K_Supervisor working branch;
3. verify generated file conflicts against that branch/base;
4. create one commit when material changes are needed;
5. open or resolve an existing pull request back to the default branch;
6. stop at the VCS handoff boundary.

No automatic PR merge is permitted.

## 11. Deterministic Branch, Commit and PR Identity

Remote recovery requires stable identities derived from project/spec/purpose rather than random names.

Recommended shape:

```text
branch: ksupervisor/<purpose>/<stable-short-id>
commit correlation: project_id + project_spec_id/release_id + content signature
PR lookup key: repository + head branch + base branch
```

Exact user-visible names may be sanitized/truncated for GitHub limits, but the derivation must be deterministic and collision-tested.

Commit messages and PR bodies may contain non-secret correlation references, but never raw ProjectSpec protected values or tokens.

A retry after transport uncertainty must reconcile remote state before attempting another material write.

## 12. Pull Request and Protected-Branch Boundary

Phase 4 is a governed handoff, not an autonomous merge system.

Required invariants:

- the adapter may inspect branch/ruleset/protection state needed to understand whether the requested handoff is possible;
- it must never disable, weaken or replace branch protection/rulesets;
- it must never force-push protected/default branches;
- it must never invoke an administrative bypass to make a denied operation succeed;
- it may create a working branch and pull request when permitted;
- merge remains external/owner-controlled unless a later roadmap phase explicitly authorizes otherwise;
- permission/protection denial is normalized and may open Human Intervention.

If repository policy requires reviews, status checks or conversation resolution, K_Supervisor records the handoff and waits; it does not spoof completion of those controls.

## 13. Release VCS Handoff and Tag Contract

Phase 4 may extend release preparation only far enough to create a governed VCS handoff.

Allowed behavior:

- prepare/update release artifacts through the same conflict-safe working-branch + commit + PR path;
- correlate the VCS handoff with project/release/release-target identifiers;
- optionally prepare a tag only when ProjectSpec/release policy explicitly permits it and the target commit is unambiguous.

Tag rules:

- deterministic tag name from approved release version/profile;
- existing tag pointing to the same object is an idempotent replay;
- existing tag pointing elsewhere is a conflict;
- no tag deletion or force-move;
- creating a GitHub Release/publication is out of Phase 4 scope.

`ReleaseManager` remains responsible for readiness/publication handoff. GitHub VCS work must not turn owner publication confirmation into automatic external publication.

## 14. Error Normalization and Retry Contract

GitHub transport/provider failures must normalize into safe categories without embedding provider response bodies or credentials in ordinary errors.

Minimum normalized classes:

```text
GITHUB_CONFIGURATION_ERROR
GITHUB_AUTHENTICATION_ERROR
GITHUB_PERMISSION_DENIED
GITHUB_NOT_FOUND
GITHUB_CONFLICT
GITHUB_RATE_LIMITED
GITHUB_TIMEOUT
GITHUB_TRANSIENT_ERROR
GITHUB_INVALID_RESPONSE
GITHUB_FAILURE
```

Retry rules:

- retry only operations classified retryable;
- retries require deterministic idempotency/correlation;
- primary rate-limit retry must not occur before `x-ratelimit-reset`;
- secondary rate-limit retry honors `retry-after` when present;
- otherwise use bounded backoff and stop after a configured attempt bound;
- 401/403 permission/auth failures are not blind-retry candidates;
- 404 is not automatically interpreted as repository absence for private resources;
- 409/422 material conflicts require reconciliation or owner intervention, not repeated writes.

Provider request ids and safe rate-limit headers may be retained as metadata; raw response bodies and Authorization values must not enter audit/state.

## 15. Durable Idempotency and Recovery Contract

Every material GitHub operation must pass a deterministic idempotency key to `SideEffectGateway`.

The existing durable `SideEffectExecutionRecord` remains the first authority for attempted/outcome state. GitHub-specific reconciliation is still required because a provider operation may have succeeded remotely before the local outcome was recorded.

Recovery examples:

- repository create uncertain -> GET exact owner/name before any re-create;
- branch create uncertain -> resolve exact ref and expected base SHA;
- commit create uncertain -> search deterministic branch/head/content correlation before another commit;
- PR create uncertain -> resolve by exact head/base pair before another PR;
- tag create uncertain -> resolve exact tag/ref and object before another tag.

A stale local PENDING record must never be treated as proof that the remote operation failed.

No new physical SQLite schema is required if durable records fit the existing generic resource/event persistence layout; any new persisted contract must remain versioned and backup/restore compatible.

## 16. Owner Intervention Contract

The existing `HumanInterventionBroker` is the fallback for blocked repository automation.

Owner intervention is appropriate when:

- credential reference is missing/unavailable;
- token lacks required permissions;
- organization/repository policy disallows creation or writes;
- repository must be created/authorized manually;
- branch protection prevents the requested handoff;
- conflicting pre-existing content requires an owner decision;
- rate/abuse limits or provider state make safe automation unavailable beyond bounded retry.

The HumanActionRequest must describe the required owner action without including token material. Resume verification re-runs safe provider/repository checks; a manual “done” message is not by itself proof of remote state.

## 17. Configuration and Compatibility Decision

Phase 4 must preserve existing ProjectSpec and repository compatibility.

Allowed additive changes include:

- optional protected repository credential reference;
- optional GitHub provider configuration such as bounded timeout/retry settings outside ordinary project secrets;
- optional VCS handoff policy fields under existing repository/release objects;
- additive public exports for the GitHub adapter/provider contracts.

Existing FILESYSTEM ProjectSpecs and `FilesystemRepositoryAdapter` behavior must remain green without migration.

No Service/API v1 route or CLI expansion is required by Phase 4. If implementation discovers that operator-driven repository actions need a new API command, that is a separate audited scope decision rather than an implicit addition.

## 18. Zero-Cost Validation Plan

Phase 4 implementation and qualification must not require GitHub API calls that consume paid project resources.

Authoritative deterministic evidence can use:

- fake GitHub transport responses;
- local in-memory transport state that models repository/ref/commit/PR/tag resources;
- temporary SQLite;
- existing ProjectFactory/Policy/SideEffectGateway composition;
- failure-injection for timeout/auth/rate-limit/conflict/restart cases;
- local wheel build/install and public import smoke.

A real GitHub live smoke is supplemental only when it is available with no additional project-attributable charge and when the configured owner credential/repository can be used safely.

The current GitHub Actions included quota is exhausted. Therefore the audit itself may be prepared locally and pushed only on a docs-only branch that does not trigger Actions, but its protected PR/merge gate is deferred until zero-cost CI capacity is available again.

## 19. Required Test Families

Planned Phase 4 families:

```text
tests/test_v04_phase4_github_repository_provider.py
tests/test_v04_phase4_github_repository_bootstrap.py
tests/test_v04_phase4_github_vcs_handoff.py
tests/test_v04_phase4_github_recovery.py
```

Required deterministic coverage:

- provider availability and missing credential fail closed;
- protected credential reference is required/authorized and plaintext never persists;
- create vs resolve-existing is deterministic;
- owner/name/visibility/default-branch mismatch is rejected;
- private-resource 404 is not blindly treated as absence;
- new empty repository obtains exactly one deterministic root bootstrap commit;
- existing repository uses deterministic working branch + one logical commit + PR;
- byte-identical bootstrap content is idempotent and conflicting content fails closed;
- branch protection/permission denial never triggers bypass/force/default-branch write;
- exact head/base PR lookup prevents duplicate PRs;
- commit/tag/branch retries reconcile remote state after uncertain transport outcome;
- existing tag same-target replay vs different-target conflict;
- primary/secondary rate-limit semantics and bounded backoff;
- auth, permission, not-found, conflict, timeout, transient and malformed-response normalization;
- owner intervention opens and resumes safely;
- `SideEffectGateway` policy DENY/REQUIRE_APPROVAL invokes GitHub zero times;
- access-reference denial invokes GitHub zero times;
- filesystem repository regression remains green;
- release VCS handoff stops before merge/publication;
- cumulative regression, branch-aware coverage >=80%, ResourceWarning-as-error, compileall, wheel build/install and public CLI/import smoke.

## 20. Implementation Order Guard

Only after a separate owner-approved activation checkpoint is protected/merged may runtime implementation begin.

Recommended order:

1. additive repository target credential/VCS contracts and safe error types;
2. deterministic fake GitHub transport plus production HTTPS transport;
3. `GitHubRepositoryProvider` read/create primitives with secret resolution;
4. internal platform repository capability/agent registration and SideEffectGateway composition;
5. `GitHubRepositoryAdapter` create-or-resolve behavior and FILESYSTEM compatibility;
6. deterministic bootstrap branch/tree/commit logic;
7. pull-request handoff and protected-branch enforcement;
8. optional release tag/handoff integration;
9. recovery/reconciliation and owner-intervention paths;
10. docs/runbook/public exports;
11. Phase 4 + cumulative deterministic validation.

If implementation would require automatic merge, branch-protection modification, GitHub secrets administration or a generic arbitrary GitHub API proxy, stop and re-audit instead of widening Phase 4.

## 21. Hosted-CI Quota Governance

At audit preparation time the owner reported:

```text
GitHub Actions included usage: 2,000 / 2,000 minutes
Further usage: may be billed
UI reset date: 2026-10-01
```

Under `DEVELOPMENT_RESOURCE_POLICY.md`:

- no new GitHub-hosted Actions run is authorized while no-cost capacity is unavailable;
- this docs branch may be pushed because current `Core Validation` push path filters do not include ordinary `docs/**` changes;
- a pull request targeting `main` would trigger `Core Validation`, so the audit PR must not be opened yet;
- repository protection/required-CI rules must not be bypassed;
- Phase 4 activation cannot proceed before the audit is protected/merged and the owner separately approves activation.

## 22. Protected Governance Evidence

```text
Audit preparation branch: docs/zero-cost-ci-quota
Audit preparation baseline main: db37da2a1a8210fd45d3bf8dcb716d6fbfba7624
Audit preparation baseline tree: 6215ab22dcd0c2daf820168ab2b9d1706be6f650
Audit PR: DEFERRED — ZERO-COST HOSTED CI QUOTA EXHAUSTED
Protected Core Validation: NOT RUN — intentionally avoided to prevent billable usage
Runtime/source/test paths changed by audit preparation: NONE
Phase 4 activation: NO
```

The audit is not canonical/merged until it passes the existing protected governance gate at no additional project-attributable cost.

## 23. Audit Outcome

The existing provider-neutral repository, provisioning, protected-reference, policy, SideEffectGateway and owner-intervention boundaries are sufficient for an additive Phase 4 implementation.

The principal implementation work is a governed GitHub Provider/RepositoryAdapter/VCS handoff composition, not a new Supervisor control plane.

Audit result:

```text
Phase 0: COMPLETE
Phase 1: COMPLETE
Phase 2: COMPLETE
Phase 3: COMPLETE
Phase 4 pre-implementation audit: LOCAL COMPLETE / PROTECTED MERGE DEFERRED
Phase 4 activation: NO
Phase 4 runtime implementation authorized: NO
Phase 5-7: PLANNED / INACTIVE
Hosted GitHub Actions availability for new runs: UNAVAILABLE UNDER ZERO-COST POLICY
```

This document does not activate Phase 4. Runtime changes may begin only after the audit is merged through required protected governance using zero-cost CI capacity, explicit owner approval is recorded, and a separate Phase 4 activation checkpoint is merged.
