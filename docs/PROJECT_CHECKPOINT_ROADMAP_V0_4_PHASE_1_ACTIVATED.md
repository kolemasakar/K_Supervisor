# PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_1_ACTIVATED

Контрольна точка активації ROADMAP v0.4 Phase 1 — Production Model Provider & AI Execution.

Version: 1.0
Status: ACTIVATION CANDIDATE
Roadmap: v0.4
Phase: 1
Date: 2026-09-16
Baseline main: `9eff7d6f31751dfee83ca98a1b9fba6669ba6505`
Baseline tree: `9e0cce06a27305d3143a01c242501070b67e417d`

## Activation Basis

Phase 0 is COMPLETE. `V0_4_PHASE1_PREIMPLEMENTATION_AUDIT.md` verified the current provider, registry, protected-secret, policy and `SideEffectGateway` boundaries and fixed the implementation scope against the current OpenAI Responses API contract.

## Authorized Runtime Scope

Phase 1 authorizes only the bounded production MODEL-provider work defined by the audit and active ROADMAP/TEST_MATRIX: concrete `openai.responses` adapter, protected API-key resolution, provider-neutral model selection, stateless `store=false` text generation, governed gateway invocation, safe response/usage normalization, typed provider-failure semantics, deterministic fake transport tests and a separate owner-controlled live smoke.

Provider-hosted tools, remote conversation state, background mode, multi-provider routing, fine-tuning/training, broad multimodal expansion and any later v0.4 phase are not authorized.

## Permanent Invariants

- policy/approval and access-reference enforcement precede network invocation;
- raw credentials are never durable ordinary state or logs;
- provider/model details remain replaceable behind generic contracts;
- no model ID is a platform invariant;
- provider-hosted tools cannot bypass `SideEffectGateway`;
- normal protected CI is deterministic and credential-free;
- live external smoke is required for Phase 1 completion but is not an ordinary PR merge dependency.

## Activation Gate

This checkpoint becomes ACTIVE only after the audit/activation PR passes protected `Core Validation` and merges to `main`. Until that merge, Phase 1 runtime implementation remains unauthorized.
