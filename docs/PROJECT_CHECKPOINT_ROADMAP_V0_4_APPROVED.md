# PROJECT_CHECKPOINT_ROADMAP_V0_4_APPROVED
Контрольна точка затвердження ROADMAP v0.4.

Version: 1.0
Status: APPROVED
Roadmap: v0.4
Date: 2026-09-16
Current phase: v0.4 Phase 0

## Decision

ROADMAP v0.4 — Single-Node Operator Productization is explicitly approved. Revision-local numbering is `v0.4 Phase 0` through `v0.4 Phase 7`; this approval does not create a v0.3 Phase 9.

## Program Objective

Move K_Supervisor from the validated PRE-ALPHA local-first baseline into an owner-operable, production-deployable single-node product boundary with governed production model inference, supported operator API/CLI, a real GitHub repository path, Plugin-native release packaging, and stronger telemetry/supply-chain evidence.

## Approved Phase Sequence

```text
v0.4 Phase 0  Baseline Freeze & Operator Product Contract
v0.4 Phase 1  Production Model Provider & AI Execution
v0.4 Phase 2  Operator Control API
v0.4 Phase 3  Production Single-Node Service Host & Operator CLI
v0.4 Phase 4  GitHub Repository Provider & Governed VCS Handoff
v0.4 Phase 5  Plugin-Native ChatGPT/Codex Release Packaging
v0.4 Phase 6  Production Telemetry & Supply-Chain Hardening
v0.4 Phase 7  End-to-End Single-Node Product Qualification
```

## Predecessor Runtime Baseline

```text
Validated runtime main: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Runtime tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Implementation commit: f0c9bc30a5562c83803a861aafe6f669a2ae4730
Protected PR Core Validation: 35134961231 — PASS
Merged-main Core Validation: 35135133947 — PASS
Python workflow: 3.13
Local exact-tree regression: 163 passed / 85.82% branch coverage
```

Current pre-activation main is `19847c9415f5311add7da787aa5a2ebe0807050b` with tree `568c98d790ae996212c4505446e503bd2cd4f7f5`; changes after the validated runtime baseline are documentation-only.

## Preserved Boundaries

ProjectSpec remains material-scope authority; Supervisor remains orchestration authority; policy/approval precedes side effects; protected secrets remain opaque references; email remains the required executable owner-notification transport; `RELEASE_READY != publication`; publication remains owner/workspace controlled; existing `/api/v1`, package, CLI, config and extension compatibility remain governed unless explicitly versioned.

## Deferred Program Scope

Distributed execution/federation, distributed databases/consensus, multi-tenant SaaS, non-email transports, universal arbitrary-Python sandboxing, mandatory event-bus infrastructure, broad cloud provisioning, certificate lifecycle automation, and automatic external publication are not part of approved v0.4.

## Current Authorization

Only v0.4 Phase 0 is ACTIVE. It authorizes documentation/baseline/hardening-contract work and no runtime implementation. Runtime work begins only after Phase 0 completion plus the next phase's pre-implementation audit and activation gate.
