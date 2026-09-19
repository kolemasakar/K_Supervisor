# DEVELOPMENT_RESOURCE_POLICY

Permanent development-resource policy for K_Supervisor.

Version: 1.1
Status: ACTIVE
Date: 2026-09-19
Authority: owner-approved project invariant

## Policy

K_Supervisor development, testing, CI, validation, smoke testing and qualification must use resources that are free to the project owner at the time they are required.

A roadmap phase, test gate or acceptance criterion must not require purchasing credits, starting a paid subscription, upgrading a plan, renting paid infrastructure, or otherwise incurring a new project-attributable external-service charge.

## Allowed Development Resources

Allowed resources include:

- local owner-controlled hardware and local open-source tooling;
- free/open-source software and libraries;
- free service tiers or free grants that require no purchase to execute the approved development/validation step;
- repository/CI capabilities available at no additional project-attributable charge;
- deterministic fakes, fixtures, emulators and local test doubles for external providers;
- externally hosted services only when the required operation is available without payment.


## CI Capacity and Self-Hosted Runner Rule

Exhaustion of included GitHub-hosted Actions minutes does not authorize paid Actions usage or weakening protected-main validation.

When included hosted CI capacity is unavailable, the project may migrate required validation to owner-controlled self-hosted infrastructure only when all of the following remain true:

- the required quality gate and status context are preserved;
- the self-hosted runtime is repository-scoped and least-privileged;
- CI runtime credentials are isolated from unrelated production secrets and administration credentials;
- privileged bootstrap is bounded and separated from normal runner execution;
- the runner cannot materially displace an existing production workload; enforce resource guardrails when sharing a host;
- migration and rollback are documented before changing the protected workflow;
- no new project-attributable paid service is required.

For the current K_Supervisor migration, the canonical architecture and acceptance contract is `PROJECT_CHECKPOINT_SELF_HOSTED_CI_MIGRATION_APPROVED_2026_09_19.md`.

## Paid Provider Boundary

K_Supervisor may implement and support adapters for providers that offer paid production services. Supporting such a provider does not authorize spending money during project development.

Paid-only provider access is a deployment/operator option, not a development prerequisite. Product architecture must preserve provider independence and must provide a zero-cost development and validation path.

## Verification Rule

When a live external check is available at zero cost, it may be used as supplemental evidence.

When successful live evidence requires payment, the paid live check is non-blocking. Required development evidence must instead come from deterministic contract tests, policy/side-effect boundary tests, safe failure normalization, local integration tests, or a no-cost provider/service path.

A real-provider reachability attempt that safely terminates at authentication, quota, billing or another provider-controlled gate may be retained as supplemental evidence, but the project must not purchase access solely to convert that attempt into a successful phase gate.

## Scope and Precedence

This policy applies to current and future roadmap phases unless the owner explicitly approves a later written amendment.

Historical evidence remains factual and is not rewritten.

Where an older roadmap, test matrix, hardening baseline or handoff requires paid external evidence for phase completion, this policy supersedes that requirement only to the extent necessary to remove the paid dependency. Security, credential protection, policy enforcement, protected-main governance and deterministic quality gates remain unchanged.
