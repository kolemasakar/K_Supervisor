# CHAT_HANDOFF
Канонічний контекст для продовження роботи над K_Supervisor у новому чаті.

Version: 1.2
Status: ACTIVE
Date: 2026-09-14

## Start Here

Before changing runtime code in a new conversation, read from `main`:

```text
docs/PROJECT_STATE.md
docs/ROADMAP.md
docs/HARDENING_BASELINE_V0_3.md
docs/PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md
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
Current approved phase: v0.3 Phase 1 - Persistence & Resource Hygiene
v0.3 Phase 1: ACTIVE
v0.3 Phase 2-8: PLANNED / NOT STARTED
Phase 17: NOT DEFINED
```

Do not use an invented Phase 17. Work proceeds under revision-local v0.3 phase numbering.

## Current Runtime Baseline

No runtime implementation change was introduced in v0.3 Phase 0. Until Phase 1 creates a new validated implementation checkpoint, the authoritative runtime baseline is:

```text
Implementation SHA: 755be348fc3376ad5c09f178a3268b0fb7685107
Core Validation run: 34793901147
Python: 3.13.15
pytest: 88 passed
branch-aware coverage: 85.46%
coverage gate: >= 80% PASS
compileall including examples: PASS
wheel build/install: PASS
k-supervisor CLI outside checkout: PASS
import ksupervisor outside checkout: PASS
```

## Phase 0 Result

Phase 0 froze the predecessor runtime/compatibility baseline, classified all known technical debt, defined migration/rollback expectations and hardening invariants, and established cumulative v0.3 validation rules.

Authoritative Phase 0 records:

- `HARDENING_BASELINE_V0_3.md`;
- `PROJECT_CHECKPOINT_ROADMAP_V0_3_PHASE_0_COMPLETE.md`.

## Active Phase 1

Goal: make persistence/resource ownership reliable for long-running execution while preserving the storage abstraction.

Required work includes:

- explicit storage connection lifecycle/ownership;
- transaction boundary hardening;
- persistent schema version/migration mechanism;
- storage abstractions independent of SQLite physical layout;
- elimination of known SQLite ResourceWarning leaks;
- deterministic reopen/restart recovery;
- documented storage replacement boundary.

Required verification includes lifecycle/reopen/restart, migration, rollback, supported concurrency, zero known SQLite ResourceWarning leaks, all v0.2 regression tests and successful Core Validation on the committed Phase 1 implementation SHA.

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

Implement only the active roadmap phase. Do not mark Phase 1 complete until the committed implementation passes all published Phase 1 verification and permanent Core Validation gates. After completion, synchronize README, PROJECT_STATE, ROADMAP status, TEST_MATRIX, DOCS_INDEX, CHAT_HANDOFF and the phase checkpoint.
