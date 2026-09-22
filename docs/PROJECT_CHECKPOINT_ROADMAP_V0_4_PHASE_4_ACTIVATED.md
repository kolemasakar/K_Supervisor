# PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_4_ACTIVATED

Контрольна точка активації ROADMAP v0.4 Phase 4 — GitHub Repository Provider & Governed VCS Handoff.

Version: 1.0
Status: ACTIVATED — EFFECTIVE ON PROTECTED MERGE
Roadmap: v0.4
Phase: 4
Date: 2026-09-22
Baseline main: 047cea473d69ec3484cb17bbad44f031269bb6e0
Validated runtime predecessor: a1791b607496edfaf84593d753f7d1d7662eede1
Validated runtime predecessor tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7

## Activation Basis

Phase 0, Phase 1, Phase 2 and Phase 3 are COMPLETE.

The Phase 4 pre-implementation audit is COMPLETE and merged through protected PR #34. Canonical audit: `V0_4_PHASE4_PREIMPLEMENTATION_AUDIT.md`.

The audit final head `9ed1e6be7e5ef15e771d18e92a8c8efb75594132` passed protected `Core Validation` run `35738157959` and merged to main as `047cea473d69ec3484cb17bbad44f031269bb6e0`.

The owner directed continuation with `go` on 2026-09-22 after the audit had completed. This checkpoint records that instruction as approval to activate Phase 4 under the already-audited scope only.

## Authorized Runtime Scope

After this checkpoint passes protected `Core Validation` and merges to `main`, Phase 4 authorizes only the work frozen in `V0_4_PHASE4_PREIMPLEMENTATION_AUDIT.md`:

- production GitHub repository adapter behind existing repository / ProjectFactory / provisioning boundaries;
- versioned GitHub REST transport/client with safe error normalization;
- protected-reference credential resolution with no token persistence in ordinary state, logs, telemetry or generated files;
- exact repository owner/name canonicalization, resolve/create and visibility/default-branch validation;
- conflict-safe new/existing repository bootstrap preserving the no-silent-overwrite rule;
- governed branch, commit and pull-request handoff for repository/release artifacts;
- optional policy-permitted tag preparation without automatic tag movement;
- policy / approval enforcement before every material remote write;
- durable idempotency/correlation and restart-safe remote reconciliation;
- normalized auth, permission, rate-limit, conflict, network and provider-unavailable handling;
- Human Intervention fallback for credentials, permissions, organization/repository policy and content conflicts;
- additive supported Service/API and CLI repository operation only if needed by the audited operator boundary;
- production service composition wiring through governed repository orchestration;
- deterministic credential-free zero-cost validation plus optional owner-controlled live GitHub smoke.

## Explicit Non-Scope

- no automatic protected-branch merge;
- no bypass or weakening of branch protection/rulesets;
- no direct Service/API or CLI calls to raw GitHub transport;
- no broad GitHub organization administration;
- no GitLab/Bitbucket production adapters;
- no broad cloud/server/database provisioning;
- no automatic external publication;
- no Phase 5 Plugin-native packaging implementation;
- no Phase 6 supply-chain/telemetry expansion beyond Phase 4 correlation requirements;
- no paid development-validation dependency.

## Permanent Invariants

- the existing FilesystemRepositoryAdapter behavior remains compatible;
- ProjectFactory and ReleaseManager do not receive an ungoverned material network-write path;
- protected access references remain opaque;
- material remote writes are policy/approval gated before provider invocation;
- same idempotency key with a materially different payload is rejected;
- protected-branch/ruleset refusal is surfaced and never bypassed;
- branch/ref updates are non-force;
- merge/publication remains external owner/repository-governance action;
- normal protected CI remains deterministic, credential-free and zero-cost.

## Activation State

```text
Owner approval: YES — 2026-09-22
Pre-implementation audit: COMPLETE
Audit PR: #34
Audit final head: 9ed1e6be7e5ef15e771d18e92a8c8efb75594132
Audit final Core Validation: 35738157959 — PASS
Audit merged main: 047cea473d69ec3484cb17bbad44f031269bb6e0
Phase 4 runtime implementation authorization: YES — audited scope only, effective after this checkpoint merges
Phase 5-7 runtime implementation authorization: NO
Zero-cost development policy: REQUIRED
```

No Phase 4 runtime/source/test code may be committed before this activation checkpoint passes protected governance and merges to `main`.
