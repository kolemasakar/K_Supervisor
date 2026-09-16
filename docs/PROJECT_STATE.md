# PROJECT_STATE
Канонічний поточний знімок K_Supervisor після завершення ROADMAP v0.3 Phase 5.

Version: 2.6
Status: ACTIVE
Date: 2026-09-16

## Current Baseline

```text
Repository: kolemasakar/K_Supervisor
Branch: main
Product status: PRE-ALPHA
Package: k-supervisor==0.1.0
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0: COMPLETE
v0.3 Phase 1: COMPLETE
v0.3 Phase 2: COMPLETE
v0.3 Phase 3: COMPLETE
v0.3 Phase 4: COMPLETE
v0.3 Phase 5: COMPLETE
v0.3 Phase 6-8: PLANNED / NOT STARTED
Phase 6 activation in this checkpoint: NO
Phase 17: NOT DEFINED
```

## Current Validated Runtime Baseline

```text
Core Validation run: 35103131762
Implementation SHA: 0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841
Python workflow: 3.13
pytest: 129 passed
branch-aware coverage: 85.34%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples/service_api: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

The final Phase 5 implementation SHA passed GitHub Core Validation. Documentation-only closure commits do not replace this runtime baseline.

## Phase 5 Completion

ROADMAP v0.3 Phase 5 established the Service/API boundary without bypassing the Project Control Plane:

- `ServiceApiV1` is the transport-neutral v1 service core;
- `WsgiServiceAppV1` is the thin HTTP/WSGI adapter;
- Project list/get and lifecycle/operational transition operations are exposed under `/api/v1`;
- mutations delegate to `ProjectRegistry` and existing state models;
- authentication is injected and Bearer support is host-configured;
- read/lifecycle-write/operational-write scopes are independent;
- Project read responses do not expose ProjectSpec protected configuration;
- every mutation requires an idempotency key;
- `ServiceMutationRecord` provides durable restart-safe replay;
- transition + transition audit + service receipt share one persistence transaction;
- duplicate replay and conflicting replay semantics are explicitly tested.

Authoritative Phase 5 records:

- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_5_COMPLETE.md`;
- `PHASE5_PREIMPLEMENTATION_AUDIT.md`;
- `SERVICE_API.md`;
- `PLATFORM_INTERFACES.md`;
- `PERSISTENCE.md`;
- `TEST_MATRIX.md`.

SQLite physical schema remains version `2`; the service receipt uses the generic resources/events storage layout.

## Preserved Completed Hardening

- Phase 1 persistence/resource hygiene remains authoritative.
- Phase 2 durable control state remains authoritative.
- Phase 3 centralized side-effect enforcement remains authoritative.
- Phase 4 runtime isolation/cancellation remains authoritative.
- Phase 5 does not alter ProjectSpec approval, Human Intervention, owner publication, SideEffectGateway or RuntimeAdapter semantics.

## Next Planned Phase

```text
v0.3 Phase 6 - Production Observability
Status: PLANNED / NOT STARTED
```

Phase 6 is not activated by the Phase 5 completion checkpoint. No Phase 6 runtime work is included in the current baseline.

## New-Chat Handoff

Current transition record: `PROJECT_HANDOFF_2026_09_16_PHASE_6.md`.

Decision fixed for the next chat:

- Phase 5 remains COMPLETE on validated runtime SHA `0c92ae8328c99bc3219a51b16c5e5fb7ef3c3841`;
- Phase 6 remains PLANNED / NOT STARTED until explicit activation;
- before Phase 6 runtime changes, verify current `main` and complete a Phase 6 pre-implementation audit;
- Phase 6 must address only its observability assignment and preserve the completed Service/API boundary;
- Phase 7-8 work remains outside Phase 6 scope.

## Public Compatibility Baseline

```text
Python facade: ksupervisor
Service facade: ksupervisor.service
Service API: /api/v1
CLI: k-supervisor
Config version: 1
Extension groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

`COMPATIBILITY_POLICY.md` remains authoritative.

## Validation Rule

The completed v0.2 regression baseline plus completed v0.3 phase tests are cumulative. Runtime implementation phases require successful Core Validation on their committed implementation SHA before completion.
