# PROJECT_CHECKPOINT_SELF_HOSTED_CI_PREFLIGHT_2026_09_20

Read-only preflight evidence for the approved K_Supervisor self-hosted Core Validation migration.

Version: 1.0
Status: PREFLIGHT PASS / PRIVILEGED BOOTSTRAP PENDING
Date: 2026-09-20
Predecessor: PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_APPROVED_2026_09_19.md

## Scope

This checkpoint records read-only inspection only. No runner user, swap, package, systemd unit, workflow, ruleset, KGM production service, or privilege boundary was modified.

The inspection used the already-connected read-only Remote Desktop Commander surface on `kgm-e4-owner-pilot` only for host/file/process facts. It is not approved as the privileged bootstrap path and was not used with sudo.

## Bootstrap Script Inspection

Inspected:

```text
/home/kgmops/runner-bootstrap/bootstrap-self-hosted-runner.sh
owner=kgmops:kgmops
mode=0700
```

The script enforces:

- exact host `kgm-e4-owner-pilot`;
- exact architecture `aarch64`;
- root execution through the approved owner path;
- official runner archive SHA-256 validation before extraction;
- dedicated `ghrunner` system account;
- removal/rejection of `sudo`, `adm`, `docker`, and `lxd` memberships;
- rejection if `ghrunner` can read/traverse `/home/kgmops`;
- isolated runner directory `/opt/actions-runner/k-supervisor`;
- interactive runner registration under a clean `ghrunner` environment;
- systemd service installation only after registration;
- systemd cgroup/resource/security guardrails;
- no workflow mutation.

No registration token is embedded in the script.

## Official Runner Artifact

```text
version=v2.337.0
asset=actions-runner-linux-arm64-2.337.0.tar.gz
local_size=139124737
official_sha256=9b1dc70626422526e3c94767cf024896beb15da5342a3f4819bf2feac13e0393
local_sha256=9b1dc70626422526e3c94767cf024896beb15da5342a3f4819bf2feac13e0393
DIGEST_MATCH=PASS
```

The release/tag and digest were independently verified against the official `actions/runner` GitHub release metadata.

The package contains `config.sh` and `bin/systemd.svc.sh.template`. A top-level `svc.sh` is not present before configuration; service tooling is generated as part of configured runner state. This is not treated as a preflight failure.

## VM Preflight

```text
hostname=kgm-e4-owner-pilot
architecture=aarch64
os=Ubuntu 24.04
cpu=1 OCPU
cpu_model=Neoverse-N1

memory_total=5.8 GiB
memory_available≈5.0 GiB
swap_total=0
disk_root=45 GiB
disk_available≈38 GiB
disk_use≈15%

systemd=255
system_state=running
cgroup=v2
controllers=cpu,memory,pids present

kgm-monitor.service=active
kgm-monitor.service enabled=yes
kgm_memory_current≈14 MiB
kgm_memory_peak≈14 MiB
kgm_tasks_current=1

ghrunner=ABSENT
existing_actions_runner_service=NONE_OBSERVED
liblttng-ust1t64=NOT_INSTALLED
liblttng-ust1t64_candidate=2.13.7-1.1ubuntu2

github.com outbound=PASS
api.github.com outbound=PASS
```

`objects.githubusercontent.com` was reachable but its root path returned HTTP 404; this is not an outbound-connectivity failure.

## Resource Guardrail Decision

Based on the observed 1-OCPU / 5.8-GiB host and the small current KGM service footprint, retain the prepared conservative limits:

```text
CPUQuota=70%
MemoryHigh=1G
MemoryMax=1536M
TasksMax=128
NoNewPrivileges=true
PrivateTmp=true
ProtectProc=invisible
InaccessiblePaths=/home/kgmops
UMask=0077
```

Decision:

```text
SYSTEMD_GUARDRAIL_PLAN=APPROVED
GUARDRAIL_CHANGE_REQUIRED_BEFORE_BOOTSTRAP=NO
SWAP_2_GIB=APPROVED_IF_CURRENT_SWAP_REMAINS_ZERO_AT_BOOTSTRAP
```

## Management-Path Gate

The existing KGM GitHub/Tailscale control workflow remains operational; a recent `KGM Tailscale Ansible Control` run completed successfully.

However, its normal SSH identity is `kgmops`, whose privileges must not be expanded. Repository evidence inspected during this preflight does not prove that the existing Tailscale SSH ACL authorizes privileged `ubuntu` login from `tag:github-actions`.

Therefore:

```text
KGMOPS_PRIVILEGE_EXPANSION=NO
SENTINELX_REENROLLMENT=NO
HP_OMEN_DEPENDENCY=NO
UNVERIFIED_PRIVILEGED_TAILSCALE_PATH=DO_NOT_USE
PRIVILEGED_BOOTSTRAP=OWNER_INTERACTIVE_SESSION_REQUIRED
```

The approved owner/bootstrap SSH path may be used only for the bounded bootstrap/systemd operation. Normal CI runtime remains `ghrunner`.

## Next Gate

From an approved interactive owner/bootstrap session on `kgm-e4-owner-pilot`:

```bash
sudo /home/kgmops/runner-bootstrap/bootstrap-self-hosted-runner.sh
```

At the GitHub runner registration prompt, enter a freshly generated repository-scoped short-lived registration token for `kolemasakar/K_Supervisor`.

Do not paste or store that token in project files, documentation, chat, Sentinel, shell history, or logs.

After the script reports `RUNNER_BOOTSTRAP=PASS`, perform read-only verification of:

```text
RUNNER_REGISTERED
RUNNER_ONLINE
RUNNER_IDLE
REPOSITORY_SCOPE
labels
ghrunner groups/access
systemd guardrails
swap
KGM service health/resource impact
```

Only after that verification may `.github/workflows/core-validation.yml` be changed from `ubuntu-latest` to the approved self-hosted labels.
