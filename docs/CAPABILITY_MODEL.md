# CAPABILITY_MODEL
Модель декларації, реєстрації, сумісності та маршрутизації функціональних можливостей агентів K_Supervisor.

Version: 0.1
Status: ACTIVE
Phase: 0

## 1. Purpose

The Capability Model defines what the platform can ask an agent or executor to do independently of which implementation performs the work.

A capability is a versioned declarative contract, not an agent.

Core relation:

```text
Agent provides Capability
Workflow requires Capability
Supervisor matches Requirement to Provider
```

## 2. Why Capabilities Are First-Class

Hard-coding workflow nodes to concrete agents makes the Supervisor responsible for implementation details.

First-class capabilities allow:

- multiple agents to provide the same function;
- one agent to provide multiple functions;
- routing by compatibility and policy;
- later replacement of providers;
- domain growth without Supervisor rewrites;
- explicit tool, trust, risk, and side-effect requirements.

## 3. Capability Identifier

Capability identifiers use lowercase dot-separated namespaces.

Examples:

```text
research.web
critique.independent
source.verify
report.generate
data.tabular.analyze
engineering.geodesy.validate
```

Rules:

- identifiers describe function, not implementation;
- provider names do not belong in the identifier;
- breaking semantics require a new major version;
- specialized sub-capabilities may extend a namespace.

## 4. Capability Descriptor

Baseline fields:

```text
capability_id
capability_version
description
operations[]
input_schema
output_schema
constraints
requires[]
side_effects[]
risk_class
trust_requirements
resource_profile
metadata
```

Logical example:

```json
{
  "capability_id": "critique.independent",
  "capability_version": "1.0",
  "description": "Independent structured review of supplied work",
  "operations": ["review"],
  "input_schema": "schema://critique.independent/input/1.0",
  "output_schema": "schema://critique.independent/output/1.0",
  "constraints": {},
  "requires": [],
  "side_effects": ["NONE"],
  "risk_class": "LOW",
  "trust_requirements": {},
  "resource_profile": {},
  "metadata": {}
}
```

## 5. Capability Requirement

A workflow requests work through CapabilityRequirement.

Baseline fields:

```text
capability_id
version_constraint
operation
required_inputs
required_outputs
hard_constraints
preferences
policy_context
```

Example:

```json
{
  "capability_id": "research.web",
  "version_constraint": ">=1.0,<2.0",
  "operation": "research",
  "required_inputs": {},
  "required_outputs": {},
  "hard_constraints": {},
  "preferences": {},
  "policy_context": {}
}
```

## 6. Provider Declaration

AgentDescriptor references capabilities provided by the agent.

A provider declaration may add implementation-specific operating metadata such as:

```text
quality_class
cost_class
latency_class
supported_languages
supported_regions
provider_dependencies
tool_dependencies
execution_environment
```

These values may influence routing but must not redefine the capability contract.

## 7. Capability Compatibility

Compatibility is determined before preference scoring.

A candidate is eligible only when all hard requirements pass.

Hard checks may include:

```text
identifier match
version compatibility
operation support
input schema compatibility
output schema compatibility
policy permission
side-effect permission
required tool availability
required provider availability
risk/trust threshold
execution environment
availability state
```

If a hard check fails, scoring must not make the candidate eligible.

## 8. Routing Model

Logical routing sequence:

```text
1. Workflow emits CapabilityRequirement.
2. CapabilityRegistry resolves the requested capability contract.
3. AgentRegistry returns providers declaring compatible capability versions.
4. Policy layer removes forbidden candidates.
5. Dependency checks remove unavailable candidates.
6. Router scores remaining candidates by preferences.
7. Supervisor selects one candidate or returns NO_ELIGIBLE_PROVIDER.
8. AgentRunRequest is created under Agent Contract.
9. Result and routing decision are audited.
```

## 9. Preference Scoring

Preference scoring may consider:

```text
quality
latency
cost
historical reliability
locality
provider preference
model class
specialization
resource availability
```

The initial scoring algorithm must remain replaceable. Routing policy should not be embedded in capability descriptors.

## 10. Risk Model

Baseline capability risk classes:

```text
NONE
LOW
MODERATE
HIGH
CRITICAL
```

Risk class describes the inherent potential impact of executing the capability, especially when side effects exist.

Task-specific policy may raise required controls beyond the default capability risk class.

## 11. Side-Effect Model

Baseline side effects:

```text
NONE
READ_EXTERNAL
WRITE_EXTERNAL
SEND_MESSAGE
CREATE_RESOURCE
MODIFY_RESOURCE
DELETE_RESOURCE
EXECUTE_CODE
```

A capability may declare multiple side effects.

Side-effect declaration is used by policy and approval logic before execution.

## 12. Dependency Model

Dependencies are explicit and typed.

Examples:

```text
tool:web_search
provider:llm
storage:artifact_store
capability:source.verify
runtime:python
```

A capability dependency does not authorize direct agent-to-agent calls. Required capabilities are resolved by the platform.

## 13. Capability Composition

Complex workflows are built by composing capabilities.

Example Research-Critic composition:

```text
research.web
-> source.verify
-> critique.independent
-> report.generate
```

This composition is a workflow definition, not a special Supervisor implementation.

## 14. Capability Profiles

A workflow may attach a domain or task profile to a capability request.

Examples:

```text
critic profile
source policy
engineering standard set
financial risk policy
language profile
```

Profiles configure execution but do not change the base capability identifier.

## 15. Discovery API Direction

The initial logical registry API is:

```text
register_capability(descriptor)
register_provider(agent_id, capability_id, version)
get_capability(capability_id, version)
find_providers(requirement)
validate_candidate(requirement, agent_id)
list_capabilities()
```

Concrete schemas and Python interfaces are Phase 1 deliverables.

## 16. Versioning

Capability versions use semantic compatibility principles.

```text
MAJOR: breaking contract or semantic change
MINOR: backward-compatible extension
PATCH: clarification or implementation-neutral correction
```

Phase 0 uses document version `0.1`. Machine capability schema version `1.0` will be frozen in Phase 1.
