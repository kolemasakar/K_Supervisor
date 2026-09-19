# PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_2_ACTIVATED

Контрольна точка активації ROADMAP v0.4 Phase 2 — Operator Control API.

Version: 1.0
Status: ACTIVE
Roadmap: v0.4
Phase: 2
Date: 2026-09-19
Baseline main: `40636f154f4c58e95d085ca34b3d750f93e2056e`
Baseline tree: `d6fd4e79e44752f941092e7a538ccbc32d27d13c`

## Activation Basis

Phase 0 and Phase 1 are COMPLETE. `V0_4_PHASE2_PREIMPLEMENTATION_AUDIT.md` is COMPLETE and merged through protected PR #22. The owner explicitly approved Phase 2 activation on 2026-09-19.

## Authorized Runtime Scope

Phase 2 authorizes only the audited Operator Control API work:

- additive authenticated `/api/v1` Project onboarding/registration and ProjectSpec submission/approval/activation;
- Human Intervention / Policy Approval read and owner-decision operations;
- Task/Workflow start, status and cancellation through authoritative lower-layer control paths;
- release/readiness/target status and owner publication-confirmation;
- explicit redacted recovery/status projections;
- independent least-privilege scopes;
- restart-safe idempotency and durable service-command receipts;
- normalized error/conflict semantics and safe service telemetry;
- deterministic zero-cost validation.

The required lower-layer prerequisites identified by the audit are part of Phase 2 scope: ProjectSpec status-transition authority, Task/Workflow cancellation authority/state, and additive generic service command receipt support.

## Explicit Non-Scope

- no raw secret retrieval or secret-resolution endpoint;
- no direct Tool/Provider invocation endpoint;
- no administrator-wide multi-tenant RBAC;
- no Phase 3 production host/CLI work;
- no paid development-validation dependency;
- no automatic external publication.

## Permanent Invariants

- existing v0.3 Phase 5 Service/API routes/scopes remain backward-compatible;
- Service/API remains a thin orchestration boundary and must not become a second control plane;
- protected references remain opaque and raw secret material never enters ordinary API state/telemetry/errors;
- nested resources are project-isolated before read or mutation;
- material writes are idempotent and restart-safe;
- no SQLite transaction spans external/provider/runtime work;
- owner publication remains explicit;
- normal protected CI remains deterministic and zero-cost.

## Protected Activation Evidence

```text
Activation PR: #23
Initial activation head: e0b8acfaaf5cbca778de75998917a464a74c8c3d
Initial activation tree: 9144dafa28c1c46db86029173271b332d1b6777d
Core Validation: 35442484760 — PASS
Runtime paths changed: NONE
```

The exact final PR head, including this evidence, must also pass required `Core Validation` before merge.

## Activation State

```text
Owner approval: YES — 2026-09-19
Pre-implementation audit: COMPLETE
Audit PR: #22
Audit final Core Validation: 35441339098 — PASS
Phase 2 runtime implementation authorization: YES — audited scope only
Phase 3-7 runtime implementation authorization: NO
```

This checkpoint must itself pass protected `Core Validation` and merge before any Phase 2 runtime code is committed.
