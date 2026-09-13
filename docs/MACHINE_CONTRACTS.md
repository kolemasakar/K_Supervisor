# MACHINE_CONTRACTS
Опис першої machine-readable версії базових контрактів K_Supervisor та результатів Phase 1.

Version: 1.0
Status: ACTIVE
Phase: 1 COMPLETE

## 1. Runtime Baseline

```text
Python >= 3.13
Pydantic v2
JSON Schema 2020-12
pytest
```

The runtime baseline applies to the initial local platform implementation. External and future remote agents remain contract-driven and are not required to use Python.

## 2. Canonical Machine Contract Set

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

Python models are stored in `models/`.

Interchange schemas are stored in:

```text
schemas/v1/
```

## 3. Contract Version

The first machine-readable contract baseline is:

```text
contract_version: 1.0
schema_namespace: schemas/v1
```

Breaking contract changes require a new major version or an explicit migration path.

## 4. Project Isolation

`Project` is the top-level managed and isolation boundary.

Task, workflow, agent execution, intervention, notification, and release records carry `project_id` where they belong to one managed project.

Agent execution envelopes explicitly include:

```text
project_id
capability_id
capability_version
```

This avoids reliance on process-global project context and supports later parallel-project execution.

## 5. ProjectSpec Approval

`ProjectSpec.status == APPROVED` requires `approved_at`.

Non-approved ProjectSpec instances must not silently represent themselves as approved snapshots.

Approved specifications are immutable machine models. Material changes require a new ProjectSpec version.

## 6. State Validation

Project lifecycle and operational state are separate.

Allowed transitions are defined by explicit validation tables in the model layer.

Examples:

```text
lifecycle: BUILDING -> VALIDATING
operational: ACTIVE -> WAITING_FOR_OWNER
```

Invalid transitions fail validation rather than being accepted as arbitrary state changes.

## 7. Agent Contract v1

The execution boundary is:

```text
AgentRunRequest
-> Agent Runtime
-> AgentRunResult
```

Execution status remains separate from domain conclusions.

A failed normalized result requires an explicit error object at the Python model boundary.

## 8. Capability Contract v1

Capabilities remain independent from agents.

Capability identifiers use lowercase dot-separated namespaces.

A capability descriptor declares its version, operations, schemas, dependencies, side-effect codes, risk metadata, and extension metadata.

`NONE` cannot be combined with other side-effect declarations.

Side-effect codes are extensible strings in the v1 machine model. Their normative semantics and permission enforcement belong to Capability Model and the policy layer.

## 9. Human Intervention and Notification

Machine contracts exist for:

```text
HumanActionRequest
NotificationEvent
```

The initial implemented notification channel is:

```text
EMAIL
```

Additional messaging channels remain deferred extension points.

## 10. Release Contract

Release state remains separate from project lifecycle state.

Release targets may include GPT Store and other project-specific targets. GPT Store preparation may be automated; actual publication remains an owner action under the approved project policy.

## 11. Validation Baseline

Repository tests include:

```text
tests/test_phase1_models.py
tests/test_phase1_schemas.py
```

The behavioral test baseline covers:

- ProjectSpec approval rules;
- serialization round-trip;
- lifecycle transition rejection;
- operational WAITING_FOR_OWNER separation;
- capability side-effect consistency;
- project isolation in AgentRunRequest;
- email notification default;
- release publication-state validation.

Equivalent local execution of the committed model set passed:

```text
pytest behavioral tests: 8 passed
```

The schema test validates every `*.schema.json` file under `schemas/v1/` as JSON Schema Draft 2020-12.

## 12. Phase 1 Result

Phase 1 exit criteria are satisfied:

- core machine models exist;
- ProjectSpec approval is machine-enforced;
- invalid project state transitions fail deterministically;
- agent execution carries project and capability version context;
- machine interchange schemas are versioned under `schemas/v1/`;
- validation tests are tracked in the repository.

Next phase:

```text
Phase 2 - Persistence and Project Registry
```
