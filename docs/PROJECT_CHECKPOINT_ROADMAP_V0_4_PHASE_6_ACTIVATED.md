# PROJECT_CHECKPOINT_ROADMAP_V0_4_PHASE_6_ACTIVATED

Control checkpoint activating ROADMAP v0.4 Phase 6 — Production Telemetry & Supply-Chain Hardening.

Version: 1.0
Status: ACTIVATED — EFFECTIVE ON PROTECTED MERGE
Roadmap: v0.4
Phase: 6
Date: 2026-09-22
Validated runtime predecessor: cf827d3d6b5dfa1f030cab28a5284ae2b72990c1
Audit merge main: 45d58aabc40ca67f49d5f7d89072a8073a8e49a9

## Activation Basis

ROADMAP v0.4 Phases 0 through 5 are COMPLETE.

The Phase 6 pre-implementation audit is COMPLETE and merged through protected PR #47. Canonical audit: `V0_4_PHASE6_PREIMPLEMENTATION_AUDIT.md`.

Audit validation evidence:

```text
Audit PR: #47
Final audit head: 1570d7d7f028e5d8e9da96842ded99fb7364a165
Final Core Validation: 35778192643 — PASS
Audit merge main: 45d58aabc40ca67f49d5f7d89072a8073a8e49a9
Runtime/source/test/workflow paths changed by audit: NONE
```

The owner explicitly approved Phase 6 activation on 2026-09-22 after review of the completed audit.

## Authorized Runtime Scope

After this checkpoint passes protected `Core Validation` and merges to `main`, Phase 6 authorizes only the implementation scope frozen in `V0_4_PHASE6_PREIMPLEMENTATION_AUDIT.md`:

- safe structured JSON production logging with deterministic correlation;
- schema-driven/allowlisted telemetry attributes and fail-closed sensitive-data redaction;
- fixed low-cardinality operational metric/event vocabulary;
- optional OpenTelemetry OTLP/HTTP export adapters behind existing observability contracts;
- Prometheus-compatible metrics exposure without requiring a Prometheus server;
- bounded exporter queues, timeouts, retries and deterministic drop/failure accounting;
- exporter failures isolated from authoritative business/control flow;
- service/auth/provider/repository/release instrumentation within the frozen telemetry taxonomy;
- deterministic dependency inventory for the built wheel;
- SPDX 2.3 SBOM generation;
- current machine-readable vulnerability evidence with explicit time-sensitive semantics;
- immutable full-commit-SHA pinning for external GitHub Actions;
- trusted-main/release wheel provenance and SBOM attestations where GitHub provides the capability at zero project-attributable cost;
- least-privilege workflow permissions for attestation and build jobs;
- explicit package metadata and protected compatibility coverage for stable Python 3.13 and 3.14;
- metadata narrowing to `>=3.13,<3.15` until Python 3.15 is separately qualified;
- operations/security documentation and deterministic failure-injection coverage;
- zero-cost deterministic development and qualification.

## Explicit Non-Scope

Phase 6 does not authorize:

- mandatory remote OpenTelemetry Collector, Prometheus, Grafana, Jaeger or SaaS infrastructure;
- paid observability, vulnerability or supply-chain services as a development/qualification dependency;
- arbitrary telemetry attributes or uncontrolled high-cardinality metric labels;
- exporter failure influencing authoritative business/control decisions;
- automatic external package publication;
- automatic Plugin installation, sharing or publication;
- organization-wide SIEM deployment;
- universal signing infrastructure outside the supported GitHub attestation path;
- arbitrary untrusted-code sandboxing;
- Python 3.15 support before a separate qualification decision;
- Phase 7 end-to-end product qualification.

## Permanent Invariants

- Existing durable telemetry, correlation, metrics snapshots, health/reliability primitives and projection exporters remain the compatibility floor.
- Production telemetry must minimize data and use explicit safe schemas rather than arbitrary attribute capture.
- External telemetry export remains optional and non-authoritative.
- Metric/event names and labels remain bounded and low-cardinality.
- Supply-chain evidence must be deterministic and machine-readable where defined by the audit.
- GitHub Actions dependencies must use immutable full-SHA references.
- Protected compatibility target is Python 3.13 + 3.14 until a later explicit qualification changes it.
- Package/publication actions remain owner-controlled.
- Development and qualification remain subject to `DEVELOPMENT_RESOURCE_POLICY.md`.

## Activation State

```text
Owner approval: YES — 2026-09-22
Pre-implementation audit: COMPLETE
Audit PR: #47
Audit final head: 1570d7d7f028e5d8e9da96842ded99fb7364a165
Audit final Core Validation: 35778192643 — PASS
Audit merge main: 45d58aabc40ca67f49d5f7d89072a8073a8e49a9
Phase 6 runtime implementation authorization: YES — audited scope only, effective after this checkpoint merges
Phase 7 runtime implementation authorization: NO
Zero-cost development policy: REQUIRED
Remote collector/SaaS dependency: OPTIONAL / NOT REQUIRED
External publication automation: FORBIDDEN
```

No Phase 6 runtime/source/test/workflow implementation may be committed before this activation checkpoint passes protected governance and merges to `main`.
