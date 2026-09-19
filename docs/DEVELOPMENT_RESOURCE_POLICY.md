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

## Paid Provider Boundary

K_Supervisor may implement and support adapters for providers that offer paid production services. Supporting such a provider does not authorize spending money during project development.

Paid-only provider access is a deployment/operator option, not a development prerequisite. Product architecture must preserve provider independence and must provide a zero-cost development and validation path.

## Verification Rule

When a live external check is available at zero cost, it may be used as supplemental evidence.

When successful live evidence requires payment, the paid live check is non-blocking. Required development evidence must instead come from deterministic contract tests, policy/side-effect boundary tests, safe failure normalization, local integration tests, or a no-cost provider/service path.

A real-provider reachability attempt that safely terminates at authentication, quota, billing or another provider-controlled gate may be retained as supplemental evidence, but the project must not purchase access solely to convert that attempt into a successful phase gate.

## Hosted CI Quota Exhaustion

When an included hosted-CI quota is exhausted and further hosted execution may create a charge, new hosted CI runs are not authorized under this policy.

During such a quota-exhaustion window:

- local deterministic tests, compile checks, packaging checks and documentation work may continue on owner-controlled zero-cost resources;
- branches and commits may be prepared only when doing so does not trigger paid hosted execution;
- pull requests, manual workflow dispatches, reruns or other actions that would start potentially billable hosted CI must be deferred;
- required protected-CI gates remain mandatory and must not be bypassed or weakened;
- the affected protected merge/completion gate remains pending until included/free CI capacity is available again or another explicitly verified zero-cost protected runner path is approved;
- later work should be batched to reduce unnecessary hosted-CI invocations while preserving required protected validation.

On 2026-09-19 the owner reported GitHub Actions included usage at 2,000 / 2,000 minutes. The account UI indicated that further usage may be billed and that included usage resets on 2026-10-01. K_Supervisor therefore treats new GitHub-hosted Actions runs as unavailable for zero-cost development until no-cost capacity is confirmed again.

## Scope and Precedence

This policy applies to current and future roadmap phases unless the owner explicitly approves a later written amendment.

Historical evidence remains factual and is not rewritten.

Where an older roadmap, test matrix, hardening baseline or handoff requires paid external evidence for phase completion, this policy supersedes that requirement only to the extent necessary to remove the paid dependency. Security, credential protection, policy enforcement, protected-main governance and deterministic quality gates remain unchanged.
