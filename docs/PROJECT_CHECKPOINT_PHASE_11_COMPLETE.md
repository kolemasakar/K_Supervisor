# PROJECT_CHECKPOINT_PHASE_11_COMPLETE
Контрольна точка завершення Phase 11: Policy, Permissions, Risk та Approval.

Version: 1.0
Status: COMPLETE
Phase: 11

## Completed

- deterministic PolicyEffect model: ALLOW, DENY, REQUIRE_APPROVAL;
- capability RiskClass model: LOW, MEDIUM, HIGH, CRITICAL;
- canonical side-effect permission classes;
- project policy resolution from the active approved ProjectSpec;
- restrictive workflow policy overlays;
- capability allow/deny constraints;
- side-effect allow/approval/deny constraints;
- per-agent tool-operation permissions;
- protected access-reference allowlists;
- least-privilege execution context;
- PolicyEnforcedDispatcher before the concrete AgentDispatcher;
- normalized policy blocks as AgentRunResult BLOCKED / POLICY_BLOCKED;
- Supervisor Task and WorkflowRun preservation of BLOCKED state;
- PolicyApprovalBroker integrated with HumanInterventionBroker;
- durable ApprovalRecord with exact permission-scope hash;
- WAITING_FOR_OWNER while explicit material permission approval is pending;
- approved exact scope reuse for equivalent future work;
- durable rejected scope without repeated approval prompts;
- append-only PolicyDecision audit events in platform persistence;
- policy audit survives SQLite restart;
- tool and protected-access enforcement helpers against the resolved execution context;
- Core Validation trigger includes `policy/**`;
- `docs/POLICY_AND_PERMISSIONS.md` added.

## Validation

The committed Phase 11 implementation was validated with GitHub Actions on Python 3.13.15.

```text
63 passed in 1.45s
```

This includes Phase 1-11 regression coverage.

## Exit Criteria

```text
prohibited operations are blocked before downstream agent execution: PASS
material permission expansion requires explicit approval: PASS
capability risk and side effects come from registered descriptors: PASS
workflow policy cannot expand project permissions: PASS
per-agent tool permissions are machine-resolved: PASS
protected access references are least-privilege scoped: PASS
policy-blocked work remains BLOCKED rather than FAILED: PASS
policy decisions are durably auditable without hidden chain-of-thought: PASS
```

## Architecture Notes

Production controlled execution composes:

```text
SupervisorKernel
  -> PolicyEnforcedDispatcher
      -> PolicyEngine
      -> Policy audit
      -> PolicyApprovalBroker when required
      -> concrete AgentDispatcher only on ALLOW
```

Approval is bound to an exact deterministic permission scope for project, agent, capability/version, operation, risk class, side effects, tool permissions, and protected access references. Equivalent later work may reuse an approved scope. Phase 11 does not implement approval expiry or revocation.

The policy layer resolves and checks per-agent tool permissions and provides `require_tool_operation()` for invocation boundaries. A universal centralized Tool Gateway is not claimed by Phase 11 and remains a later integration refinement.

Approval/HumanAction/project-state writes are conservatively ordered but are not one SQLite transaction. An interrupted transition cannot broaden authority: the durable ApprovalRecord remains non-approved until the approval write succeeds.

## Next

Phase 12 - Reference Agents and Agent Factory.
