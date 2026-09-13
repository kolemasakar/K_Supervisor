# MACHINE_CONTRACTS
Опис першої machine-readable версії базових контрактів K_Supervisor та рішень Phase 1.

Version: 1.0-draft
Status: IN_PROGRESS
Phase: 1

## 1. Runtime Baseline

Initial implementation baseline:

```text
Python >= 3.13
Pydantic v2
JSON Schema 2020-12
pytest
```

The runtime choice is an implementation baseline, not a requirement for future remote agents or external integrations.

## 2. Machine Contract Set

Phase 1 defines machine models for:

```text
Project
ProjectSpec
ProjectLifecycleTransition
ProjectOperationalTransition
Task
WorkflowRun
CapabilityDescriptor
CapabilityRequirement
AgentDescriptor
AgentRunRequest
AgentRunResult
HumanActionRequest
NotificationEvent
Release
```

## 3. Project Isolation

Project is the top-level isolation boundary.

Agent run envelopes must include `project_id` so parallel project execution does not depend on process-global context.

## 4. ProjectSpec Approval

`ProjectSpec.status == APPROVED` requires an approval timestamp.

Draft or review-required specifications must not carry an approval timestamp.

Approved ProjectSpec snapshots are immutable. Material changes create a new specification version.

## 5. State Validation

Project lifecycle state and operational state are independent machine enums.

Allowed transitions are represented by explicit transition tables. Invalid transitions fail deterministically during validation.

## 6. Agent Contract v1 Direction

The execution boundary remains:

```text
AgentRunRequest -> Agent Runtime -> AgentRunResult
```

The v1 machine envelope adds explicit:

```text
project_id
capability_version
```

Agent capability declarations use structured `capability_id + capability_version` references.

Execution status remains separate from domain conclusions.

## 7. Capability Contract v1 Direction

Capability identifiers remain lowercase dot-separated namespaces.

Capabilities declare operations, schema references, dependencies, side effects, risk class, trust requirements, and resource metadata.

`NONE` side effect cannot be combined with effectful declarations.

## 8. Human Intervention and Notification

Phase 1 includes machine contracts for `HumanActionRequest` and `NotificationEvent`.

The initial NotificationEvent channel set contains only:

```text
EMAIL
```

WhatsApp, Viber, and other messaging transports remain future extension points.

## 9. Release Contract

Release state remains independent from project lifecycle.

Baseline release targets:

```text
GPT_STORE
API_SERVICE
WEB_APPLICATION
CLI_PACKAGE
INTERNAL_AGENT
OTHER
```

GPT Store publication remains an owner action.

## 10. Schema Export

The planned canonical schema location is:

```text
schemas/v1/
```

Schemas are generated from validated contract models.

## 11. Local Prototype Validation

The prepared Phase 1 implementation prototype has passed locally:

```text
pytest: 8 passed
schema export: PASS
JSON Schema 2020-12 validation: PASS
python compileall: PASS
```

The implementation is not yet committed because the current GitHub write channel rejected source-code writes at the platform safety boundary.

Therefore Phase 1 remains `IN_PROGRESS` until the executable models, schemas, and tests are present in the repository and re-verified there.
