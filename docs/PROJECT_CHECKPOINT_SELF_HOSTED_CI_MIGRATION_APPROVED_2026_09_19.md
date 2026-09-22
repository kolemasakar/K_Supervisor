# PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_APPROVED_2026_09_19

Approved operational checkpoint for migrating K_Supervisor Core Validation from GitHub-hosted Actions to a repository-scoped self-hosted runner.

Version: 1.0
Status: APPROVED / NOT EXECUTED
Date: 2026-09-19
Authority: owner-approved CI infrastructure decision

## Purpose

Preserve the existing protected `Core Validation`, pull-request/ruleset governance and quality gates while removing the dependency on GitHub-hosted Actions minutes.

Owner-observed quota condition:

```text
GITHUB_ACTIONS_MINUTES=2000/2000
RESET=2026-10-01
PAID_ACTIONS_USAGE=DENIED
```

The quota observation is owner-provided project evidence. This checkpoint does not claim independent billing-API verification.

## Verified Repository Baseline

At approval time:

```text
repository=kolemasakar/K_Supervisor
canonical_main=db37da2a1a8210fd45d3bf8dcb716d6fbfba7624
workflow=.github/workflows/core-validation.yml
workflow_name=Core Validation
job_name=Core Validation
current_runs_on=ubuntu-latest
ruleset=main-core-validation
ruleset_id=23556478
required_status_context=Core Validation
ruleset_enforcement=active
bypass_actors=NONE
```

The required check name must remain `Core Validation`.

## Approved Target Architecture

```text
VM=kgm-e4-owner-pilot
OS=Ubuntu 24.04 ARM64
runner_user=ghrunner
runner_scope=repository
repository=kolemasakar/K_Supervisor
runner_version_target=v2.337.0 ARM64
concurrency=1
service=systemd
swap_target=2 GiB when preflight proves it is needed
labels=self-hosted,linux,arm64,k-supervisor-ci
runner_directory=/opt/actions-runner/k-supervisor
```

The runner package URL and cryptographic hash must be verified against the official GitHub release before installation. The target version is an approved installation target, not a substitute for release/hash verification.

After migration the workflow target is:

```yaml
runs-on: [self-hosted, linux, arm64, k-supervisor-ci]
```

## Approved Management Path

Do not re-enroll SentinelX on `kgm-e4-owner-pilot` and do not create a new persistent privileged Sentinel channel.

Use the existing KGM owner-management path:

```text
owner / GitHub-controlled management
       ↓
OCI OIDC
       ↓
ephemeral Tailscale
       ↓
Tailscale SSH
       ↓
bounded administrative bootstrap
       ↓
ghrunner system account
```

`kgmops` privileges must not be expanded.

## Runtime Security Boundary

`ghrunner` must be an isolated system account with:

- no `sudo`;
- no membership in `docker`;
- no access to `/home/kgmops`;
- no KGM production secrets;
- no SSH private keys;
- no OCI credentials;
- no production environment files;
- no credentials for unrelated repositories;
- no access to privileged sockets;
- no authority over KGM production services.

The runner directory should be owned by:

```text
ghrunner:ghrunner
```

Any later request for Docker, deployment or another privileged capability requires a separate security review.

## Bootstrap Inspection Gate

Prepared bootstrap path:

```text
/home/kgmops/runner-bootstrap/bootstrap-self-hosted-runner.sh
```

It must not be executed blind. Before mutation, perform read-only inspection covering:

- user/group creation and permissions;
- filesystem ownership and paths;
- systemd unit/service behavior;
- swap changes;
- outbound network assumptions;
- runner download URL;
- package checksum/hash verification;
- token handling;
- any change that could weaken KGM security.

VM preflight must confirm:

- ARM64 architecture;
- CPU/RAM;
- disk and free space;
- current swap;
- systemd availability;
- outbound connectivity required by GitHub Actions;
- absence of unacceptable contention with KGM workload.

## Registration Token Boundary

Repository runner registration token must be:

- obtained immediately before registration;
- single-use/disposable;
- never committed;
- never stored in project files;
- never passed through Sentinel;
- never written into handoff/checkpoint documents;
- never intentionally emitted to logs;
- discarded after successful registration.

Prefer an ephemeral mechanism that avoids persistence and unnecessary process/log exposure. Use only mechanisms supported by the official runner tooling.

## Resource Guardrails

Before the first controlled `Core Validation`, the runner systemd service must receive resource guardrails derived from actual VM preflight.

Required guardrail classes:

```text
MemoryMax=REQUIRED
CPUQuota=REQUIRED
TasksMax=REQUIRED
MemoryHigh=RECOMMENDED_WHEN_APPROPRIATE
```

Exact values are intentionally not frozen here. They must be selected after measuring the VM and existing KGM workload so that CI cannot materially displace production workload.

## Execution Order

1. Read-only inspect `bootstrap-self-hosted-runner.sh`.
2. Perform VM resource/network/systemd/architecture preflight.
3. Confirm no unacceptable KGM workload conflict.
4. Create `ghrunner`.
5. Prepare `/opt/actions-runner/k-supervisor`.
6. Download and verify the official GitHub Actions Runner ARM64 package.
7. Add 2 GiB swap only if preflight shows it is appropriate and needed.
8. Register the runner repository-scoped to `kolemasakar/K_Supervisor`.
9. Install/start the systemd service.
10. Apply and verify systemd resource guardrails.
11. Confirm through GitHub that the runner is online, idle and correctly labelled.
12. Only then change `.github/workflows/core-validation.yml` `runs-on`.
13. Execute one controlled `Core Validation`.
14. Confirm the ruleset is still satisfied by the unchanged `Core Validation` context.
15. Record final migration evidence in a completion checkpoint.

No test transition through a GitHub-hosted runner is required or authorized while the quota is exhausted.

## Acceptance Criteria

Migration is complete only when:

```text
RUNNER_REGISTERED=PASS
RUNNER_ONLINE=PASS
RUNNER_IDLE_BEFORE_TEST=PASS
REPOSITORY_SCOPE=K_Supervisor_ONLY

GHRUNNER_SUDO=NO
GHRUNNER_DOCKER_AUTHORITY=NO
KGM_PRODUCTION_SECRET_ACCESS=NO
KGMOPS_PRIVILEGE_EXPANSION=NO

SYSTEMD_MEMORY_GUARDRAIL=PASS
SYSTEMD_CPU_GUARDRAIL=PASS
SYSTEMD_TASKS_GUARDRAIL=PASS

CORE_VALIDATION_SELF_HOSTED=PASS
REQUIRED_CHECK_NAME_UNCHANGED=PASS
RULESET_GOVERNANCE=PASS

GITHUB_HOSTED_MINUTES_USED=0
KGM_PRODUCTION_IMPACT=NONE
```

## Rollback

Before workflow mutation, preserve the current runner selector:

```text
runs-on: ubuntu-latest
```

If self-hosted validation fails:

1. restore the workflow to the previous runner selector;
2. stop the self-hosted runner service;
3. do not remove or modify unrelated KGM production components;
4. preserve failure evidence;
5. do not activate ROADMAP v0.4 Phase 4 as a consequence of this migration.

## Current State

```text
SELF_HOSTED_RUNNER_PLAN=APPROVED
MIGRATION_EXECUTION=NOT_STARTED
WORKFLOW_MUTATION=NO
MANAGEMENT_PATH=EXISTING_KGM_OWNER_PATH
SENTINELX_REENROLLMENT=NO
KGMOPS_PRIVILEGE_EXPANSION=NO
RUNNER_USER=ghrunner
PRIVILEGED_BOOTSTRAP=BOUNDED
RESOURCE_GUARDRAILS=REQUIRED_BEFORE_CONTROLLED_CI
PHASE4_ACTIVATION=NO
NEXT_ACTION=READ_ONLY_BOOTSTRAP_INSPECTION_AND_VM_PREFLIGHT
```
