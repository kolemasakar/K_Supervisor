# PROJECT_STATE
Канонічний поточний знімок K_Supervisor після завершення ROADMAP v0.3 Phase 4.

Version: 2.5
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
v0.3 Phase 5-8: PLANNED / NOT STARTED
Phase 5 activation in this checkpoint: NO
Phase 17: NOT DEFINED
```

## Current Validated Runtime Baseline

```text
Core Validation run: 35092932820
Implementation SHA: 34049f601fc8116aa12ee15023f1dc20bc25901a
Python: 3.13.15
pytest: 117 passed
branch-aware coverage: 85.13%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
public CLI/import smoke: PASS
```

The validated implementation baseline passed Core Validation run `35092932820` on the candidate branch before `main` was fast-forwarded.

## Phase 3 Completion

ROADMAP v0.3 Phase 3 completed centralized Agent/Workflow Tool/Provider side-effect enforcement:

- `SideEffectGateway` is the standard Tool/Provider execution boundary for material Agent/Workflow side effects;
- policy is re-evaluated immediately before the adapter boundary;
- DENY and REQUIRE_APPROVAL never invoke the external adapter through the standard path;
- least-privilege Tool operations and protected references are enforced before invocation/use;
- project/request/agent/capability and idempotency correlation is propagated to adapters and durable records;
- side-effect attempts and outcomes are durably persisted and audited;
- supported repeated invocations replay authoritative results without unintended duplicate adapter calls;
- idempotency input conflicts fail closed;
- Tool/Provider failures are normalized and auditable;
- side-effect execution state participates in `ProjectRecoverySnapshot`;
- concrete Tool/Provider adapters remain replaceable.

Authoritative records:

- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_3_COMPLETE.md`;
- `PHASE3_PREIMPLEMENTATION_AUDIT.md`;
- `INTEGRATIONS.md`;
- `PERSISTENCE.md`;
- `POLICY_AND_PERMISSIONS.md`;
- `TEST_MATRIX.md`.

SQLite schema remains version 2 because Phase 3 uses the existing generic resources/events storage layout.

## Phase 4 Completion

ROADMAP v0.3 Phase 4 hardened the runtime execution boundary:

- `ProcessRuntimeAdapter` runs each supported isolated invocation in a dedicated worker process;
- parent-side timeout/cancellation owns escalation and bounded cleanup;
- unresponsive workers are terminated rather than being allowed to continue after timeout/cancel return;
- abnormal worker exit is contained and normalized as a runtime worker failure;
- child runtime errors and resource-limit failures preserve normalized `AgentRunResult` semantics;
- a failed/crashed worker does not poison a subsequent run;
- `InProcessRuntimeAdapter` remains available for compatibility and trusted scenarios.

Authoritative Phase 4 records:

- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_4_COMPLETE.md`;
- `PHASE4_PREIMPLEMENTATION_AUDIT.md`;
- `AGENT_RUNTIME.md`;
- `TEST_MATRIX.md`.

## Next Planned Phase

```text
v0.3 Phase 5 - Service/API Boundary
Status: PLANNED / NOT STARTED
```

Phase 5 is not activated by the Phase 4 completion checkpoint. No Phase 5 runtime work is included in the current baseline.

## New-Chat Handoff

Current transition record: `PROJECT_HANDOFF_2026_09_16_PHASE_5.md`.

Decision fixed for the next chat:

- Phase 4 remains COMPLETE on validated runtime SHA `34049f601fc8116aa12ee15023f1dc20bc25901a`;
- Phase 5 remains PLANNED / NOT STARTED until an explicit user instruction activates it;
- before any Phase 5 runtime change, verify current `main`, read the canonical records and complete a Phase 5 pre-implementation audit;
- the Phase 5 audit must preserve the existing control plane and define the versioned Service/API boundary without creating a parallel orchestration path;
- Phase 6-8 work is outside the Phase 5 transition scope.

## Historical Handoff

`PROJECT_HANDOFF_2026_09_16.md` remains the frozen historical start point used to resume and audit Phase 3. Its pre-implementation statements describe the state at handoff and are not the current runtime state.

## Public Compatibility Baseline

```text
Python facade: ksupervisor
CLI: k-supervisor
Config version: 1
Extension groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

`COMPATIBILITY_POLICY.md` remains authoritative. Phase 4 preserved the distribution/CLI/config/entry-point baseline.

## Preserved Architecture Rules

Project remains the top-level managed unit; Agent and Capability remain separate; workflows remain capability-oriented; Supervisor owns orchestration; authoritative state is platform-owned; Human Intervention and owner publication remain explicit; email remains the primary required owner notification transport; protected access remains reference-based; policy/permission checks precede material external Agent/Workflow side effects; K-Research & Critic remains reference-only.

## Remaining Hardening Debt

Completed:

- Phase 1 persistence/resource hygiene;
- Phase 2 durable control state;
- Phase 3 centralized side-effect enforcement;
- Phase 4 runtime isolation and bounded cancellation/termination.

Remaining roadmap work starts only when the next phase is explicitly activated. Phase 5-8 remain PLANNED / NOT STARTED.

Distributed consensus, cross-region event sourcing and universal provider-level exactly-once guarantees remain explicitly deferred rather than hidden Phase 4 failures.

## Validation Rule

The completed v0.2 regression baseline plus completed v0.3 phase tests are cumulative. Runtime implementation phases require successful Core Validation on their committed implementation SHA before completion.
