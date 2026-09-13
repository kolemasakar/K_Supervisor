# REFERENCE_RESEARCH_CRITIC_WORKFLOW
Референсна композиція поведінки K-Research & Critic v1.0.0 на нових контрактах K_Supervisor.

Version: 1.0
Status: ACTIVE
Phase: 14
Reference: `kolemasakar/K_Research_Critic` tag `v1.0.0`, commit `815ddc35ea2c90304119fb3f7d5e8741848cc88b`

## Purpose

Phase 14 proves that the essential Research-Critic behavior can be expressed through K_Supervisor capabilities, registries, Supervisor routing, runtime execution, durable workflow context, and explicit owner approval without importing the legacy runtime.

## Reference Behavior

The v1.0.0 reference establishes this control sequence:

```text
user task
  -> task-specific CriticProfile proposal
  -> explicit owner approve/edit
  -> frozen approved profile
  -> ResearchAgent
  -> independent CriticAgent verification
  -> PASS or REVISE
  -> bounded autonomous revision loop
  -> final report + review protocol
```

Research must not start before profile approval. Normal revision cycles after approval do not require repeated owner confirmation. Acceptance requires the critic result and configured reliability threshold. Hitting the iteration limit must not be treated as approval.

## K_Supervisor Composition

The Phase 14 implementation is `workflows/reference_loop.py` and uses existing Phase 12 capabilities:

```text
research.reference
factcheck.reference
critique.reference
report.reference
```

No concrete agent identity is embedded in the reference workflow. Every capability execution goes through:

```text
ReferenceResearchReviewWorkflow
  -> SupervisorKernel.run_task()
  -> AgentRegistry / CapabilityRegistry
  -> ProviderRouter
  -> AgentRuntimeDispatcher
  -> AgentRunResult
```

This preserves provider replaceability. In particular, `research.reference@1.0.0` already has two interchangeable providers.

## Profile Approval Boundary

`start()` creates a task-specific review profile with status `REVIEW_REQUIRED` and persists it in the parent `WorkflowRun` context. The workflow stops at `WAITING_FOR_APPROVAL`, and no agent execution occurs before the owner approves the profile.

`approve_profile()` supports owner edits to the reviewable profile while protecting profile identity and approval fields. The approved value receives approver and timestamp metadata and a SHA-256 fingerprint. `StructuredApprovalRecord` provides the reusable structured approval record used for this boundary.

The approved profile fingerprint is checked before successful finalization so autonomous execution cannot silently mutate the approved control object.

## Independent Review and Revision

After approval, each iteration performs:

```text
Research capability
  -> independent FactCheck capability
  -> Critique capability
  -> acceptance check
```

A failing critique creates a `REVISE` review entry and the next research iteration uses the configured revision evidence. The loop is bounded by `max_iterations`.

Each review history item records iteration, research/fact-check/critique run identifiers, selected research and critic agent identifiers, verdict, reliability score, issues, and fact-check verdict. This is audit data, not private chain-of-thought.

On `PASS` with reliability at or above the approved threshold, `report.reference` generates the final report and review protocol. The review protocol contains only structured outcome data and does not store hidden reasoning.

## Iteration Limit

If acceptance is not reached within `max_iterations`, the workflow records:

```text
reference_status = MAX_ITERATIONS_REACHED
```

and ends as failed. No final approved result is generated.

## Intentional Differences from v1.0.0

The Phase 14 reference is a contract/integration demonstration rather than a port of the legacy product:

- the task-specific profile is stored in durable `WorkflowRun` context instead of a dedicated legacy CriticProfile persistence subsystem;
- profile proposal is deterministic workflow input normalization rather than the legacy DomainResolver/ProfileManager implementation;
- material profile amendment/re-approval is not implemented in this baseline;
- evidence is supplied to deterministic reference agents rather than collected by production web/LLM research providers;
- independent verification uses the generic `factcheck.reference` capability in addition to `critique.reference`;
- the generic K_Supervisor Task state model has no `COMPLETED_WITH_LIMITATIONS`; therefore an exhausted revision loop records `MAX_ITERATIONS_REACHED` and fails instead of silently approximating the legacy partial-completion state;
- final report and review protocol are returned in durable workflow context rather than written as legacy artifact files in this phase;
- legacy runtime classes, persistence schema, configuration, prompts, and imports are not dependencies.

These differences are intentional and must not be described as behavior already implemented elsewhere in K_Supervisor.

## Validation

Phase 14 regression tests verify:

```text
mandatory profile approval gate before any AgentRun
owner profile edits preserved
REVISE -> revised research -> PASS
research and critic resolve to different agent identities
bounded iteration limit with no false approval
final report and review protocol generation
absence of legacy runtime imports
```

Final clean Core Validation baseline:

```text
run: 34781252658
head SHA: 04de1361a6c33eca84879f962c515ab1c1e6d93c
Python: 3.13.15
pytest: 75 passed
conclusion: SUCCESS
```

## ROADMAP Result

Phase 14 exit criteria are satisfied:

```text
required behavior is expressed through new contracts and registries: PASS
no direct legacy runtime dependency exists: PASS
```
