# PROJECT_CHECKPOINT_ROADMAP_V0_4_FREE_RESOURCE_AMENDMENT

Owner-approved ROADMAP v0.4 amendment establishing zero-cost development as a permanent project constraint.

Version: 1.0
Status: OWNER-APPROVED — EFFECTIVE ON PROTECTED MERGE
Date: 2026-09-19
Baseline main: 34b30f83e5058fc55d358c72b0fcd5de2d914019

## Decision

All K_Supervisor development must proceed without requiring paid external resources.

Canonical policy: `DEVELOPMENT_RESOURCE_POLICY.md`.

## v0.4 Impact

- the implemented `openai.responses` adapter remains a supported production adapter;
- purchasing OpenAI API credits is not authorized or required for Phase 1 development/closure;
- the successful paid OpenAI live inference requirement is removed as a blocking Phase 1 gate;
- deterministic Phase 1 provider tests and governed real-provider reachability/failure evidence remain valid evidence;
- future phases must choose free/local/free-tier development infrastructure and must provide deterministic substitutes for paid-only external dependencies;
- production/operator deployment may still support paid providers when separately selected and funded by the operator outside the development gate.

## Preserved Invariants

This amendment does not weaken:

- protected credential handling;
- `PolicyEngine -> SideEffectGateway -> ProviderRegistry` enforcement;
- `store=false` for the Phase 1 OpenAI Responses path;
- protected-main PR + `Core Validation`;
- cumulative regression, coverage, ResourceWarning, package-build/install and public-interface gates;
- owner-controlled publication and other existing trust boundaries.

## Governance

This is a docs-only roadmap/policy amendment. Runtime code is unchanged.

```text
Protected PR: #20
Initial policy head: 3b3075a1cd1d9db817636a792e67b1577ff6a4a9
Initial policy tree: 0a1ba620e00fe843aa90990cbc253541a58b4c3f
Core Validation: 35438708291 — PASS
```

The exact final PR head must also pass the required `Core Validation` before merge. Protected merge is the activation event for this amendment.

Phase 1 must be re-evaluated against the amended zero-cost exit criteria after this amendment passes protected governance. Phase 2 remains inactive until Phase 1 is formally closed.
