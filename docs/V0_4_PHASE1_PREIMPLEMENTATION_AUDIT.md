# V0_4_PHASE1_PREIMPLEMENTATION_AUDIT

K_Supervisor ROADMAP v0.4 Phase 1 — Production Model Provider & AI Execution.

Date: 2026-09-16
Status: COMPLETE — implementation may begin after this audit/activation gate is merged
Baseline main SHA: `9eff7d6f31751dfee83ca98a1b9fba6669ba6505`
Baseline main tree: `9e0cce06a27305d3143a01c242501070b67e417d`
Phase 0 checkpoint: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_0_COMPLETE.md`

## 1. Baseline Verification

Phase 0 is complete. PR #11 merged the documentation-only Phase 0 completion tree through protected `main`; Core Validation run `35146876160` passed. The validated runtime predecessor remains `f0c9bc30a5562c83803a861aafe6f669a2ae4730` / tree `85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef`. No runtime path changed during v0.4 Phase 0.

Existing reusable boundaries are present and must be extended rather than bypassed: `Provider` / `ProviderDescriptor` / `ProviderRequest` / `ProviderResponse`, `ModelProfile`, `ProviderRegistry`, `model_candidates()`, `AccessReference` / `SecretBackend`, and the policy/idempotency/audit `SideEffectGateway`.

## 2. Current OpenAI Contract Snapshot

The initial production adapter will target the current OpenAI Responses API documented at `https://developers.openai.com/api/reference/responses/create` (current documentation redirects from the earlier platform.openai.com API docs).

Current contract facts relevant to Phase 1:

- model responses are created with `POST /responses`;
- the request accepts a model identifier and text/input payload;
- responses expose `id`, `model`, `status`, `output`, `output_text` where supported, `error`, `incomplete_details`, and token `usage`;
- `max_output_tokens` is supported;
- `store` defaults to `true` if omitted, so K_Supervisor must explicitly send `store=false` for the Phase 1 stateless path;
- built-in/provider-hosted tools exist, but are outside the Phase 1 trust boundary because their side effects would not traverse K_Supervisor `SideEffectGateway`;
- model identifiers evolve, therefore no particular OpenAI model ID is a platform invariant.

This snapshot is implementation guidance, not a promise that third-party API details are immutable. Adapter behavior must fail closed on unsupported response shapes.

## 3. Gap Inventory

The current runtime has no concrete MODEL provider that performs production inference. `ModelProfile` and `model_candidates()` are metadata-only. `SideEffectGateway` can execute providers after policy enforcement, but generic adapter exceptions are currently collapsed to `SIDE_EFFECT_ADAPTER_ERROR`, which is insufficient for explicit timeout/rate-limit/provider-failure semantics. Secret references exist, but no MODEL adapter resolves one at the final network boundary. No live MODEL smoke procedure exists.

## 4. Approved Implementation Boundary

### 4.1 Provider identity and operation

Add a replaceable MODEL provider with stable provider identity `openai.responses`, provider contract version `1.0`, and operation `generate`. The provider remains an implementation of the generic `Provider` protocol; OpenAI-specific types must not leak into Supervisor core contracts.

### 4.2 Model configuration

Model ID is runtime/project/provider configuration. No specific OpenAI model is hard-coded as a K_Supervisor invariant. `ModelProfile` may expose configured model capabilities and context metadata, but provider selection remains vendor-neutral through existing registry/model-selection hooks.

### 4.3 Credential boundary

The API key is represented only by an `AccessReference` and resolved through an injected `SecretBackend` inside the concrete adapter immediately before transport use. Raw key material must never appear in `ProviderRequest.payload`, persisted Project state, audit, telemetry, exception text, idempotency signatures, or ordinary logs.

The requested credential reference must already be authorized by `SideEffectGateway` through the least-privilege execution context before provider invocation.

### 4.4 Request and storage semantics

Phase 1 supports a bounded stateless text-generation request. The adapter must explicitly set `store=false`. Remote conversations, `previous_response_id`, background responses, provider-hosted tools, MCP/tool execution, file search, web search and computer use are not enabled in Phase 1.

The initial normalized payload may include model, input text, optional instructions and a bounded output-token limit. Unsupported provider-native fields fail validation rather than passing through unchecked.

### 4.5 Response normalization

Normalize successful provider results into provider-neutral output and metadata containing only safe fields needed by the control plane, including generated text, provider response ID, effective model, status, and token usage when returned. Hidden reasoning content is not persisted as product state.

Incomplete/failed provider responses must not be treated as success merely because HTTP transport returned 2xx.

### 4.6 Failure taxonomy

Introduce a safe provider execution error contract that allows the gateway to preserve normalized error code/category/retryability metadata without exposing credentials or raw response bodies. At minimum distinguish configuration/authentication, invalid request, timeout/cancellation, rate limit, transient provider/server failure, malformed response, and non-retryable provider failure.

Existing generic adapters remain backward-compatible: unknown exceptions continue to normalize to the existing generic gateway error.

### 4.7 Timeout, retry and idempotency

Network calls require explicit bounded connect/request timeout. Automatic retries are allowed only for the audited retryable classes and must be bounded. K_Supervisor idempotency remains authoritative at `SideEffectGateway`; retry logic must not cause an already-authoritatively-completed side effect to be repeated.

For HTTP-level retry correlation, reuse the K_Supervisor idempotency/correlation token where the provider transport supports a safe idempotency header. Retry count/backoff are adapter configuration, not hard-coded platform policy.

### 4.8 Dependency strategy

Do not make one vendor SDK a mandatory dependency of every K_Supervisor installation. The OpenAI adapter may use an optional, version-bounded OpenAI client dependency or an injected transport boundary. CI must remain deterministic and credential-free through a fake transport/provider fixture. The implementation must remain testable without live network access.

### 4.9 Governed invocation path

No agent/capability may instantiate the OpenAI client and call it directly. The production path is:

```text
Agent/Capability
  -> AgentRunRequest
  -> PolicyEngine
  -> SideEffectGateway.execute_provider(...)
  -> ProviderRegistry.resolve("openai.responses", ...)
  -> OpenAI Responses adapter
  -> SecretBackend.resolve(authorized AccessReference)
  -> bounded HTTPS transport
```

DENY and REQUIRE_APPROVAL must result in zero provider transport calls.

## 5. Required Phase 1 Verification

Phase 1 implementation must add deterministic tests covering:

- provider availability/config validation and model candidate projection;
- credential missing/present behavior with no plaintext persistence/logging;
- ALLOW invokes once, DENY invokes zero times, REQUIRE_APPROVAL invokes only after valid approval;
- model ID remains configurable/provider-neutral;
- `store=false` and no provider-hosted tools in outbound request;
- successful text/response-id/model/status/usage normalization;
- malformed/incomplete/failed response handling;
- timeout/cancellation/rate-limit/auth/invalid-request/server-failure normalization and retryability;
- bounded retry behavior and idempotency/replay safety;
- deterministic fake transport/provider path in normal CI;
- reference offline providers and all predecessor provider/gateway tests remain green;
- full cumulative regression, branch coverage >=80%, ResourceWarning-as-error, compileall, wheel build/install and public smoke;
- separate owner-controlled live OpenAI Responses smoke before Phase 1 completion.

## 6. Live Smoke Rule

The live smoke is a completion requirement, not an ordinary PR merge requirement. It uses an owner-provided protected reference and explicitly selected model. It must send a minimal stateless `store=false` request, verify a non-empty normalized response and usage/status metadata, and persist only redacted/correlation evidence. Absence of credentials blocks Phase 1 completion but does not block deterministic PR CI.

## 7. Explicitly Deferred from Phase 1

Provider-hosted tools, OpenAI web/file/computer/MCP tool execution, remote conversation state, background mode, multi-provider routing, fine-tuning/training, broad multimodal handling, production-grade bespoke intelligence for every domain agent, and remote-agent federation remain outside Phase 1.

## 8. Activation Decision

The current runtime has sufficient reusable policy, provider, registry and protected-reference boundaries to implement Phase 1 without a core architectural rewrite. The identified gateway error-normalization gap is in-scope and bounded. No blocker requires roadmap revision.

Phase 1 may become ACTIVE once this audit and the accompanying activation checkpoint are merged through protected `main` with `Core Validation` PASS. Runtime implementation must remain within this document, `ROADMAP.md`, `TEST_MATRIX.md`, and `HARDENING_BASELINE_V0_4.md`.
