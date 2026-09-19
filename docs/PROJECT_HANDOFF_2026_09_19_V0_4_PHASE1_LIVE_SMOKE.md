# PROJECT_HANDOFF_2026_09_19_V0_4_PHASE1_LIVE_SMOKE

Canonical new-chat transition for K_Supervisor ROADMAP v0.4 Phase 1 live-smoke closure.

Version: 1.0
Status: ACTIVE HANDOFF
Date: 2026-09-19

## Current State

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Current main SHA: 907f6466d91624002a9ccaf5e9e1c46aa72ccc66
Current main tree: e97b71a62f2fb846a8af6dbd8c7fffe84d63d888
ROADMAP v0.4: ACTIVE
Phase 0: COMPLETE
Phase 1: ACTIVE — IMPLEMENTED / LIVE SMOKE PENDING
Phase 2-7: PLANNED / INACTIVE
```

The current main commit is documentation/evidence-only after Phase 1 implementation. The authoritative Phase 1 runtime implementation remains:

```text
Implementation PR: #14
Implementation head: 0d6a3ed863c687ec9461135a306180014c248312
Implementation tree: 7fabf5220d4370124bb245445c84f9ed77eb2041
Validated runtime main: 8f748e993737cebe45a6e8ebaac74d8c0e10d1b7
Protected PR Core Validation: 35175344558 — PASS
Merged-main Core Validation: 35175392964 — PASS
Local candidate: 187 passed / 85.02% branch coverage on Python 3.12.3 (non-authoritative)
```

Phase 1 implementation evidence was synchronized through PR #15. Its protected Core Validation run was 35175773647 — PASS and it merged as current main 907f6466d91624002a9ccaf5e9e1c46aa72ccc66.

## Sole Phase 1 Completion Blocker

The owner-controlled live OpenAI Responses smoke is still required. No approved credential was present on the owner host at the last check.

Approved AccessReference:

```text
secret://project/P11/openai
```

EnvironmentSecretBackend key derived from that reference:

```text
KSUP_SECRET__PROJECT_P11_OPENAI
```

The API key must be configured locally on the owner host under that environment key. Do not paste, persist, log, commit or send the raw key through chat.

## Live Smoke Contract

Use the already merged governed `openai.responses` provider path. Do not bypass `ProviderRegistry`, `SideEffectGateway`, policy/approval enforcement or `AccessReference -> SecretBackend` resolution.

The smoke must:
- use an explicitly configured model allowed by the provider profile;
- make one minimal stateless Responses request with `store=false`;
- use the authorized `secret://project/P11/openai` reference;
- produce a non-empty normalized response;
- record only safe response id, effective model, status, request/correlation identifiers and token usage;
- never persist or print the API key, hidden reasoning or private prompt/response content beyond the minimal approved smoke evidence.

If the credential reference is absent, stop and report the blocker. Do not fabricate a successful smoke.

## Mandatory New-Chat Sequence

1. Verify current `main`, protected governance, `PROJECT_STATE.md`, `ROADMAP.md`, `TEST_MATRIX.md`, `V0_4_PHASE1_PREIMPLEMENTATION_AUDIT.md` and `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md`.
2. Check only the presence of `KSUP_SECRET__PROJECT_P11_OPENAI`; do not reveal its value.
3. If present, execute the minimal governed live Responses smoke.
4. If the smoke passes, record safe evidence, mark Phase 1 COMPLETE through a docs-only protected PR, pass required `Core Validation`, merge and verify final `main`.
5. Only after Phase 1 is COMPLETE, perform the mandatory v0.4 Phase 2 — Operator Control API pre-implementation audit.
6. Do not activate or implement Phase 2 runtime before its audit/activation gate is committed through protected governance.

## Canonical References

```text
docs/PROJECT_STATE.md
docs/ROADMAP.md
docs/TEST_MATRIX.md
docs/HARDENING_BASELINE_V0_4.md
docs/V0_4_PHASE1_PREIMPLEMENTATION_AUDIT.md
docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_ACTIVATED.md
docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md
docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md
docs/CHAT_HANDOFF.md
```

Owner-controlled external publication remains unchanged and outside this Phase 1 closure. All v0.4 deferred boundaries remain in force.
