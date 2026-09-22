# V0_4_PHASE6_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 6 — Production Telemetry & Supply-Chain Hardening.

Version: 1.0
Status: COMPLETE — ACTIVATION PENDING
Date: 2026-09-22
Baseline main: cf827d3d6b5dfa1f030cab28a5284ae2b72990c1
Baseline tree: df376ec022fba242db52d546ea181fa92f96ddd9
Validated runtime predecessor: cf827d3d6b5dfa1f030cab28a5284ae2b72990c1
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 6 is limited to the ROADMAP v0.4 assignment for production telemetry and software-supply-chain hardening.

Authorized implementation scope after a separate owner activation checkpoint:

- production structured logging with deterministic correlation and fail-closed redaction;
- stable low-cardinality operational metrics;
- concrete optional OpenTelemetry and Prometheus-compatible export adapters behind existing observability contracts;
- bounded exporter queues/timeouts/retry/drop accounting with exporter failure isolated from authoritative control flow;
- service/auth/provider/repository/release telemetry coverage using a frozen event/metric taxonomy;
- strengthened telemetry privacy/data-minimization rules;
- deterministic dependency inventory and SPDX-compatible SBOM generation for the built wheel;
- current vulnerability scanning/review with machine-readable evidence;
- GitHub artifact build-provenance and SBOM attestation for trusted main/release builds where platform support is available at zero project-attributable cost;
- GitHub Actions hardening, including immutable full-SHA pinning of external actions and least-privilege workflow permissions;
- explicit Python compatibility metadata and protected CI coverage for every stable Python minor admitted by package metadata;
- operations/security runbook updates and deterministic failure-injection coverage.

Explicitly outside Phase 6:

- mandatory external telemetry collector or SaaS backend;
- mandatory Prometheus server, Grafana, Jaeger or OpenTelemetry Collector infrastructure;
- paid observability/security services;
- automatic external package publication;
- automatic Plugin publication;
- arbitrary untrusted-code sandboxing;
- organization-wide SIEM deployment;
- universal package signing infrastructure outside the supported GitHub attestation path;
- Phase 7 end-to-end product qualification.

`DEVELOPMENT_RESOURCE_POLICY.md` remains authoritative.

## 2. Frozen Phase 5 Predecessor

Phase 5 is COMPLETE.

```text
Phase 5 completion merge main: cf827d3d6b5dfa1f030cab28a5284ae2b72990c1
Merged-main Core Validation: 35775919670 — PASS
Full regression: 322 passed
Branch-aware coverage: 81.20%
compileall: PASS
wheel build/install: PASS
installed-wheel Phase 3 smoke: PASS
installed-wheel Phase 4 smoke: PASS
installed-wheel Phase 5 plugin package smoke: PASS
```

No runtime/source/test commit exists after this validated predecessor at audit start.

## 3. Existing Observability Compatibility Floor

K_Supervisor already contains a durable observability baseline that Phase 6 must evolve rather than replace.

Current implemented primitives include:

- `TelemetryRecord` with project/request/task/workflow/run/agent/capability/service-operation correlation fields;
- durable SQLite telemetry storage and restart recovery;
- `TelemetryRecorder` with basic attribute redaction;
- deterministic `TelemetryTimeline`;
- `MetricsCollector` project/agent snapshots;
- `PrometheusProjectionExporter` and `OpenTelemetryProjectionExporter` as projection-only adapters;
- `ServiceHealthEvaluator`;
- `DeploymentQualifier`;
- `ReliabilityValidator`;
- deterministic failure-injection support;
- service request telemetry;
- runtime dispatch start/completion telemetry;
- non-fatal runtime telemetry failure semantics.

Existing tests already prove:

- durable telemetry survives restart;
- selected secret-like keys and `secret://` strings are redacted;
- telemetry failure does not fail an agent execution;
- health/readiness depends on required component probes rather than Project operational state;
- exporter projections are deterministic;
- runtime correlation identifiers are preserved.

These contracts are the Phase 6 compatibility floor.

## 4. Observability Gaps

### 4.1 No production structured logger

The service host intentionally suppresses the default WSGI request log and K_Supervisor has no first-class structured production logger.

Phase 6 therefore needs a controlled structured-log adapter rather than re-enabling raw request logs.

### 4.2 Current redaction is key-pattern narrow

Current redaction protects exact sensitive keys and `secret://` string values, but arbitrary telemetry attributes may still contain private content under non-sensitive field names.

Phase 6 must move from best-effort key redaction to explicit safe telemetry schemas / allowlisted attributes for production events.

### 4.3 Current exporter implementations are projections only

`PrometheusProjectionExporter` and `OpenTelemetryProjectionExporter` currently return in-memory projections. They do not send telemetry, expose a scrape endpoint, batch, retry, enforce timeouts or account for dropped exports.

Their public compatibility should be retained, while production adapters are added separately.

### 4.4 Current Prometheus projection creates metric names from event names

The existing projection creates metric names procedurally from `event_name`.

For production metrics this is too unconstrained. Prometheus guidance favors stable metric families with labels and warns against uncontrolled/high-cardinality series.

Phase 6 needs a frozen metric vocabulary rather than arbitrary event-to-metric-name conversion.

### 4.5 Telemetry coverage is incomplete

The current production composition does not yet provide a complete operational event matrix for:

- authentication outcomes;
- service request latency/outcome;
- policy/provider side-effect attempts/outcomes;
- GitHub repository operations;
- release preparation/validation/publication handoff;
- exporter health/drop/failure state.

### 4.6 No bounded exporter lifecycle

There is no production queue/backpressure/flush/shutdown contract for telemetry exporters.

### 4.7 No current SBOM or vulnerability evidence in Core Validation

The existing workflow builds and installs a wheel but does not generate an SBOM, create a dependency inventory, or scan dependencies for known vulnerabilities.

### 4.8 No artifact provenance attestation

The current workflow does not create a GitHub artifact attestation for the built wheel or its SBOM.

### 4.9 Actions use mutable version tags

Current workflows reference actions such as `actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-artifact@v7` and `pypa/gh-action-pypi-publish@release/v1`.

GitHub security guidance states that full-length commit SHA pinning is the immutable action reference. Phase 6 should close this supply-chain gap.

### 4.10 Python metadata / CI mismatch

Current package metadata is:

```text
requires-python = ">=3.13"
```

Current protected Core Validation tests only Python 3.13.

At the 2026-09-22 compatibility snapshot:

- Python 3.13 is a supported stable bugfix branch;
- Python 3.14 is the latest supported stable feature branch;
- Python 3.15 is prerelease, with final release scheduled for 2026-10-01.

Therefore current metadata already admits stable Python 3.14 without protected CI coverage and will admit future Python 3.15 final unless bounded.

## 5. External Compatibility Snapshot

Authoritative external documentation was inspected on 2026-09-22.

### GitHub artifact attestations

GitHub documents artifact attestations as available for public repositories on current plans and supports build provenance plus SBOM attestations through `actions/attest`.

Required attestation permissions are:

```text
contents: read
id-token: write
attestations: write
```

Attestations can later be verified using GitHub CLI, including offline verification when the attestation bundle and trusted roots have been obtained.

### GitHub action hardening

GitHub security guidance recommends pinning actions to a full-length commit SHA; this is the immutable action reference.

### GitHub dependency / SBOM surfaces

GitHub supports:

- dependency review for pull requests;
- dependency submission;
- SPDX-compatible SBOM export/generation workflows.

Because vulnerability advisory data is intentionally updated over time, vulnerability status is current-security evidence rather than an immutable historical property of a commit.

### OpenTelemetry

Current OpenTelemetry Python documentation reports traces and metrics as stable and supports OTLP HTTP/protobuf and gRPC exporters.

The recommended production topology uses an OpenTelemetry Collector when one is available, but a collector is not required for K_Supervisor runtime correctness.

### Prometheus

Prometheus guidance requires stable metric meaning, base units and controlled label cardinality. IDs/user/project-specific unbounded values must not become unconstrained metric labels.

### Python

The current stable minors admitted by K_Supervisor's lower bound are 3.13 and 3.14. Python 3.15 is prerelease on the audit date.

## 6. Target Observability Architecture

```text
authoritative runtime/service/provider/repository/release path
        |
        +--> durable audit where contractually required
        |
        +--> safe telemetry event
                |
                +--> bounded structured log sink
                +--> bounded metric recorder
                +--> optional exporter supervisor
                         |
                         +--> OTLP exporter
                         +--> Prometheus-compatible projection/scrape surface
```

Permanent invariant:

```text
telemetry/export failure != business/control-state failure
```

except when an operator explicitly invokes a telemetry self-test/qualification operation whose purpose is to validate the exporter itself.

## 7. Structured Log Contract

Phase 6 should introduce a structured log event with a stable envelope.

Recommended fields:

```text
timestamp
level
event_name
component
status
duration_ms
correlation_id
request_id
project_id              optional / policy-controlled
operation
error_code              normalized only
attributes              safe allowlisted metadata
```

The logger must:

- emit JSON Lines or an equivalently deterministic machine-readable form;
- never serialize request bodies by default;
- never serialize authorization headers, bearer tokens, cookies or resolved secret values;
- never serialize hidden model reasoning;
- never serialize raw provider error bodies by default;
- normalize exception output to safe type/code/message fields;
- bound string lengths, collection depth and attribute count;
- support stdout/stderr/file-like sinks without requiring a remote service;
- remain usable when all remote exporters are disabled.

## 8. Telemetry Privacy Contract

Production telemetry must be schema-driven.

Required rules:

- event producers use event-specific safe attribute builders;
- arbitrary dictionaries from request/provider/project content are not accepted directly into production telemetry;
- credential/reference keys remain redacted;
- strings beginning with `secret://` remain redacted;
- authorization/cookie/header values are never persisted;
- request/response bodies are excluded unless a future explicitly approved event schema includes a bounded safe field;
- model prompts/responses are not telemetry fields;
- repository file contents are not telemetry fields;
- app/plugin reference-file contents are not telemetry fields;
- provider error bodies are allowlisted/normalized before recording;
- user-controlled values used as metric labels are prohibited unless from a fixed bounded enumeration.

Redaction failure must fail closed by dropping/redacting the suspect attribute, not by logging it verbatim.

## 9. Event Taxonomy

Phase 6 should freeze a small stable event taxonomy instead of emitting arbitrary names.

Minimum families:

```text
service.request.started
service.request.completed
service.request.rejected

auth.accepted
auth.rejected

policy.decision

provider.call.started
provider.call.completed
provider.call.failed

repository.operation.started
repository.operation.completed
repository.operation.blocked
repository.operation.failed

release.prepare.started
release.prepare.completed
release.prepare.failed
release.publication_required

telemetry.export.completed
telemetry.export.failed
telemetry.export.dropped
```

Existing event names remain readable for compatibility; new production instrumentation should use the frozen Phase 6 taxonomy.

## 10. Correlation Contract

Correlation should be preserved across:

```text
Service request
  -> command/idempotency receipt
  -> task/workflow/run
  -> policy decision
  -> provider/tool/repository operation
  -> release preparation
  -> telemetry/audit
```

Correlation identifiers may appear in logs/traces/events but must not become Prometheus labels.

## 11. Metrics Contract

Production metrics should use a fixed namespace and low-cardinality labels.

Recommended families:

```text
ksupervisor_service_requests_total{method,route,status_class}
ksupervisor_service_request_duration_seconds{method,route}
ksupervisor_auth_attempts_total{result}
ksupervisor_provider_calls_total{provider_type,operation,result}
ksupervisor_repository_operations_total{provider,operation,result}
ksupervisor_release_operations_total{target,operation,result}
ksupervisor_telemetry_exports_total{exporter,result}
ksupervisor_telemetry_export_dropped_total{exporter,reason}
ksupervisor_telemetry_queue_depth{exporter}
```

Rules:

- no project_id, request_id, task_id, workflow_run_id, run_id, repository name, plugin ID, email or user-provided string as a Prometheus label;
- route labels must be normalized templates, not raw paths containing IDs;
- duration uses seconds;
- byte quantities use bytes;
- result/status labels use fixed enumerations;
- all metric families must have deterministic names independent of arbitrary telemetry event names.

Existing `PrometheusProjectionExporter` remains available as a backward-compatible projection, but is not the production metric schema.

## 12. Production Exporter Contract

### OpenTelemetry

Preferred production transport: OTLP HTTP/protobuf as an optional install extra.

Requirements:

- exporter disabled by default;
- no collector required for normal runtime;
- endpoint/configuration explicit;
- optional protected-reference authentication headers resolved only at exporter boundary;
- bounded connect/request timeout;
- bounded queue;
- bounded batch size;
- bounded retry count/backoff;
- final drop accounting;
- shutdown flush bounded by configured deadline;
- exporter exception never changes authoritative control state.

OTLP gRPC may remain a future/additive option; HTTP/protobuf is sufficient for Phase 6.

### Prometheus

Phase 6 should provide a production Prometheus-compatible metrics projection/scrape surface without making a Prometheus server mandatory.

Preferred approach:

- generate deterministic Prometheus text exposition from internal metric snapshot;
- expose through an explicitly configured local/Service host endpoint or adapter;
- no background remote push;
- no authentication bypass;
- no high-cardinality labels.

If a standalone scrape endpoint is added, loopback should be the safe default and non-loopback exposure must follow existing host trust/TLS assumptions.

## 13. Exporter Isolation

Each exporter must have explicit health state:

```text
AVAILABLE
DEGRADED
UNAVAILABLE
DISABLED
```

Exporter failure handling:

- producer path performs bounded/non-blocking enqueue only;
- queue full -> drop according to explicit policy + increment drop metric;
- serialization failure -> safe normalized exporter failure;
- network timeout -> exporter degraded/unavailable;
- retry is bounded;
- no infinite retry thread;
- no unbounded memory queue;
- shutdown has bounded flush then records/drops remainder;
- business request remains independent of exporter status.

Required telemetry about telemetry must itself avoid recursive export loops.

## 14. Runtime Instrumentation Boundaries

Phase 6 implementation should instrument through existing authoritative components rather than adding parallel control paths.

Preferred insertion points:

- WSGI/Service host for request latency/status and auth outcome;
- `ServiceApiV1` for normalized operation semantics where already authoritative;
- `SideEffectGateway` for provider/tool attempt/outcome;
- governed GitHub repository adapter/provider boundary for repository-specific result categories;
- Release Manager target preparation/publication handoff;
- ServiceRuntime startup/shutdown/exporter lifecycle.

Instrumentation wrappers must not call provider/repository operations independently.

## 15. Supply-Chain Architecture

Phase 6 should separate three evidence classes.

### 15.1 Deterministic dependency inventory

Create an isolated environment from explicit pinned CI constraints and the built wheel.

Generate a machine-readable inventory from that exact environment.

### 15.2 SBOM

Generate an SPDX 2.3 JSON SBOM for the built wheel and its resolved runtime dependencies.

Required minimum content:

- package name/version;
- wheel SHA-256;
- source repository/commit;
- dependency package name/version;
- package URL where available;
- direct/transitive relationships;
- deterministic document namespace;
- explicit `NOASSERTION` rather than guessed license/download metadata.

SBOM byte generation should use stable ordering and a reproducible timestamp source such as the source commit timestamp rather than wall-clock time where the format requires a creation time.

### 15.3 Vulnerability evidence

Run a current known-vulnerability scan against the exact pinned/resolved dependency set.

The dependency set/tool invocation are deterministic; advisory status is intentionally time-sensitive because security databases evolve.

The scan must:

- emit machine-readable evidence;
- identify package/version/advisory;
- fail according to an explicit severity/allowlist policy;
- fail closed on malformed scan output;
- distinguish scanner/network unavailability from a clean result;
- require time-bounded exceptions with rationale rather than silently ignoring an advisory.

## 16. Dependency Pinning / Reproducibility

Current CI installs broad version ranges directly from PyPI, so exact dependency resolution may change without a source commit change.

Phase 6 should add explicit CI resolution artifacts for Python 3.13 and 3.14.

Preferred form:

```text
requirements/ci-py313.lock
requirements/ci-py314.lock
```

Requirements:

- exact versions;
- hashes where tooling/platform compatibility permits;
- generated/updated through an explicit documented process;
- normal protected CI installs from the lock/constraints rather than unconstrained ranges;
- package runtime metadata remains appropriately ranged for consumers;
- dependency updates arrive through reviewed PRs.

Lock artifacts are CI/build reproducibility inputs, not a claim that consumer environments must use those exact versions.

## 17. GitHub Dependency Security

For this public repository, Phase 6 should use GitHub's zero-cost dependency-security surfaces where available.

Preferred policy:

- dependency graph enabled;
- Dependabot alerts enabled where available;
- dependency review on pull requests that modify dependency manifests/locks;
- dependency review action pinned to a verified full commit SHA;
- introduced vulnerable dependencies fail the dependency-security gate according to configured severity policy;
- scan/evidence result remains separate from runtime business state.

If a required repository security feature is unavailable to the account/repository at implementation time, Phase 6 must not silently weaken the gate; it must use an explicit local/open-source fallback or stop for owner action.

## 18. GitHub Actions Hardening

Phase 6 should harden every active workflow, not only new supply-chain steps.

Required implementation review:

```text
.github/workflows/core-validation.yml
.github/workflows/package-publish.yml
.github/workflows/phase3-validation.yml
new Phase 6 supply-chain workflow(s)
```

Requirements:

- pin external actions to verified full-length commit SHAs;
- annotate the human-readable upstream release/tag in comments if useful;
- explicit least-privilege `permissions`;
- no write/OIDC permissions in untrusted PR test jobs;
- attestation permissions only in trusted main/manual release jobs;
- no secrets in pull-request jobs from untrusted forks;
- retire or migrate obsolete legacy workflows that duplicate old validation;
- preserve required `Core Validation` ruleset context.

## 19. Artifact Provenance / Attestation

K_Supervisor is currently a public GitHub repository, so GitHub artifact attestations are available under current GitHub documentation without requiring an Enterprise plan.

Phase 6 should add a trusted-main supply-chain evidence job/workflow that:

1. checks out the exact `main` commit;
2. builds the wheel;
3. computes and records SHA-256;
4. generates the SPDX SBOM;
5. creates build-provenance attestation for the wheel;
6. creates SBOM attestation linking the wheel and SBOM;
7. uploads the wheel/SBOM/evidence as workflow artifacts;
8. records the run and commit SHA in completion evidence.

Security boundary:

- run attestation only on trusted `main` push or explicit owner-controlled workflow;
- do not grant `id-token: write` / `attestations: write` to ordinary pull-request code;
- use the minimum documented permissions;
- do not imply that an attestation proves the artifact is vulnerability-free.

The manual package-publication workflow may later consume/rebuild and attest release artifacts, but Phase 6 does not automate publication.

## 20. Python Compatibility Contract

Audit-date stable compatibility target:

```text
Python 3.13: supported / required
Python 3.14: supported / required
Python 3.15: prerelease / advisory only
```

Phase 6 should make metadata and CI agree.

Preferred implementation:

```text
requires-python = ">=3.13,<3.15"
```

until Python 3.15 receives its own explicit compatibility validation/approval.

Protected CI must make both 3.13 and 3.14 gating.

Because repository rules currently require the check context `Core Validation`, the implementation must preserve that exact required context. Preferred structure:

```text
Python 3.13 validation job
Python 3.14 validation job
        |
        v
Core Validation aggregate job
```

The aggregate required check succeeds only if every admitted stable Python job succeeds.

A non-blocking Python 3.15 prerelease compatibility probe may be added only if it does not consume paid resources and cannot be confused with supported-version qualification.

## 21. Core Validation / Supply-Chain Workflow Separation

Do not broaden the current required PR job with unnecessary write permissions.

Recommended split:

### Core Validation

- pull request + trusted push;
- read-only repository permissions;
- Python 3.13 + 3.14 gates;
- tests/coverage/compile/wheel/install smoke;
- deterministic SBOM structure tests;
- deterministic exporter failure tests;
- no attestation write permission.

### Supply Chain Evidence

- trusted `main` push and/or manual owner execution only;
- self-hosted zero-cost runner where compatible;
- explicit minimal `id-token: write` and `attestations: write`;
- wheel + SBOM + provenance attestation;
- machine-readable vulnerability evidence;
- artifact upload.

The supply-chain workflow must not publish a package.

## 22. Existing Package Publish Workflow

Current `Package Publish` remains manual-only and owner-confirmed, which is compatible with the publication boundary.

Phase 6 should harden it by:

- pinning external actions to immutable full SHAs;
- keeping PyPI Trusted Publishing / OIDC;
- keeping the protected `pypi` environment;
- retaining `workflow_dispatch` + explicit confirmation only;
- adding artifact/SBOM provenance verification or attestation where it does not weaken owner control;
- avoiding any push/tag/schedule publication trigger.

## 23. Required Failure-Injection Coverage

Phase 6 deterministic tests must inject:

- structured-log sink failure;
- OTLP connect timeout;
- OTLP HTTP failure;
- malformed exporter payload;
- exporter queue full;
- exporter shutdown flush timeout;
- Prometheus render failure;
- telemetry safe-attribute rejection;
- vulnerability scanner unavailable/malformed result;
- SBOM generation failure;
- attestation workflow permission/trigger contract mismatch through static workflow tests.

Required assertion in every runtime exporter failure case:

```text
authoritative business/control result remains correct
```

while exporter degradation/drop evidence is recorded separately.

## 24. Secret / Private-Content Verification

Phase 6 should add regression fixtures containing canary values in:

- Authorization header;
- bearer token;
- cookie;
- `secret://` reference;
- provider API key;
- nested credential field;
- ProjectSpec data;
- request body;
- model prompt/response-like text;
- repository file content.

Tests must scan structured logs, telemetry storage, exporter output and failure messages and prove forbidden canaries do not appear.

## 25. Configuration Contract

Exporter configuration should be additive under existing configuration-version semantics only if old configs remain valid.

Recommended optional configuration shape:

```text
observability:
  structured_log:
    enabled
    level
    destination
  otlp:
    enabled
    endpoint
    timeout_seconds
    queue_size
    batch_size
    auth_ref
  prometheus:
    enabled
    bind_host
    port
```

Unknown fields continue to fail validation.

Default:

```text
remote exporters disabled
structured local logging safe-default
```

If the additive configuration cannot be introduced without ambiguity, bump `config_version` with explicit migration; do not silently reinterpret old fields.

## 26. Persistence Contract

Phase 6 should avoid schema migration unless durable state genuinely requires new fields/tables.

Preferred design:

- keep telemetry records durable using existing storage where sufficient;
- exporter queues remain in-memory/bounded unless durable delivery is explicitly required;
- exporter operational counters need not become authoritative business state;
- audit remains authoritative for permission/side-effect events already requiring durable evidence.

If a new persistent telemetry schema is introduced, it requires migration/rollback/recovery tests before activation completion.

## 27. Deployment / Health Contract

Remote exporter availability is optional and must not make normal service readiness false.

Required readiness distinction:

```text
required persistence/control dependencies -> readiness gate
optional telemetry exporter -> degraded diagnostic state, not business readiness gate
```

An explicit deployment profile may choose to mark an exporter required, but that is operator configuration and must not be the default.

## 28. Implementation Sequence

After a separate owner-approved Phase 6 activation checkpoint merges:

1. freeze event/log/metric schemas and strengthen redaction/allowlisting;
2. implement structured local logger and tests;
3. implement stable metrics registry/projection and low-cardinality tests;
4. add bounded exporter supervisor and failure isolation;
5. implement optional OTLP HTTP exporter and Prometheus-compatible surface;
6. instrument service/auth/provider/repository/release boundaries;
7. add Python 3.13/3.14 compatibility metadata and aggregate protected CI gate;
8. add pinned CI dependency-resolution artifacts;
9. add deterministic SPDX SBOM generation;
10. add current vulnerability review/scan evidence;
11. pin workflow actions to immutable verified SHAs;
12. add trusted-main wheel/SBOM artifact attestations with least-privilege permissions;
13. update operations/security/release documentation;
14. run cumulative qualification and installed-wheel observability/supply-chain smoke.

No Phase 7 work is authorized by this sequence.

## 29. Audited Verification Contract

After activation, deterministic Phase 6 verification must prove:

- structured log output is machine-readable and deterministic;
- no authorization/token/cookie/secret/provider private content leaks into logs, durable telemetry or exporter output;
- arbitrary unsafe telemetry attributes fail closed;
- event names come from the frozen production taxonomy where required;
- correlation survives service -> side effect/repository/release paths;
- production metric families are stable and low-cardinality;
- IDs/user/project/repository-specific unbounded values are absent from Prometheus labels;
- duration/byte units follow documented base-unit contracts;
- exporter queue and retry bounds are enforced;
- exporter/network failure does not fail authoritative business/control flow;
- exporter drop/failure state is observable without recursive failure;
- optional exporters do not make default service readiness false;
- OTLP exporter is disabled safely when dependency/config is absent;
- Prometheus projection/scrape output contains only approved metric families;
- Python 3.13 protected CI passes;
- Python 3.14 protected CI passes;
- package metadata excludes unsupported future stable minors until separately approved;
- external GitHub Actions are pinned to verified full commit SHAs;
- pull-request validation retains read-only/minimal permissions;
- trusted attestation jobs are not runnable from untrusted PR code with write/OIDC authority;
- built wheel SHA-256 is recorded;
- SPDX SBOM is generated from the exact pinned/resolved build environment;
- SBOM contains the project and resolved runtime dependency relationships;
- vulnerability scan/review emits machine-readable evidence and applies the approved failure policy;
- vulnerability-data unavailability is distinguished from a clean scan;
- GitHub build provenance attestation is created for the trusted-main wheel;
- GitHub SBOM attestation links the wheel and generated SBOM;
- attestation evidence is verifiable using the supported GitHub verification path;
- package publication remains manual owner-controlled;
- no paid external resource is required;
- full cumulative regression, branch-aware coverage >=80%, compile, wheel/install and required installed-wheel smoke paths remain green.

## 30. Protected Governance Evidence

```text
Audit PR: #47
Initial audit head: 66178b16d3bc4864b83a87226b0a4a169a8363c7
Initial Core Validation: 35778039230 — PASS
Validation runner: kgm-e4-owner-pilot
Runtime/source/test/workflow paths changed: NONE
```

The exact final audit head, including this evidence, must pass required `Core Validation` before merge. The merged audit remains documentation-only and does not activate Phase 6.

## 31. Activation Boundary

```text
PHASE_6_PREIMPLEMENTATION_AUDIT=COMPLETE
PHASE_6_ACTIVATION=NO
PHASE_6_RUNTIME_IMPLEMENTATION_AUTHORIZATION=NO
CURRENT_RUNTIME_PREDECESSOR=cf827d3d6b5dfa1f030cab28a5284ae2b72990c1
CURRENT_AUDIT_BASELINE=cf827d3d6b5dfa1f030cab28a5284ae2b72990c1
ZERO_COST_DEVELOPMENT=REQUIRED
MANDATORY_REMOTE_COLLECTOR=NO
PUBLICATION_AUTOMATION=FORBIDDEN
SUPPORTED_STABLE_PYTHON_TARGETS=3.13,3.14
NEXT_GATE=OWNER_PHASE_6_ACTIVATION_DECISION
```

This audit does not activate Phase 6. Runtime/source/test/workflow implementation may begin only after explicit owner approval, a separate protected Phase 6 activation checkpoint, protected `Core Validation` PASS, and merge to `main`.
