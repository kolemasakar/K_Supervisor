# WORKFLOW_ENGINE
Опис Phase 7 workflow engine для multi-step capability composition без прямого coupling між агентами.

Version: 1.0
Status: ACTIVE
Phase: 7

## Purpose

Workflow Engine composes multiple capability executions into one resumable workflow while keeping agent selection inside Supervisor and registries.

Core rule:

```text
Workflow -> CapabilityRequirement -> SupervisorKernel -> Registry/Router -> Agent
```

A workflow never selects or invokes a concrete agent directly.

## WorkflowDefinition

A workflow definition contains:

```text
workflow_id
workflow_version
start_node_id
nodes[]
max_steps
```

The definition is immutable as a contract instance and validated before execution.

Graph validation requires:

- unique node identifiers;
- a valid start node;
- all transition targets to exist;
- all declared nodes to be reachable from the start;
- at least one reachable END node.

## Node Types

Baseline node types are:

```text
CAPABILITY
CONDITION
APPROVAL
END
```

### CAPABILITY

A capability node contains a `CapabilityRequirement`. The engine delegates execution through `SupervisorKernel.run_task()`.

The node may read input from a deterministic dotted context path and stores the resulting JSON object under an output key.

### CONDITION

A condition node reads a boolean value from a deterministic dotted context path and selects one of two declared transitions.

No expression evaluation or arbitrary code execution is used.

### APPROVAL

An approval node pauses the workflow when no decision exists.

The persisted `WorkflowRun` enters:

```text
WAITING_FOR_APPROVAL
```

A configured `ApprovalRequester` may translate the gate into a `HumanActionRequest`. `HumanInterventionApprovalRequester` is the baseline adapter to the existing Human Intervention Broker.

After the owner action is verified and the project becomes ACTIVE again, the workflow can resume with the explicit approval decision.

### END

END terminates the workflow successfully.

## Context and Data Flow

Initial workflow input is stored as:

```text
__input__
```

Capability outputs are stored under node-defined output keys. Later nodes can consume these objects without knowing which agent produced them.

Example:

```text
analysis capability -> analysis_output
                         |
                         v
report capability <- analysis_output
```

This is capability composition, not agent-to-agent communication.

## Bounded Iteration

Loops are allowed only with deterministic bounds.

Two limits apply:

```text
WorkflowDefinition.max_steps
WorkflowNode.max_visits
```

Exceeding either bound terminates the workflow as FAILED. There is no unbounded loop mode.

## Persistence and Resume

The parent `WorkflowRun` persists:

- current node cursor;
- workflow version;
- workflow context;
- per-node visit counts;
- executed step count;
- approval request reference when present;
- terminal error when present.

The parent Task remains RUNNING while a workflow waits at an approval gate. Project operational state remains independently controlled by Human Intervention Broker.

## Delegation Model

Each CAPABILITY node creates a child task through the existing Supervisor kernel. Child task metadata links it to:

```text
parent_task_id
parent_workflow_run_id
workflow_node_id
```

This preserves existing routing, retry, Agent Contract validation, and persistence behavior rather than duplicating agent execution inside Workflow Engine.

## Phase Boundary

Phase 7 does not implement the full Agent Runtime. Timeout, cancellation, resource enforcement, runtime health, and execution isolation remain Phase 8 responsibilities.
