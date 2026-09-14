# CHAT_HANDOFF
Канонічний контекст для продовження роботи над K_Supervisor у новому чаті.

Version: 1.4
Status: ACTIVE
Date: 2026-09-14

## Start Here

Before changing runtime code in a new conversation, read from `main`:

```text
docs/PROJECT_STATE.md
docs/ROADMAP.md
docs/HARDENING_BASELINE_V0_3.md
docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md
docs/PERSISTENCE.md
docs/AGENT_RUNTIME.md
docs/POLICY_AND_PERMISSIONS.md
docs/TEST_MATRIX.md
docs/COMPATIBILITY_POLICY.md
docs/ROADMAP_IMPLEMENTATION_AUDIT.md
```

Repository:

```text
kolemasakar/K_Supervisor
branch: main
product maturity: PRE-ALPHA
package: k-supervisor==0.1.0
```

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: ACTIVE
v0.3 Phase 0: COMPLETE
v0.3 Phase 1 - Persistence & Resource Hygiene: COMPLETE
v0.3 Phase 2 - Durable Control State: COMPLETE
Current approved phase: v0.3 Phase 3 - Centralized Side-Effect Enforcement
v0.3 Phase 3: ACTIVE
v0.3 Phase 4-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

Work proceeds under revision-local v0.3 phase numbering.

## Current Runtime Baseline

The authoritative validated runtime baseline is:

```text
Implementation SHA: 573cbe433ece8ffae45d83a30fd3287fac40d820
Core Validation run: 34808287772
Python: 3.13.15
pytest: 103 passed
branch-aware coverage: 85.23%
coverage gate: >= 80% PASS
ResourceWarning gate: PASS
compileall including examples: PASS
wheel build/install: PASS
k-supervisor CLI outside checkout: PASS
import ksupervisor outside checkout: PASS
```

Documentation synchronization after this SHA does not replace the runtime baseline unless a later implementation checkpoint explicitly states otherwise.

## Completed Phase 2

Phase 2 delivered:

- persistence-backed runtime idempotency on the standard AgentRuntimeDispatcher path;
- project-scoped restart-safe successful-result replay and concurrent claim protection;
- durable notification delivery history verified for duplicate suppression after restart;
- ApprovalRecord states `EXPIRED` and `REVOKED`, with explicit timestamps/reason and policy enforcement;
- durable approval lifecycle audit;
- expanded ProjectRecoverySnapshot for human actions, notification/delivery state, approvals, runtime idempotency, policy, audit, routing and release-validation records;
- atomic state+audit persistence for core Project, Human Intervention and Approval control mutations;
- verified interrupted Task/WorkflowRun + WAITING_FOR_OWNER reconstruction and resume after restart;
- SQLite schema remains version 2 because Phase 2 uses the generic resources/events layout.

Authoritative records:

- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_2_COMPLETE.md`;
- `PERSISTENCE.md`;
- `AGENT_RUNTIME.md`;
- `POLICY_AND_PERMISSIONS.md`.

## Active Phase 3

Goal: centralize material external side effects behind one enforceable platform gateway.

Required work includes:

- Tool Gateway / side-effect execution gateway for standard production paths;
- normalized side-effect invocation/result contract;
- policy and tool-operation permission validation before invocation;
- protected-reference authorization before resolution/use;
- correlation and idempotency propagation;
- normalized durable side-effect attempt/outcome audit;
- no external invocation for DENY or REQUIRE_APPROVAL;
- replaceable concrete tool/provider adapters.

Required verification includes ALLOW/DENY/REQUIRE_APPROVAL invocation behavior, tool permissions, protected references, repeated invocation/idempotency, failure normalization/audit, correlation persistence and the full cumulative regression suite.

## Preserved Architecture

- Project is the top-level managed unit; Project != Task.
- Agent != Capability.
- ProjectSpec approval gates material project scope.
- workflows remain capability-oriented.
- Supervisor owns routing/orchestration boundaries.
- persistence is platform-owned; hidden conversational memory is not authoritative state.
- owner-required actions use Human Intervention.
- notification delivery does not mean owner action completed.
- email remains the primary required notification transport.
- protected access data is represented through protected references.
- policy/permission checks precede material external actions.
- external publication remains an explicit owner action.
- K-Research & Critic v1.0.0 is reference-only.

## Public Compatibility Baseline

```text
Python facade: ksupervisor
CLI: k-supervisor
Config version: 1
Entry-point groups:
  k_supervisor.agents
  k_supervisor.capabilities
  k_supervisor.project_templates
  k_supervisor.adapters
```

`COMPATIBILITY_POLICY.md` remains authoritative.

## Working Rule

Implement only the active roadmap phase. Do not mark Phase 3 complete until the committed implementation passes all published Phase 3 verification and permanent Core Validation gates. After completion, synchronize README, PROJECT_STATE, ROADMAP status, TEST_MATRIX, DOCS_INDEX, CHAT_HANDOFF, affected technical contracts and the phase checkpoint.
