# PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_COMPLETE_2026_09_22

Authoritative completion checkpoint for the K_Supervisor Core Validation migration from GitHub-hosted Actions to the repository-scoped ARM64 self-hosted runner.

Version: 1.0
Status: COMPLETE
Date: 2026-09-22
Authority: owner-approved CI infrastructure migration

## Outcome

The protected `Core Validation` workflow now runs on the repository-scoped self-hosted runner on `kgm-e4-owner-pilot`:

```yaml
permissions:
  contents: read

runs-on: [self-hosted, linux, arm64, k-supervisor-ci]
```

The required status context remains exactly:

```text
Core Validation
```

ROADMAP v0.4 Phase 4 was not activated by this operational migration.

## Runner Baseline

```text
VM=kgm-e4-owner-pilot
OS=Ubuntu 24.04 ARM64
runner_version=2.337.0
runner_name=kgm-e4-owner-pilot
runner_group=Default
runner_scope=repository
repository=kolemasakar/K_Supervisor
labels=self-hosted,linux,arm64,k-supervisor-ci
runtime_user=ghrunner
service=actions.runner.kolemasakar-K_Supervisor.kgm-e4-owner-pilot.service
swap=2 GiB
```

Verified runtime guardrails:

```text
CPUQuota=70%
MemoryHigh=1G
MemoryMax=1536M
TasksMax=128
NoNewPrivileges=yes
PrivateTmp=yes
ProtectProc=invisible
InaccessiblePaths=/home/kgmops
GHRUNNER_SUDO=NO
GHRUNNER_DOCKER_AUTHORITY=NO
KGMOPS_PRIVILEGE_EXPANSION=NO
```

## Security Gate for Public Repository

Because `K_Supervisor` is public and `Core Validation` runs on `pull_request`, repository Actions policy was set to:

```text
Require approval for all external contributors
```

Repository default workflow permissions remain read-only, and the workflow explicitly declares:

```yaml
permissions:
  contents: read
```

## Workflow Migration Evidence

Migration branch head:

```text
19e1df12a1e6b6f4a59c0539f69c2f1f7f3827e4
```

Pre-PR self-hosted push validation:

```text
run=35729485398
event=push
result=PASS
runner=kgm-e4-owner-pilot
GITHUB_TOKEN Contents=read
```

Protected PR validation:

```text
PR=#32
run=35729696043
event=pull_request
result=PASS
required_check=Core Validation
```

Merge:

```text
PR=#32
merge_commit=2945871da17531552ff36f7e22e5cdf19afe1375
merged_at=2026-09-22T13:10:29Z
```

Merged-main validation:

```text
run=35731755438
event=push
result=PASS
runner=kgm-e4-owner-pilot
runner_group=Default
machine=kgm-e4-owner-pilot
GITHUB_TOKEN Contents=read
```

The active repository ruleset remains:

```text
ruleset=main-core-validation
ruleset_id=23556478
enforcement=active
required_status_context=Core Validation
bypass_actors=NONE
```

## Bootstrap Compatibility Remediation

Ubuntu 24.04 provides LTTng UST with SONAME `liblttng-ust.so.1`, while the optional runner tracing provider still reports `liblttng-ust.so.0` as unresolved.

The bootstrap dependency check was narrowed so that only this exact optional tracing-provider mismatch is ignored. All other unresolved shared libraries remain fatal.

No incompatible `.so.0 -> .so.1` symlink was created.

## Recovery / Cleanup Evidence

Temporary recovery access was fully removed after runner registration.

Host cleanup verification was performed through a bounded one-shot owner workflow:

```text
KGM cleanup run=35732968034
TEMP_OWNER_KEY=ABSENT
BOOTSTRAP_BACKUP_CLEANUP=PASS
PATCH_TEMP_CLEANUP=PASS
KGM_SERVICE=ACTIVE
RUNNER_SERVICE=ACTIVE
GHRUNNER_PRIVILEGE_BOUNDARY=PASS
HOST_RECOVERY_CLEANUP=PASS
```

Owner-confirmed cleanup:

```text
temporary ubuntu SSH bootstrap key=REMOVED
temporary OCI Run Command policy=REMOVED
temporary OCI dynamic group=REMOVED
serial console connection=REMOVED / NONE PRESENT
local temporary key directory=REMOVED
local key verification=TEMP_KEY_CLEANUP=PASS
temporary KGM recovery branch=DELETED
temporary GitHub recovery workflows=REMOVED
```

The existing unrelated OCI/KRC read-only policy and dynamic group were not modified.

## Production Impact

```text
KGM production service=ACTIVE after cleanup
KGM production configuration change=NONE
KGM production secret exposure=NONE OBSERVED
K_Supervisor runtime/source behavior change=NONE
CI execution target change=YES
```

## Acceptance

```text
RUNNER_REGISTERED=PASS
RUNNER_ONLINE=PASS
RUNNER_IDLE_BEFORE_TEST=PASS
REPOSITORY_SCOPE=K_Supervisor_ONLY

GHRUNNER_SUDO=NO
GHRUNNER_DOCKER_AUTHORITY=NO
KGM_PRODUCTION_SECRET_ACCESS=NO OBSERVED
KGMOPS_PRIVILEGE_EXPANSION=NO

SYSTEMD_MEMORY_GUARDRAIL=PASS
SYSTEMD_CPU_GUARDRAIL=PASS
SYSTEMD_TASKS_GUARDRAIL=PASS

CORE_VALIDATION_SELF_HOSTED=PASS
REQUIRED_CHECK_NAME_UNCHANGED=PASS
RULESET_GOVERNANCE=PASS
PUBLIC_REPO_EXTERNAL_CONTRIBUTOR_APPROVAL=PASS

K_SUPERVISOR_HOSTED_CORE_VALIDATION_USED=NO
KGM_PRODUCTION_IMPACT=NONE OBSERVED
RECOVERY_SURFACE_CLEANUP=PASS
```

The owner-observed GitHub-hosted quota condition remains historical project evidence; this checkpoint does not claim an independent billing-meter verification.

## Current State

```text
SELF_HOSTED_CI_MIGRATION=COMPLETE
CANONICAL_MAIN=2945871da17531552ff36f7e22e5cdf19afe1375
CORE_VALIDATION_RUNNER=self-hosted,linux,arm64,k-supervisor-ci
REQUIRED_CHECK=Core Validation
RECOVERY_CLEANUP=COMPLETE
PHASE4_ACTIVATION=NO
NEXT_ROADMAP_WORK=Phase 4 pre-implementation audit only
```
