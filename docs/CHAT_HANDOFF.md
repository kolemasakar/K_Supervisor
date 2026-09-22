# CHAT_HANDOFF
Canonical compact continuation context after ROADMAP v0.4 Phase 3 completion and approval of the self-hosted CI migration.

Version: 5.3
Status: ACTIVE
Date: 2026-09-20

## Start Here

```text
docs/PROJECT_CHECKPOINT_SELF_HOSTED_CI_PREFLIGHT_2026_09_20.md
docs/PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_APPROVED_2026_09_19.md
docs/PROJECT_STATE.md
docs/PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_COMPLETE.md
docs/ROADMAP.md
docs/TEST_MATRIX.md
docs/DEVELOPMENT_RESOURCE_POLICY.md
docs/HARDENING_BASELINE_V0_4.md
docs/V0_4_PHASE3_PREIMPLEMENTATION_AUDIT.md
docs/SERVICE_API.md
```

## Current Roadmap State

```text
ROADMAP v0.2: COMPLETE
ROADMAP v0.3: COMPLETE
ROADMAP v0.4: ACTIVE
v0.4 Phase 0: COMPLETE
v0.4 Phase 1: COMPLETE
v0.4 Phase 2: COMPLETE
v0.4 Phase 3: COMPLETE
v0.4 Phase 4-7: PLANNED / INACTIVE
Current approved implementation phase: NONE
Runtime implementation phase: NONE
Next roadmap work: Phase 4 pre-implementation audit only
```

## Current Validated Runtime Baseline

```text
Phase 3 implementation PR: #29
Final PR head: c73e4c5f24f958ebb1473d4c8d23f28244c9f799
Final PR tree: 0f7b1ecba724623996c7e6e84414c029adcc63c7
Final exact-head Core Validation: 35453258878 — PASS
Merged main: a1791b607496edfaf84593d753f7d1d7662eede1
Merged-main Core Validation: 35453297160 — PASS
Full regression: 229 passed
Branch-aware coverage: 82.06%
Installed-wheel Phase 3 service/CLI smoke: PASS
```

Phase 3 completion authority: `PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_3_COMPLETE.md`.

## Current Repository / Governance Baseline

At CI migration approval:

```text
canonical main: db37da2a1a8210fd45d3bf8dcb716d6fbfba7624
ruleset: main-core-validation
ruleset id: 23556478
required status context: Core Validation
bypass actors: NONE
core workflow: .github/workflows/core-validation.yml
current runs-on: ubuntu-latest
```

The required check name `Core Validation` must not change.

## Self-Hosted CI Migration

Owner approval checkpoint: `PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_APPROVED_2026_09_19.md`.

```text
SELF_HOSTED_RUNNER_PLAN=APPROVED
MIGRATION_EXECUTION=PREFLIGHT_COMPLETE_BOOTSTRAP_PENDING
VM=kgm-e4-owner-pilot
OS=Ubuntu 24.04 ARM64
RUNNER_USER=ghrunner
RUNNER_SCOPE=repository
TARGET_LABELS=self-hosted,linux,arm64,k-supervisor-ci
MANAGEMENT_PATH=existing KGM owner / OCI OIDC / ephemeral Tailscale / Tailscale SSH
SENTINELX_REENROLLMENT=NO
KGMOPS_PRIVILEGE_EXPANSION=NO
WORKFLOW_MUTATION=NO
READ_ONLY_INSPECTION=PASS
VM_PREFLIGHT=PASS
RESOURCE_GUARDRAILS=CPUQuota_70%,MemoryHigh_1G,MemoryMax_1536M,TasksMax_128
PRIVILEGED_BOOTSTRAP=PENDING_OWNER_INTERACTIVE_SESSION
PHASE4_ACTIVATION=NO
```

Owner-observed hosted Actions quota is exhausted (`2000/2000`) until the stated reset date `2026-10-01`; paid Actions usage is denied by owner policy. Do not weaken protected-main governance to bypass the quota.

## Security Boundaries

Normal CI runtime must execute only as `ghrunner`:

- no sudo;
- no docker group;
- no KGM production secret access;
- no OCI credentials;
- no SSH private keys;
- no access to privileged sockets or KGM production-service administration;
- no unrelated repository credentials.

Privileged owner access is bootstrap/systemd administration only.

## Immediate Continuation

1. From the approved interactive owner/bootstrap session, run `sudo /home/kgmops/runner-bootstrap/bootstrap-self-hosted-runner.sh` and enter a fresh short-lived K_Supervisor repository registration token only at the runner prompt.
2. Read-only verify runner registration, `online / idle`, labels, ghrunner isolation, swap, systemd guardrails and KGM service health.
3. Only after runner registration and `online / idle` confirmation may `.github/workflows/core-validation.yml` move to:
   `runs-on: [self-hosted, linux, arm64, k-supervisor-ci]`.
4. Run one controlled `Core Validation` and confirm the existing ruleset accepts the unchanged status context.
5. Record completion evidence in a final migration checkpoint.

Do not activate ROADMAP v0.4 Phase 4 as part of the CI migration.
