# HARDENING_BASELINE_V0_4
Frozen predecessor and productization contract for ROADMAP v0.4.

Version: 1.0
Status: ACTIVE
Roadmap: v0.4
Phase: 0
Date: 2026-09-16

## 1. Frozen Predecessor Runtime

```text
Implementation commit: f0c9bc30a5562c83803a861aafe6f669a2ae4730
Implementation tree: 85ffccfe4f2254d0f4d4ce3d64eec3e6f33976ef
Validated runtime main: 641b95ed6cd29b629af9b86e6826eab7fa9bb742
Protected PR Core Validation: 35134961231 — PASS
Merged-main Core Validation: 35135133947 — PASS
Python workflow: 3.13
Local exact-tree regression: 163 passed / 85.82% branch coverage
SQLite physical schema: 2
```

The pre-activation documentation main is `19847c9415f5311add7da787aa5a2ebe0807050b` / tree `568c98d790ae996212c4505446e503bd2cd4f7f5`. The validated runtime commit is its ancestor and no runtime path changed after that baseline.

## 2. Permanent Compatibility Baseline

- Python facade: `ksupervisor`.
- CLI: `k-supervisor`.
- Service API: `/api/v1`, additive compatible evolution by default.
- Config version: `1`.
- Stable extension groups: `k_supervisor.agents`, `k_supervisor.capabilities`, `k_supervisor.project_templates`, `k_supervisor.adapters`.
- Preferred ChatGPT target: `CHATGPT_PLUGIN`; legacy persisted `GPT_STORE` remains readable/resumable.
- ProjectSpec/Supervisor/policy/Human Intervention authority boundaries remain unchanged unless a later explicit migration revises them.
- `RELEASE_READY` never implies external publication.

## 3. Supported v0.4 Product Topology

v0.4 targets one owner-operated single-node K_Supervisor service with one authoritative local SQLite store, process-isolated/local execution, external model/repository providers behind governed adapters, and TLS termination permitted at a documented external reverse proxy. Horizontal service clustering, remote worker federation and distributed persistence are not implied.

## 4. Phase Debt Assignment

```text
Phase 1  concrete production MODEL provider + governed AI execution
Phase 2  complete owner/operator control operations through Service API v1
Phase 3  supported long-running single-node host + operator CLI
Phase 4  production GitHub repository/VCS adapter and governed handoff
Phase 5  current Plugin-native package/manifest/marketplace validation
Phase 6  concrete telemetry adapters + supply-chain evidence
Phase 7  complete end-to-end single-node product qualification
```

## 5. Security and Control Invariants

- Raw provider/repository credentials are never stored in ordinary Project, audit, telemetry, notification or release records.
- Material external operations traverse policy/permission/approval enforcement before invocation.
- External-provider retries require explicit idempotency/correlation semantics and may not silently duplicate material effects.
- Hidden chain-of-thought is not persisted as product state.
- Failure of optional telemetry/exporter infrastructure cannot corrupt authoritative control state.
- Owner-required publication/availability actions remain explicit and resumable.
- Protected `main` PR + `Core Validation` remains the minimum repository merge gate.

## 6. Live External Evidence Rule

Normal protected CI remains deterministic and credential-free. Where an approved phase introduces a production external adapter, an owner-controlled live smoke may be required for phase completion but is not an ordinary PR merge dependency. Missing required live evidence blocks the phase completion claim, not unrelated CI validation.

## 7. Explicitly Deferred Beyond v0.4

Distributed worker clusters, remote-agent federation, distributed database/consensus/cross-region replication, multi-tenant SaaS identity/billing, WhatsApp/Viber/SMS/social notification transports, universal arbitrary-Python sandboxing, mandatory event-bus architecture, broad cloud/server/database provisioning, mandatory external vault products, certificate issuance/renewal automation, automatic PyPI/Plugin Directory/GPT Store publication, and autonomous scope expansion beyond approved ProjectSpec/roadmap authority remain deferred.

## 8. Migration and Rollback Contract

Persistent schema/config/public-contract changes must be versioned, backward-compatible where promised, and rollback/recovery tested. Unsupported future versions fail closed rather than being guessed. Any schema change must preserve backup/restore/upgrade qualification introduced in v0.3.

## 9. Permanent Validation Floor

Completed v0.2 and v0.3 tests remain cumulative. Runtime phases must pass branch-aware coverage >=80%, ResourceWarning-as-error, compileall including examples, isolated wheel build/install, public package/CLI smoke, phase-specific restart/recovery and failure injection, and protected `Core Validation`.

## 10. Phase 0 Exit Contract

Phase 0 completes only when current-main ancestry is verified, all audited product gaps are assigned or deferred, this contract plus approved ROADMAP/TEST_MATRIX state is merged through protected `main`, no runtime path changed, and the activation PR passes `Core Validation`.
