# REGISTRIES
Реєстри агентів і capabilities забезпечують динамічне discovery без жорстких залежностей Supervisor від конкретних реалізацій.

Version: 1.0
Status: ACTIVE
Phase: 4

## 1. Purpose

Phase 4 introduces two separate registry responsibilities:

```text
CapabilityRegistry -> what work contracts exist
AgentRegistry      -> which agents provide those contracts now
```

Supervisor and later routing code must query registries rather than import concrete agent implementations.

## 2. Capability Registry

`CapabilityRegistry` stores immutable `CapabilityDescriptor` values by:

```text
(capability_id, capability_version)
```

Registration rules:

- registering the same descriptor again is idempotent;
- registering different content under the same id/version is a conflict;
- capability versions use the Phase 4 numeric semantic-version baseline;
- unregistration removes one exact capability version.

Resolution supports:

```text
*
1.2.3
>=1.2,<2
^1.2.0
~1.2.0
```

The highest compatible version is returned.

## 3. Requirement Compatibility

`CapabilityRequirement` compatibility is evaluated using hard conditions only:

- capability id;
- version constraint;
- operation;
- hard constraints.

Hard constraints are eligibility boundaries. A scalar requirement must equal the provided value. When a capability advertises a collection, required values must be contained in that collection.

`preferences` do not affect Phase 4 eligibility. Preference scoring and ranking belong to the Phase 5 routing layer.

## 4. Agent Registry

`AgentRegistry` stores `AgentDescriptor` values by unique `agent_id`.

Registration requires every declared `CapabilityRef` to reference an already registered exact capability version.

Rules:

- identical repeat registration is idempotent;
- different descriptors using the same `agent_id` are rejected;
- unregistering an agent removes it from provider discovery without Supervisor changes.

## 5. Provider Registration

There is no independent mutable provider table in the Phase 4 baseline.

Provider registrations are derived from:

```text
AgentDescriptor.capabilities[]
+
CapabilityRegistry
+
AgentRegistry availability
```

This avoids drift between an agent descriptor and a separate provider declaration.

## 6. Availability

Runtime registry availability is kept separate from the immutable AgentDescriptor snapshot.

Baseline states:

```text
REGISTERED
AVAILABLE
BUSY
DEGRADED
UNAVAILABLE
```

Default provider discovery includes only `AVAILABLE` agents.

`DEGRADED` providers may be included explicitly. `BUSY`, `REGISTERED`, and `UNAVAILABLE` agents are not eligible by default.

## 7. Provider Discovery

`AgentRegistry.find_providers(requirement)` returns compatible providers after hard filtering.

The result is deterministic and ordered primarily by compatible capability version. This ordering is not the final routing policy.

Phase 5 may rank eligible candidates using preferences, policy, cost, trust, latency, load, or other routing signals.

## 8. Persistence Boundary

Phase 4 registries are in-memory runtime registries.

Durable project state remains owned by the Phase 2 persistence layer. Durable plugin/config based registry reconstruction is deferred to later extensibility and runtime phases.

The core registry APIs remain storage-neutral so a persistent implementation can be added without changing Supervisor contracts.

## 9. Validation

Phase 4 tests cover:

- semantic version constraints;
- highest-compatible capability resolution;
- capability registration conflicts;
- missing capability rejection during agent registration;
- duplicate agent id conflicts;
- availability filtering;
- hard constraint filtering;
- optional degraded-provider discovery;
- agent removal without Supervisor redesign.

GitHub Actions validation at Phase 4 completion:

```text
25 passed
```

## 10. Phase Boundary

Phase 4 does not dispatch agents and does not implement final routing decisions.

Next responsibility:

```text
Phase 5 - Supervisor Orchestration Kernel
```
