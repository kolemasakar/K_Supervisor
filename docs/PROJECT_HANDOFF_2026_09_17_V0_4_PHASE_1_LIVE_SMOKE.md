# PROJECT_HANDOFF_2026_09_17_V0_4_PHASE_1_LIVE_SMOKE
Canonical new-chat transition for K_Supervisor at the ROADMAP v0.4 Phase 1 live-smoke gate.

Version: 1.0
Status: ACTIVE HANDOFF
Date: 2026-09-17

## Current Repository Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Current main SHA: 907f6466d91624002a9ccaf5e9e1c46aa72ccc66
Current main tree: e97b71a62f2fb846a8af6dbd8c7fffe84d63d888
ROADMAP v0.4: ACTIVE
Phase 0: COMPLETE
Phase 1: ACTIVE — IMPLEMENTED / LIVE SMOKE PENDING
Phase 2-7: INACTIVE / PLANNED
```

The Phase 1 runtime implementation was merged through PR #14. The implementation tree is `7fabf5220d4370124bb245445c84f9ed77eb2041` and merged-main runtime SHA is `8f748e993737cebe45a6e8ebaac74d8c0e10d1b7`.

Protected validation evidence:

```text
PR #14 Core Validation: 35175344558 — PASS
Merged-main Core Validation: 35175392964 — PASS
Phase 1 evidence PR #15 Core Validation: 35175773647 — PASS
Phase 1 evidence PR #15 merged main: 907f6466d91624002a9ccaf5e9e1c46aa72ccc66
```

## Phase 1 Implemented Boundary

Production provider identity: `openai.responses`, contract version `1.0`, operation `generate`.

The implementation:
- resolves credentials only through `AccessReference` + injected `SecretBackend`;
- uses stateless Responses requests with explicit `store=false`;
- keeps provider/model selection configurable and does not hard-code a platform-wide model;
- normalizes response identity, model, status and usage without persisting hidden reasoning;
- routes governed invocation through the existing policy / SideEffectGateway boundary;
- keeps ordinary CI deterministic and credential-free.

Canonical implementation evidence: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_IMPLEMENTED.md`.
Canonical audit: `V0_4_PHASE1_PREIMPLEMENTATION_AUDIT.md`.

## Sole Phase 1 Completion Blocker

The required owner-controlled live OpenAI Responses smoke has not yet run because the owner host has no configured protected OpenAI credential reference.

Approved audit reference:

```text
AccessReference: secret://project/P11/openai
EnvironmentSecretBackend key: KSUP_SECRET__PROJECT_P11_OPENAI
```

Do not place the API key in chat, Git, ordinary project state, logs, audit bodies or documentation. The owner must inject it locally on the authorized host/runtime environment.

## New-Chat Execution Order

1. Verify current `main`, `PROJECT_STATE.md`, `ROADMAP.md`, `TEST_MATRIX.md`, the Phase 1 audit and implementation checkpoint.
2. Verify only the **presence** of `KSUP_SECRET__PROJECT_P11_OPENAI`; never print or read the value into chat output.
3. If absent, stop before any live call and give the owner an exact local injection procedure using a placeholder value.
4. If present, choose an explicitly approved/configured model and run one minimal governed `openai.responses` inference through the merged provider path.
5. The live request must remain stateless with `store=false`, use the protected reference, and avoid provider-hosted tools/background state.
6. Record only safe evidence: response id, effective model, completion status, token usage, request/correlation identifiers and PASS/FAIL. Do not record response private content unless required; never record credential material or hidden reasoning.
7. If the smoke passes, create a docs-only Phase 1 completion checkpoint, update canonical state to `Phase 1 COMPLETE`, run protected `Core Validation`, merge, and verify `main`.
8. Only after Phase 1 completion, perform the mandatory v0.4 Phase 2 pre-implementation audit. Do not start Phase 2 runtime implementation before its audit/activation gate is merged through protected governance.

## Scope Guard

Do not reinterpret the missing live credential as permission to bypass `SecretBackend`, call the OpenAI SDK/API directly from Supervisor core, hard-code a model, fabricate live evidence, or activate Phase 2 early.

External publication remains owner-controlled. Distributed/multi-tenant and other v0.4 deferred scope remains unchanged.

## Starter Prompt for the New Chat

> Продовжуємо K_Supervisor з `docs/PROJECT_HANDOFF_2026_09_17_V0_4_PHASE_1_LIVE_SMOKE.md`. Звір current `main` і canonical Phase 1 evidence. Спочатку перевір лише наявність protected env reference `KSUP_SECRET__PROJECT_P11_OPENAI` на owner host, не виводячи значення. Якщо reference відсутній — дай точну локальну команду/процедуру з placeholder і зупини live call. Якщо присутній — виконай мінімальний owner-controlled governed OpenAI Responses smoke через merged `openai.responses` provider з `store=false`, запиши тільки safe evidence, після PASS закрий v0.4 Phase 1 через protected PR/CI. Потім виконай Phase 2 pre-implementation audit; не починай Phase 2 runtime до audit/activation merge.
