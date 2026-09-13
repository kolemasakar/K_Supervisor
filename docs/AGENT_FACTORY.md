# AGENT_FACTORY
Фабрика агентів, scaffolding та reference implementations для перевірки спільного Agent Contract.

Version: 1.0
Status: ACTIVE
Phase: 12

## Purpose

Phase 12 validates that K_Supervisor can create, register, bind and execute new agents without modifying Supervisor core or hard-coding concrete implementations into routing.

The implementation is split into two layers:

```text
agent_factory/
  contracts.py
  factory.py
  scaffolder.py

agents/
  reference.py
  catalog.py
```

## AgentBlueprint

`AgentBlueprint` is the declarative source for one agent implementation. It contains:

- stable `agent_id` and `agent_type`;
- agent and Agent Contract versions;
- display/class metadata;
- one or more `CapabilityBlueprint` records;
- execution mode and initial availability.

`CapabilityBlueprint` declares:

- capability identity/version;
- operations;
- input/output schema references;
- constraints and dependencies;
- side effects and risk class.

The factory converts these declarations into the existing Phase 1 machine contracts rather than introducing parallel runtime contracts.

## AgentFactory

`AgentFactory.build()` produces:

```text
CapabilityDescriptor[]
AgentDescriptor
```

`AgentFactory.register()` then:

1. registers capability descriptors in `CapabilityRegistry`;
2. registers the agent in `AgentRegistry`;
3. optionally binds its handler through a generic runtime binding target.

The current runtime binding target is compatible with `InProcessRuntimeAdapter.register(agent_id, handler)`. SupervisorKernel, ProviderRouter and AgentRuntimeDispatcher remain unchanged.

## Scaffolder

`AgentScaffolder` deterministically generates:

```text
agent.py
test_agent.py
README.md
```

Generated Python is syntax-validated before writing. Writes are idempotent when existing content is identical and fail with `ScaffoldConflictError` when an existing file differs, preventing silent overwrite of owner-authored work.

The generated handler already conforms to:

```text
AgentRunRequest + ExecutionControl -> AgentRunResult
```

but deliberately returns a warning that domain behavior still requires implementation.

## Reference Agents

Phase 12 includes deterministic offline reference handlers:

- `ResearchAgent`;
- `CriticAgent`;
- `ReportAgent`;
- `DataAnalysisAgent`;
- `FactCheckAgent`.

These implementations are contract examples and integration fixtures. They are not presented as production-quality research, critique, reporting, analytics or fact-checking intelligence.

Reference capabilities are side-effect free and LOW risk.

## Interchangeable Providers

`research.reference@1.0.0` is registered by two independent agent identities:

```text
reference.research.alpha
reference.research.beta
```

Both expose the same capability/version/operation contract. Normal AgentRegistry/ProviderRouter behavior selects among them. If Alpha becomes unavailable, Beta remains eligible without Supervisor changes.

This demonstrates capability-oriented replaceability rather than direct agent coupling.

## Validation

Phase 12 integration tests prove:

- at least five distinct reference agent types use Agent Contract `1.0`;
- Critic, Report and DataAnalysis execute through Supervisor + AgentRuntimeDispatcher;
- `research.reference` has two eligible providers;
- provider fallback works after one provider becomes unavailable;
- a new custom Echo agent can be described by blueprint, scaffolded, syntax-validated, registered, runtime-bound and executed through Supervisor;
- generated scaffold writes are idempotent.

Core Validation baseline at Phase 12 completion:

```text
Python 3.13.15
66 tests PASS
```

## Boundaries

Phase 12 does not add vendor LLM calls, hidden agent-to-agent imports or a second routing system. Real model-backed reference implementations can be introduced later behind existing Provider/Tool/Policy boundaries.

The scaffolder generates a minimum compliant starting point; it does not claim to infer domain-specific schemas, tools, permissions, evaluations or production-quality prompts automatically.
