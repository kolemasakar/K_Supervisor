# SELF_HOSTED_CI_RUNNER_DECISION

Approved infrastructure decision for K_Supervisor protected CI.

Version: 1.1
Status: APPROVED — MIGRATION PENDING
Date: 2026-09-19
Owner approval: YES
Baseline main: `db37da2a1a8210fd45d3bf8dcb716d6fbfba7624`
Baseline tree: `6215ab22dcd0c2daf820168ab2b9d1706be6f650`

## Decision

K_Supervisor will migrate the protected `Core Validation` job from GitHub-hosted `ubuntu-latest` compute to one repository-scoped self-hosted runner on the existing owner-controlled VM `kgm-e4-owner-pilot`.

The migration changes the execution location only. It does not weaken repository governance:

```text
Pull Request
  -> GitHub Actions orchestration
  -> repository-scoped self-hosted runner
  -> Core Validation
  -> required check
  -> protected merge
```

The required check name remains exactly `Core Validation`. Pull-request review/ruleset requirements remain unchanged.

## Motivation

The project has a permanent zero-cost development requirement. On 2026-09-19 the owner reported the included GitHub-hosted Actions usage at `2,000 / 2,000` minutes, with further hosted usage potentially billable.

The project already owns an always-available VM. Running protected CI on that owner-controlled resource removes GitHub-hosted compute minutes as a development dependency while preserving GitHub Actions orchestration and protected-main governance.

## Assessed VM

```text
Host: kgm-e4-owner-pilot
OS: Ubuntu 24.04.4 LTS
Kernel architecture: aarch64 / ARM64
CPU: 1 vCPU, Neoverse-N1
RAM: 5.8 GiB total / about 5.0 GiB available at assessment
Swap: none at assessment
Root filesystem: 45 GiB / about 38 GiB available
Filesystem: ext4
Git: 2.43.0
System Python: 3.12.3
systemd: running
Docker/Podman: not installed
Outbound github.com HTTPS: PASS
```

## Measured K_Supervisor CI Load

Measured locally on the VM against the current Phase 3-complete tree:

```text
compileall:
  elapsed: 0.17 s
  max RSS: about 17 MiB

pytest + branch coverage:
  229 passed
  total branch-aware coverage: 82.06%
  elapsed: 13.53 s
  max RSS: about 80 MiB

wheel build:
  elapsed: 1.99 s
  max RSS: about 50 MiB
  wheel: k_supervisor-0.1.0-py3-none-any.whl
```

Conclusion: the VM has sufficient CPU, RAM and storage for one serialized K_Supervisor validation job. One vCPU is adequate for the present test/build load but is not approved for parallel CI jobs.

## Runner Architecture

The runner must be repository-scoped to `kolemasakar/K_Supervisor`.

Approved labels:

```text
self-hosted
linux
arm64
k-supervisor-ci
```

The workflow target will be:

```yaml
runs-on: [self-hosted, linux, arm64, k-supervisor-ci]
```

Only one runner instance is approved on this VM. Job concurrency is therefore effectively one.

## Management Path

Privileged bootstrap and later runner administration must use the existing KGM owner-management path:

```text
owner / GitHub-controlled management
  -> OCI OIDC
  -> ephemeral Tailscale
  -> Tailscale SSH
  -> bounded administrative bootstrap
  -> ghrunner system account
```

Governance constraints:

- do not re-enroll SentinelX on `kgm-e4-owner-pilot`;
- do not create a new permanent privileged Sentinel channel;
- do not expand `kgmops` privileges;
- privileged owner access is for bounded bootstrap/systemd administration only;
- normal CI runtime executes exclusively as `ghrunner`.

## Security Isolation

The runner must not run as `kgmops`.

Create a dedicated unprivileged OS account:

```text
user: ghrunner
sudo: NO
interactive project-administration role: NO
runner installation/workspace: /opt/actions-runner/k-supervisor, owned by ghrunner:ghrunner and isolated from /home/kgmops
production secrets: NONE
owner SSH private keys: NONE
provider/API credentials: NONE
```

Required properties:

- `/home/kgmops` remains inaccessible to the runner account;
- the runner may write only its own installation/work directories and ordinary temporary files;
- the runner service runs under `ghrunner`;
- no production K_Supervisor secret is installed in runner environment/systemd configuration;
- jobs are accepted only from this repository;
- workflows from untrusted forks must not be granted privileged secrets or host access;
- no `sudo` permission is granted to workflow steps;
- no membership in `docker`, `lxd`, `adm` or other privileged groups;
- no access to KGM production environment files, OCI credentials, repository-external credentials or privileged sockets;
- no ability to manage KGM production services.

The self-hosted runner is persistent rather than disposable. Workspace cleanup and runner/software updates are therefore operational responsibilities.

## System Preparation

Before registration:

1. perform read-only inspection of the bootstrap script before privileged execution;
2. perform VM/KGM workload preflight;
3. create dedicated `ghrunner` account;
4. create `/opt/actions-runner/k-supervisor`, owned by `ghrunner:ghrunner`;
5. add a 2 GiB swap file only if preflight confirms it is appropriate and there is no existing swap/policy conflict;
6. install the selected official Linux ARM64 GitHub Actions Runner v2.337.0;
7. obtain a short-lived repository registration token immediately before registration;
8. register it only for `kolemasakar/K_Supervisor`;
9. install/start it as a systemd service under `ghrunner`;
10. apply runner-specific systemd resource guardrails;
11. verify runner status is online and idle.

Selected runner artifact:

```text
release: actions/runner v2.337.0
artifact: actions-runner-linux-arm64-2.337.0.tar.gz
sha256: 9b1dc70626422526e3c94767cf024896beb15da5342a3f4819bf2feac13e0393
staging verification: PASS
```

Docker is not required by the current `Core Validation` workflow and will not be installed as part of this migration. Any future Docker or privileged capability requires a separate security review.

## Registration Token Handling

The repository runner registration token is short-lived bootstrap material. It must be obtained immediately before registration, never committed or stored in project files, never sent through Sentinel, never included in handoffs/checkpoints, and never printed to logs. Hidden input or other ephemeral handoff is preferred. If the official GitHub configuration command ultimately requires the token as an argument, exposure must be bounded to the one registration process and the token must not be persisted.

## Systemd Resource Guardrails

Before migration closure, the K_Supervisor runner service must have dedicated cgroup limits so CI cannot crowd out KGM workload. Initial target:

```ini
[Service]
CPUQuota=80%
MemoryMax=2G
TasksMax=256
```

The limits must be applied as a drop-in for the specific runner service only. They must not modify unrelated KGM services.

## Python and Dependencies

The system Python version is not the CI contract. `Core Validation` continues to use:

```yaml
actions/setup-python@v7
python-version: "3.13"
```

Thus Python 3.13 remains the authoritative CI runtime. Project dependencies continue to be installed in the job as currently defined.

No GitHub Actions cache or artifact storage is required for the migration.

## Migration Sequence

The transition must occur in this order:

1. commit/push this decision as documentation only;
2. prepare the VM and dedicated runner account;
3. install and register the repository-scoped runner;
4. verify the runner is online without changing the workflow;
5. change only `runs-on` from `ubuntu-latest` to the approved self-hosted labels;
6. push the workflow change only after the runner is online;
7. require the resulting `Core Validation` job to execute on the self-hosted runner and PASS;
8. open/validate the infrastructure PR through the same protected required check;
9. merge only after exact-head PASS;
10. verify protected `main` remains green on the self-hosted runner.

This sequence avoids accidentally dispatching a new `ubuntu-latest` job during migration.

## Rollback

If the self-hosted runner cannot complete the existing workflow deterministically:

- do not weaken tests, coverage, ResourceWarning, packaging or smoke gates;
- do not bypass the required check;
- disable/stop the faulty runner;
- keep the transition branch unmerged;
- restore `runs-on: ubuntu-latest` only when GitHub-hosted execution is again available at no additional project-attributable cost, or repair the self-hosted environment.

Rollback must not create a paid validation requirement.

## Acceptance Criteria

The migration is complete only when all are true:

```text
read-only bootstrap inspection: PASS
VM/KGM workload preflight: PASS
dedicated ghrunner account: PASS
runner repository scope: PASS
runner online/idle: PASS
runner service persistence: PASS
no sudo for runner: PASS
no docker/lxd/adm authority: PASS
no access to /home/kgmops: PASS
no KGM production secret/OCI/privileged-socket access: PASS
runner path /opt/actions-runner/k-supervisor: PASS
systemd CPUQuota/MemoryMax/TasksMax guardrails: PASS
2 GiB swap safety margin, if preflight-approved: PASS
Core Validation runs on self-hosted labels: PASS
Python 3.13 via setup-python: PASS
229+ cumulative tests: PASS
branch-aware coverage >= 80%: PASS
ResourceWarning-as-error: PASS
compileall: PASS
wheel build/install: PASS
installed-wheel CLI/service smoke: PASS
required check name unchanged: PASS
protected-main governance unchanged: PASS
GitHub-hosted compute minutes required for normal K_Supervisor CI: NO
KGM production impact: NONE
SentinelX re-enrollment on runner host: NO
kgmops privilege expansion: NO
```

## Scope Boundary

This infrastructure migration does not activate ROADMAP v0.4 Phase 4 and does not authorize any Phase 4 runtime/source/test implementation.

Phase 4 remains subject to its independent audit/activation governance.
