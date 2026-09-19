# SELF_HOSTED_CI_RUNNER_PREFLIGHT_2026_09_19

Read-only preflight evidence for the approved K_Supervisor self-hosted CI migration.

Version: 1.1
Status: COMPLETE — PRIVILEGED BOOTSTRAP PENDING
Date: 2026-09-19
Decision authority: `SELF_HOSTED_CI_RUNNER_DECISION.md` v1.2

## Host Evidence

```text
host: kgm-e4-owner-pilot
OS: Ubuntu 24.04.4 LTS
architecture: ARM64 / aarch64
CPU: 1 vCPU Neoverse-N1
RAM: 5.8 GiB / about 5.0 GiB available
disk: 45 GiB / about 38 GiB available
swap: none before migration
systemd: running
Tailscale: running / online
Docker/Podman: absent
```

## KGM Workload Check

Observed host load was low. `kgm-monitor.service` runs as the dedicated `kgm` account, used about 14 MiB memory during the sample and was effectively idle on CPU. VM samples showed 99-100% CPU idle.

Conclusion: one serialized CI runner with the approved resource guardrails is compatible with current KGM workload.

## Isolation / Storage

```text
/home/kgmops: mode 0750, owner kgmops:kgmops
/opt: root-owned
ghrunner before migration: absent
free disk: about 38 GiB
runner archive: about 133 MiB
expanded package: about 454 MiB
```

The approved installation location remains `/opt/actions-runner/k-supervisor`. No privilege expansion for `kgmops` is authorized.

## Network / Management Path

GitHub, GitHub API and codeload HTTPS checks passed. Tailscale reports the host online. Privileged work remains restricted to the existing KGM owner-management path documented in `SELF_HOSTED_CI_RUNNER_DECISION.md`. SentinelX re-enrollment is not authorized.

## Runner Package

```text
version: 2.337.0
platform: Linux ARM64
checksum verification: PASS
tar path-safety scan: PASS
config version check: PASS
listener version check: PASS
```

## Dependency Review

A full ELF dependency scan found one missing runtime library associated with the tracing provider. Ubuntu 24.04 maps it to `liblttng-ust1t64`. A package-manager simulation showed only that package plus its two runtime dependencies would be added, with no upgrades or removals.

Decision: use only the bounded reviewed dependency change. Do not invoke the broad upstream dependency installer.

## Original Bootstrap Review

The first staged bootstrap was reviewed and NOT executed. It was rejected because it did not satisfy the final manager-approved installation path, service resource-guardrail contract and token-handling model.

The rejected file was made non-executable and moved to:

`/home/kgmops/runner-bootstrap/bootstrap-self-hosted-runner.preflight-rejected.sh`

## Registration Token Review

Official runner help confirms interactive registration is supported and a token argument is mandatory only for unattended mode. The corrected migration must therefore use the official interactive registration prompt under the dedicated runner identity; project scripts must not persist or log the short-lived registration token.

## Swap Decision

No swap is currently configured. With about 38 GiB free disk, the previously approved 2 GiB swap safety margin remains appropriate if host state is unchanged at privileged execution time. No global swappiness change is approved.

## Resource Guardrail Sizing

Final pre-validation values approved from measured capacity/workload evidence:

```text
CPUQuota=70%
MemoryHigh=1G
MemoryMax=1536M
TasksMax=128
Restart override=NONE
```

Evidence used:

- host: 1 vCPU, 5.8 GiB RAM, about 4.9 GiB available, 38 GiB disk free;
- KGM production monitor: about 14 MiB, one task, 0% CPU over a 5-second sample;
- K_Supervisor pytest+coverage benchmark: 229 tests, 82.06% coverage, about 13.5 s, about 80 MiB max RSS, about 61% average CPU;
- wheel build: about 50 MiB max RSS and about 2 s;
- standard GitHub runner v2.337.0 systemd template contains no `Restart=` directive;
- a separate parallel `kgmops` pytest was observed during the later preflight sample and was deliberately not terminated or treated as KGM production load.

These guardrails must be installed before the first self-hosted `Core Validation` run and must apply only to the K_Supervisor runner service/cgroup.

## Result

```text
BOOTSTRAP_READ_ONLY_REVIEW=PASS
VM_CAPACITY=PASS
KGM_WORKLOAD_CONFLICT=NONE
NETWORK_TO_GITHUB=PASS
TAILSCALE_READY=PASS
RUNNER_PACKAGE_VERIFICATION=PASS
BOUNDED_DEPENDENCY_PLAN=PASS
SWAP_2G_APPROVED=YES
SYSTEMD_GUARDRAIL_SIZING=PASS
ORIGINAL_BOOTSTRAP=REJECTED_NOT_EXECUTED
WORKFLOW_MUTATED=NO
GITHUB_ACTIONS_RUN_TRIGGERED=NO
PHASE4_ACTIVATION=NO
```

## Next Gate

The next action is bounded privileged bootstrap through the existing KGM owner path. Workflow mutation is prohibited until the dedicated runner is independently confirmed as repository-scoped, online/idle, resource-limited and isolated according to `SELF_HOSTED_CI_RUNNER_DECISION.md`.

## Reviewed Bootstrap Artifact

```text
guardrail implementation commit: cceefcabeaf73b74d4f0d1364980d5be1557b69d
path: ops/ci/bootstrap-self-hosted-runner.sh
reviewed content SHA-256: 37b9f1e6674eb313761efd060e08eca7791959f093aec46b244cce988561ff12
bash syntax check: PASS
clean registration environment: PASS
token CLI argument in project script: ABSENT
broad upstream dependency installer: ABSENT
workflow runs caused by script commit: NONE
```

## Management Execution Boundary

Read-only review found the existing KGM GitHub workflows `tailscale-kgm-control.yml` and `tailscale-kgm-bootstrap.yml`; both currently run on GitHub-hosted Ubuntu runners. They are therefore not an authorized bootstrap route while the included hosted quota is exhausted.

The existing `kgmops` sudo contract is intentionally limited to KGM health/restart/log operations and is insufficient for runner installation. It must not be expanded.

The next gate is a bounded privileged owner session through the approved external KGM management path/Tailscale SSH. No workflow mutation is permitted before that bootstrap completes and the runner is independently confirmed online/idle.
