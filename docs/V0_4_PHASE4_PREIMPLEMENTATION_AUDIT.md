# V0_4_PHASE4_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 4 — GitHub Repository Provider & Governed VCS Handoff.

Version: 1.0
Status: COMPLETE — ACTIVATION PENDING
Date: 2026-09-19
Baseline main: `db37da2a1a8210fd45d3bf8dcb716d6fbfba7624`
Baseline tree: `6215ab22dcd0c2daf820168ab2b9d1706be6f650`
Validated runtime predecessor main: `a1791b607496edfaf84593d753f7d1d7662eede1`
Validated runtime predecessor tree: `0f7b1ecba724623996c7e6e84414c029adcc63c7`
Predecessor phase: v0.4 Phase 3 COMPLETE
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 4 is limited to the approved ROADMAP v0.4 GitHub Repository Provider & Governed VCS Handoff assignment:

- production GitHub repository adapter behind existing Project Factory/provisioning abstractions;
- protected-reference credential resolution with no token persistence in normal state/audit;
- repository resolve/create, visibility/default-branch validation and safe bootstrap application;
- governed branch, commit and pull-request operations for project/release artifacts;
- optional release-tag preparation when explicitly permitted;
- restart/retry reconciliation that avoids duplicate repositories, commits, branches and pull requests;
- normalized GitHub auth/rate-limit/conflict/transient failures with durable correlation/audit;
- owner intervention fallback when remote credentials, permissions or repository policy block automation.

Explicitly out of Phase 4 scope:
- automatic protected-branch merge or administrator bypass;
- repository deletion/rename/transfer;
- changing branch-protection/ruleset policy to make automation succeed;
- GitHub Actions secret/variable administration;
- webhook/event-ingestion infrastructure;
- GitHub App installation/authorization lifecycle management;
- GitLab/Bitbucket production adapters;
- broad cloud/server/database provisioning;
- Plugin-native packaging work (Phase 5);
- mandatory telemetry/exporter infrastructure (Phase 6);
- automatic external publication;
- paid-only development validation.

`DEVELOPMENT_RESOURCE_POLICY.md` remains authoritative: implementation and validation must remain zero-cost.

## 2. Frozen Predecessor and Ancestry

Phase 3 runtime completion is the authoritative predecessor:

```text
Implementation PR: #29
Initial protected Core Validation: 35452558739 — PASS
Final PR head: c73e4c5f24f958ebb1473d4c8d23f28244c9f799
Final PR tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Final exact-head Core Validation: 35453258878 — PASS
Runtime merged main: a1791b607496edfaf84593d753f7d1d7662eede1
Merged-main Core Validation: 35453297160 — PASS
Full regression: 229 passed
Branch-aware coverage: 82.06%
Installed-wheel Phase 3 service/CLI smoke: PASS
```

Current documentation baseline after Phase 3 closure:

```text
main: db37da2a1a8210fd45d3bf8dcb716d6fbfba7624
tree: 6215ab22dcd0c2daf820168ab2b9d1706be6f650
```

The Phase 3 closure after the validated runtime merge is README/docs-only. Therefore `a1791b60...` / tree `0f7b1ecb...` remains the authoritative runtime predecessor for Phase 4.
## 3. Existing Repository and Integration Compatibility Floor

Existing reusable boundaries:

- `RepositoryAdapter` is the Project Factory repository abstraction;
- `FilesystemRepositoryAdapter` proves local repository bootstrap compatibility;
- `ProjectFactory.bootstrap()` owns approved ProjectSpec lifecycle/bootstrap orchestration and owner-blocking fallback;
- `RepositoryProvisioningAdapter` bridges repository creation through the generic provisioning abstraction;
- `ProvisioningRequest` carries protected `AccessReference` values;
- `Provider` / `ProviderRegistry` provide replaceable external provider contracts;
- `SideEffectGateway` is the standard governed Tool/Provider policy, idempotency and audit boundary;
- `ProjectSpec.repository` already rejects plaintext credential-like values;
- `ReleaseManager` consumes repository file evidence and preserves owner-controlled publication.

Phase 4 must extend these boundaries; it must not embed GitHub behavior into Supervisor core, Service/API business semantics or release-state logic.

## 4. Current Gaps

### 4.1 RepositoryAdapter has no remote VCS operation contract

The existing protocol supports only:

```text
prepare(target)
apply_files(repository, files)
list_files(repository)
```

This is sufficient for local filesystem bootstrap but cannot express governed branch creation, commit/ref updates, pull-request handoff or tags.

Phase 4 requires an additive VCS-capable repository abstraction without breaking the existing filesystem adapter.

### 4.2 Generic ProviderProvisioningAdapter is not a valid Phase 4 mutation path

`ProviderProvisioningAdapter.provision()` currently calls `provider.execute()` directly. That historical low-level compatibility adapter predates the centralized production side-effect boundary.

New GitHub network writes must not use this direct path. They require policy/access/idempotency/audit enforcement before external invocation.

### 4.3 Existing SideEffectGateway is AgentRunRequest-shaped

`SideEffectGateway` correctly centralizes Agent/Workflow side effects, but `ProjectFactory` and release VCS handoff are control-plane operations, not agent executions. Phase 4 must not fabricate agent/capability identity merely to satisfy that API.

Implementation therefore requires an additive governed control-plane repository-operation bridge that reuses the same security invariants and durable side-effect semantics without weakening or impersonating the agent path.

### 4.4 No production GitHub transport or normalized error model

There is no production GitHub API adapter, credential resolution, rate-limit normalization, remote-state reconciliation or deterministic fake transport for CI.

### 4.5 No durable remote VCS reconciliation contract

The current repository bootstrap path assumes local synchronous mutation. Remote create/commit/PR operations can have uncertain outcomes after timeouts or process loss and require resolve-before-retry behavior.
## 5. Governed Repository/VCS Boundary Decision

Phase 4 must introduce an additive governed repository/VCS execution boundary. Exact class names may vary, but responsibilities are fixed:

```text
ProjectFactory / ReleaseManager
    -> repository/VCS orchestration abstraction
    -> governed repository operation boundary
        -> ProjectSpec policy + protected-reference authorization
        -> durable idempotency/correlation/audit
        -> GitHub provider adapter
    -> GitHub HTTP transport
```

Rules:

- no new GitHub material mutation may call `Provider.execute()` directly from ProjectFactory, ReleaseManager, provisioning or CLI;
- the control-plane bridge must not construct fake `AgentRunRequest` identities;
- it must preserve the existing policy effects: ALLOW / DENY / REQUIRE_APPROVAL where applicable;
- it must enforce approved side-effect classes and protected references from the active approved ProjectSpec;
- it must create durable attempt/outcome evidence before/after remote material mutation;
- an uncertain remote result remains reconcilable rather than being treated as automatic failure/retry;
- existing Agent/Workflow `SideEffectGateway` behavior remains unchanged.

Implementation may reuse/extend existing durable `SideEffectExecutionRecord` semantics or add a narrowly scoped repository-operation record only if needed for correct reconciliation. Any new durable schema must use the existing generic persistence layout where possible.

## 6. GitHub Provider Contract

The first production repository provider is GitHub. It must remain behind repository/provider abstractions.

Required logical operations:

```text
repository.resolve
repository.create
repository.inspect
files.read
files.apply
branch.resolve
branch.create
commit.create
ref.update
pull_request.resolve
pull_request.create
tag.resolve
tag.create   # optional/policy-gated
```

Not every operation must be exposed publicly; this is the internal adapter capability floor needed for deterministic orchestration and recovery.

Provider behavior:

- use GitHub REST APIs through a replaceable HTTP transport;
- default production API endpoint is the official GitHub API;
- deterministic tests inject a fake transport and never require network credentials;
- no raw response body containing sensitive/private material is persisted;
- provider request metadata remains vendor-neutral above the adapter.

## 7. Protected Credential Contract

ProjectSpec may persist only an opaque repository credential reference, for example:

```text
repository:
  repository_provider: GITHUB
  repository_owner: example-owner
  repository_name: example-repo
  token: secret://project/P123/github
```

Rules:

- `ProjectSpec` validation continues to reject plaintext token/secret fields;
- the GitHub adapter resolves `AccessReference` only at the outbound transport boundary;
- resolved values remain in memory only;
- tokens never appear in request URLs, durable state, telemetry, audit, exception messages or normal logs;
- authentication may use an owner-supplied fine-grained PAT or already-issued GitHub App installation token as opaque bearer material;
- creating/managing GitHub Apps or installation authorization is out of Phase 4 scope;
- missing/invalid credentials fail safely and may open owner intervention where automation is blocked.

## 8. Repository Resolve/Create Semantics

Remote repository identity is deterministic from approved ProjectSpec owner/name/provider.

Required algorithm:

1. resolve `owner/name` first;
2. if found, validate expected repository identity, visibility and other approved invariants before mutation;
3. if not found and provisioning is AUTOMATABLE, create once;
4. after timeout/connection loss during create, resolve `owner/name` before any retry;
5. if an existing repository conflicts with approved identity/policy, fail closed or require owner intervention;
6. never delete, rename or overwrite a conflicting remote repository to recover automatically.

Creation must not weaken organization/repository policy. Visibility is validated against ProjectSpec and cannot be silently broadened.

## 9. Bootstrap File and Commit Semantics

GitHub bootstrap must preserve the existing generated-file conflict guarantees while respecting remote history.

Preferred flow:

```text
resolve repository
resolve target/default branch head
read relevant existing paths
validate no conflicting generated content
construct tree/blob changes
create commit with observed parent
update ref without force
verify resulting paths/content
```

Rules:

- identical desired content is a no-op/replay, not a duplicate commit;
- divergent existing generated paths produce an explicit conflict;
- ref updates are never force-pushed;
- commit parent is the observed remote head;
- concurrent ref movement normalizes as conflict and triggers re-read/reconciliation;
- branch protection/rulesets are never disabled or bypassed.

If direct default-branch update is prohibited, the governed path may prepare a dedicated branch and pull request rather than bypassing protection.

## 10. Branch and Pull-Request Handoff

Branch/PR operations are additive VCS capabilities used for governed project/release handoff.

Requirements:

- deterministic/safe managed branch naming derived from project/spec/release operation identity;
- resolve branch before create; reuse only when its expected managed state matches;
- divergent pre-existing branch produces conflict rather than force reset;
- create commits against an observed branch head with non-force ref updates;
- resolve existing open PR by exact repository/head/base before create;
- timeout after PR create requires resolve-before-retry;
- repeated/restarted execution must not create duplicate PRs for the same logical handoff;
- PR creation does not imply merge authorization;
- protected-branch merge remains an owner/repository-policy action unless a later roadmap explicitly authorizes it.
## 11. Optional Release-Tag Preparation

Phase 4 may prepare a repository tag only when the approved ProjectSpec/release policy explicitly allows it.

Rules:

- tag name is deterministic from the approved release version/profile;
- resolve existing tag/ref before creation;
- an existing tag pointing at the expected commit is an idempotent replay;
- an existing tag pointing elsewhere is a conflict;
- tag creation does not publish a GitHub Release;
- tag deletion/retargeting is not authorized;
- release publication remains a separate owner-controlled boundary.

## 12. Idempotency and Recovery Contract

Remote exactly-once delivery is not claimed. Phase 4 instead requires durable logical-operation identity plus remote-state reconciliation.

Logical identity must bind at least:

```text
project_id
provider
repository owner/name
operation
ProjectSpec/release correlation
idempotency key
canonical semantic input signature
```

Rules:

- the durable attempt is claimed before a material remote request;
- successful result records safe remote identifiers/SHAs/URLs needed for future reconciliation;
- same key + same semantic input reuses/reconciles the prior operation;
- same key + different semantic input fails as idempotency conflict;
- stale PENDING/uncertain operations query authoritative GitHub state before deciding whether to complete, retry or require owner action;
- create-repository, commit/ref, PR and tag recovery each use operation-specific reconciliation;
- blind retry with a new idempotency key is prohibited for an uncertain material mutation.

## 13. Provider Error Normalization

GitHub-specific transport failures must normalize into safe categories without exposing token material:

```text
AUTHENTICATION / AUTHORIZATION
NOT_FOUND
CONFLICT / VALIDATION
RATE_LIMIT
TIMEOUT / NETWORK
TRANSIENT_PROVIDER
INVALID_RESPONSE
NON_RETRYABLE_PROVIDER
```

Expected mapping includes:

- 401 -> authentication;
- 403 -> authorization or rate-limit based on explicit response metadata;
- 404 -> not found where semantically expected;
- 409/422 -> conflict/validation;
- 429 -> rate limit;
- 5xx -> transient provider;
- socket/HTTP timeout -> uncertain transport outcome for material mutations.

Safe metadata may include GitHub request ID, rate-limit reset/retry-after values and remote object IDs/SHAs. Raw authorization headers and sensitive response data are prohibited.

## 14. Owner Intervention and Repository Policy

Existing Human Intervention remains the fallback when automation cannot safely proceed.

Open an owner action when, for example:

- the required protected credential is unavailable;
- GitHub permissions do not allow the approved operation;
- organization/repository policy blocks creation or ref update;
- branch protection requires an owner-controlled review/merge step;
- a pre-existing repository/branch/tag conflicts with approved ProjectSpec intent;
- recovery cannot determine a unique safe remote outcome.

Owner intervention must describe the required external action without embedding credentials. Verifying the owner action does not itself grant hidden provider permissions.

## 15. ProjectFactory / ReleaseManager Compatibility

ProjectFactory remains responsible for project bootstrap lifecycle and generated bootstrap validation. GitHub-specific network details stay below the repository boundary.

ReleaseManager remains responsible for release readiness/publication state. Phase 4 VCS handoff may prepare branch/commit/PR/tag evidence for release artifacts, but:

- it does not merge protected branches automatically;
- it does not publish GitHub Releases;
- it does not convert repository/VCS success into external publication confirmation;
- the existing owner publication boundary remains authoritative.

No new arbitrary GitHub endpoint is added to Service/API or operator CLI in Phase 4. Phase 7 later qualifies the complete operator journey through existing lifecycle surfaces.

## 16. Zero-Cost Validation Plan

Authoritative Phase 4 CI must remain deterministic, credential-free and network-free:

- fake GitHub HTTP transport with scripted responses;
- temporary SQLite;
- deterministic repository/object identifiers and SHAs;
- injected timeout/rate-limit/auth/conflict responses;
- restart/reopen reconciliation fixtures;
- no real GitHub repository required for protected CI.

A live GitHub smoke may be supplemental only when an owner-controlled repository/credential can be used at no additional project-attributable cost. A successful live mutation is not a phase-completion requirement.

## 17. Required Test Families

Planned Phase 4 tests:

```text
tests/test_v04_phase4_github_repository.py
tests/test_v04_phase4_github_vcs.py
tests/test_v04_phase4_github_recovery.py
```

Required deterministic coverage:

- ProjectSpec GitHub target/credential-reference validation and zero plaintext secret leakage;
- provider availability/configuration and safe HTTP request construction;
- resolve existing repository and validate visibility/default branch;
- create-on-not-found only, including create-timeout resolve-before-retry;
- pre-existing conflicting repository fails closed;
- bootstrap file no-op/conflict behavior;
- commit creation against observed parent and non-force ref update;
- concurrent ref movement conflict/reconciliation;
- protected-branch denial cannot trigger force/admin bypass;
- governed branch creation/reuse/conflict semantics;
- PR resolve/create/restart deduplication;
- optional tag idempotency/conflict behavior;
- auth/rate-limit/validation/transient error normalization;
- policy DENY/REQUIRE_APPROVAL performs zero outbound mutation calls;
- protected-reference denial performs zero outbound calls;
- durable attempt/outcome/replay audit contains no token material;
- stale PENDING remote operations reconcile before retry;
- owner intervention fallback for credentials/permissions/policy conflicts;
- FilesystemRepositoryAdapter and predecessor ProjectFactory tests remain compatible;
- release publication remains explicit owner action;
- cumulative regression, branch-aware coverage >=80%, ResourceWarning-as-error, compileall, build/install and public/Phase3 smoke gates remain green.

## 18. Implementation Order Guard

After a separate owner-approved Phase 4 activation checkpoint merges through protected governance, implementation should proceed in this order:

1. GitHub transport/config/error-normalization contracts with deterministic fake transport;
2. additive governed control-plane repository side-effect bridge;
3. protected credential resolution at the transport boundary;
4. repository resolve/create/visibility validation and reconciliation;
5. remote bootstrap file/tree/commit/ref operations;
6. governed branch and pull-request handoff;
7. optional policy-gated tag preparation;
8. owner-intervention and restart/recovery reconciliation;
9. production composition/ProjectFactory/ReleaseManager wiring;
10. full Phase 4 + cumulative validation and documentation.

If implementation would require weakening centralized side-effect enforcement, bypassing repository policy or expanding Service/API with arbitrary GitHub controls, stop and audit that change separately.

## 19. Activation Boundary

This audit authorizes no runtime/source/test implementation.

Required sequence after audit merge:

```text
owner reviews audit
-> explicit Phase 4 activation approval
-> separate docs-only protected activation checkpoint
-> required Core Validation PASS
-> activation checkpoint merge
-> Phase 4 runtime implementation may begin
```

Phase 5-7 remain inactive.

## 20. Protected Audit Governance

```text
Audit PR: PENDING
Initial audit head: PENDING
Initial audit tree: PENDING
Initial Core Validation: PENDING
Final exact-head Core Validation: PENDING
Audit merged main: PENDING
Runtime/source/test paths changed: NONE
```

The audit PR must remain README/docs-only. Its exact final head, including recorded validation evidence, must pass required protected `Core Validation` before merge.

## 21. Audit Outcome

The current architecture can support Phase 4 additively, but production GitHub work requires two missing layers: a VCS-capable repository abstraction and a governed control-plane external-mutation bridge.

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

This document does not activate Phase 4. Runtime changes may begin only after explicit owner approval, a separate Phase 4 activation checkpoint, protected `Core Validation` PASS, and merge to `main`.
