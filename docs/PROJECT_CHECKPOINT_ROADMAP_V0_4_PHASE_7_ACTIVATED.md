# PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_7_ACTIVATED

Control checkpoint activating ROADMAP v0.4 Phase 7 — End-to-End Single-Node Product Qualification.

Version: 1.0
Status: ACTIVATED — EFFECTIVE ON PROTECTED MERGE
Roadmap: v0.4
Phase: 7
Date: 2026-09-23
Validated runtime predecessor: bbf74fb68690a4f9b802d03fad50071eb50b6aec
Audit merge main: a8167fb119b371cc4a88d56d8a91526df4caeea3

## Activation Basis

ROADMAP v0.4 Phases 0 through 6 are COMPLETE.

The Phase 7 pre-implementation audit is COMPLETE and merged through protected PR #60. Canonical audit: `V0_4_PHASE7_PREIMPLEMENTATION_AUDIT.md`.

Audit validation evidence:

```text
Audit PR: #60
Final audit head: 12da73290c9a31e401601abafd41106498378294
Final Core Validation: 35819849884 — PASS
Audit merge main: a8167fb119b371cc4a88d56d8a91526df4caeea3
Post-merge Supply Chain Attestation: 35820087935 — PASS
Runtime/source/test/workflow paths changed by audit: NONE
```

The owner explicitly approved Phase 7 activation on 2026-09-23 after review of the completed audit.

## Authorized Runtime Scope

After this checkpoint passes protected `Core Validation` and merges to `main`, Phase 7 authorizes only the implementation and qualification scope frozen in `V0_4_PHASE7_PREIMPLEMENTATION_AUDIT.md`:

- **P7-A — production composition gap closure**
  - assemble the existing governed MODEL provider/ModelBackedAgent path inside standard ServiceRuntime;
  - wire the existing ReleaseManager into ServiceRuntime/ServiceApiV1;
  - add only the narrow ProjectFactory repository-context/reconcile boundary needed by release preparation;
  - add an explicit idempotent owner/operator release-preparation API/CLI operation if required by the audit;
  - use additive compatible PlatformConfig v1 fields only where needed for the already-implemented MODEL provider;
  - preserve existing policy, approval, protected-reference and owner-publication contracts;
- **P7-B — deterministic owner/operator E2E**
  - exercise registration/spec approval/activation, repository bootstrap, MODEL Task, FIRST_WORKING, release preparation, Plugin-native packaging and PUBLICATION_REQUIRED through API/CLI;
  - use production OpenAI/GitHub provider classes with deterministic injected transports in protected CI;
- **P7-C — recovery/concurrency qualification**
  - restart/reopen, backup/restore/upgrade, expanded durable-state recovery;
  - two-project owner-wait isolation;
  - deterministic provider/repository/exporter failure handling;
- **P7-D — installed-wheel and cumulative qualification**
  - installed-wheel end-to-end operator smoke;
  - Python 3.13 + 3.14 protected matrix;
  - coverage >=80%, ResourceWarning, compileall, wheel/package, SBOM/vulnerability and governance gates;
- **P7-E — ROADMAP v0.4 closure**
  - synchronize final product/operations docs;
  - create the v0.4/Phase 7 completion checkpoint;
  - close Phase 7 runtime authorization after protected completion merge.

## Explicit Non-Scope

Phase 7 does not authorize:

- distributed worker/service topology or remote-agent federation;
- multi-node/distributed persistence, consensus or cross-region replication;
- multi-tenant SaaS identity/billing;
- broad cloud/server/database provisioning;
- automatic protected-branch merge;
- automatic PyPI, Plugin Directory, GPT Store or marketplace publication;
- provider-account OAuth performed on behalf of the owner;
- mandatory paid MODEL/GitHub/observability/security services;
- mandatory external telemetry collector/SaaS;
- arbitrary untrusted-Python sandboxing;
- bypass of ProjectRegistry, PolicyEngine, SideEffectGateway, ProjectFactory, ReleaseManager or Service/API authority for product operations;
- direct test-only business/control paths created merely to satisfy qualification;
- changes to the owner publication boundary.

## Permanent Invariants

- Operations after production ServiceRuntime startup must traverse supported API/CLI boundaries except fixture/composition setup and evidence inspection explicitly allowed by the audit.
- Production MODEL and GitHub provider implementations remain the code under test; deterministic transport injection is allowed only at their existing/internal composition seams.
- Protected credentials remain opaque `secret://` references until provider boundaries.
- `RELEASE_READY` never means externally published.
- Plugin/package publication remains an explicit owner/workspace action.
- External telemetry failures remain non-authoritative.
- Public API remains additive under `/api/v1`.
- `config_version = 1` remains the compatibility baseline unless a separately approved migration changes it.
- Supported Python target remains 3.13 + 3.14.
- Development/qualification remain subject to `DEVELOPMENT_RESOURCE_POLICY.md`.
- No paid successful provider call is required for Phase 7 completion.

## Activation State

```text
Owner approval: YES — 2026-09-23
Pre-implementation audit: COMPLETE
Audit PR: #60
Audit final head: 12da73290c9a31e401601abafd41106498378294
Audit final Core Validation: 35819849884 — PASS
Audit merge main: a8167fb119b371cc4a88d56d8a91526df4caeea3
Audit merge Supply Chain Attestation: 35820087935 — PASS
Phase 7 runtime implementation authorization: YES — audited scope only, effective after this checkpoint merges
Automatic external publication: FORBIDDEN
Paid qualification dependency: FORBIDDEN
Distributed/multi-tenant scope: NOT AUTHORIZED
NEXT_IMPLEMENTATION_WAVE=P7-A
```

No Phase 7 runtime/source/test/workflow implementation may be committed before this activation checkpoint passes protected governance and merges to `main`.
