# PROJECT_CONTRACT
Контракт ProjectSpec для формалізації вступного обговорення, меж, доступів і цілей кожного проєкту K_Supervisor.

Version: 0.2
Status: ACTIVE
Phase: 0

## 1. Purpose

Project Contract defines the canonical ProjectSpec used to create and operate a project under K_Supervisor.

The ProjectSpec is produced from project onboarding, reviewed by the owner, and approved before autonomous project bootstrap begins.

Core rule:

```text
Onboarding discussion
-> Draft ProjectSpec
-> Owner review
-> Approved ProjectSpec
-> Automated project bootstrap
```

## 2. ProjectSpec Role

ProjectSpec is the durable contract between the owner and K_Supervisor for one project.

It defines:

- what is being built;
- why it is being built;
- success and first-working criteria;
- repository and documentation expectations;
- architecture constraints;
- required integrations and infrastructure;
- expected agents, capabilities, and workflows;
- autonomy and approval boundaries;
- notification policy;
- release targets;
- resource and risk constraints.

ProjectSpec is not a task description. A project may contain many tasks and workflow runs.

## 3. ProjectSpec Status

Baseline statuses:

```text
DRAFT
REVIEW_REQUIRED
APPROVED
REJECTED
SUPERSEDED
```

Only an `APPROVED` ProjectSpec may authorize normal automated project provisioning and bootstrap.

`SUPERSEDED` remains a logical status available to future migration or materialized-view mechanisms. The current immutable persistence model does not rewrite an already stored approved ProjectSpec merely to change its status.

## 4. ProjectSpec Identity

Required baseline identity fields:

```text
project_spec_id
project_id
spec_version
status
created_at
updated_at
approved_at
supersedes_spec_id
```

Rules:

- `project_id` remains stable for the life of the project;
- `project_spec_id` identifies one immutable approved or historical specification snapshot;
- `spec_version` increments when material project requirements change;
- an approved ProjectSpec is not silently edited in place.

## 5. Project Identity and Purpose

Baseline fields:

```text
name
short_name
purpose
problem_statement
target_users
project_type
primary_use_cases[]
out_of_scope[]
```

The onboarding process should make project boundaries explicit enough to avoid accidental scope expansion.

## 6. Success Definition

Baseline fields:

```text
success_criteria[]
first_working_criteria[]
acceptance_criteria[]
known_initial_limitations[]
```

`first_working_criteria` defines the minimum demonstrable state that triggers the `FIRST_WORKING` project milestone.

These criteria are project-specific and must be testable or verifiable where practical.

## 7. Documentation Profile

Baseline fields:

```text
documentation_standard
documentation_language
required_documents[]
architecture_decision_policy
roadmap_required
changelog_policy
```

The default K_Supervisor project profile should include at least:

```text
README.md
VISION.md or equivalent scope document
ARCHITECTURE.md
ROADMAP.md
```

Additional documents depend on project type.

## 8. Repository Profile

Baseline fields:

```text
repository_provider
repository_owner
repository_name
repository_visibility
repository_url
branch_policy
license
ci_required
```

Repository may be:

- created automatically where authorized;
- connected to an existing repository;
- created manually by the owner when platform or policy restrictions require it.

The repository is a project resource, not the ProjectSpec itself.

## 9. Architecture Profile

Baseline fields:

```text
architecture_style
runtime_constraints[]
platform_constraints[]
provider_constraints[]
security_constraints[]
compatibility_requirements[]
data_constraints[]
```

Architecture decisions derived later must remain compatible with the approved ProjectSpec or trigger an amendment when the change is material.

## 10. Agent and Capability Profile

Baseline fields:

```text
required_capabilities[]
preferred_agents[]
required_workflows[]
custom_agents_expected
agent_publication_expected
```

`preferred_agents` is advisory unless explicitly pinned.

The preferred platform design remains capability-based rather than hard-coded to specific agent implementations.

## 11. Integration and Infrastructure Profile

Baseline fields:

```text
external_services[]
servers[]
databases[]
cloud_resources[]
third_party_accounts[]
integration_dependencies[]
```

Each external dependency should indicate whether it is:

```text
REQUIRED
OPTIONAL
DEFERRED
```

and whether provisioning is:

```text
AUTOMATABLE
OWNER_ACTION_REQUIRED
UNKNOWN
```

## 12. Access and Credential Requirements

ProjectSpec may declare required access classes, but it must not contain raw secrets.

Baseline references:

```text
required_access[]
credential_refs[]
oauth_connections[]
owner_actions_required[]
```

Raw passwords, API keys, tokens, recovery codes, and private keys are prohibited in ProjectSpec.

Secrets are referenced through Secret Manager.

## 13. Autonomy and Approval Policy

Baseline fields:

```text
autonomy_level
approval_required_for[]
auto_retry_policy
side_effect_policy
irreversible_action_policy
owner_escalation_policy
```

Default principle:

```text
Automate everything that is authorized, reversible, and safely verifiable.
Escalate identity, payment, legal, high-risk, irreversible, or owner-reserved actions.
```

## 14. Notification Policy

Baseline fields:

```text
owner_email
email_notifications_enabled
immediate_event_types[]
digest_enabled
digest_schedule
future_messaging_channels[]
```

Initial implementation policy:

```text
primary_channel: EMAIL
required_initial_channels: [EMAIL]
```

WhatsApp, Viber, and other messaging channels may be declared as future preferences but are not required for the initial platform implementation.

## 15. Parallel Execution Policy

Baseline fields:

```text
allow_parallel_project_work
project_priority
max_parallel_project_tasks
max_parallel_agent_runs
resource_budget
cost_budget
```

Project-level limits are combined with global platform limits.

A blocked project does not reserve unrelated execution capacity unless an explicit policy requires it.

## 16. Release Profile

Baseline fields:

```text
release_targets[]
release_readiness_criteria[]
publication_owner
publication_mode
maintenance_expected
```

Potential release targets:

```text
GPT_STORE
API_SERVICE
WEB_APPLICATION
CLI_PACKAGE
INTERNAL_AGENT
OTHER
```

For `GPT_STORE`, K_Supervisor should prepare all feasible publication requirements automatically.

Actual publication remains a per-project owner action unless a future explicit capability and policy authorize otherwise.

## 17. Risk and Resource Profile

Baseline fields:

```text
risk_level
sensitive_data_classes[]
prohibited_actions[]
allowed_external_effects[]
compute_budget
cost_budget
time_constraints
```

Risk and resource policy may become more restrictive during execution, but must not silently become less restrictive than the approved baseline.

## 18. ProjectSpec Approval

The onboarding workflow should present a concise owner-readable summary before approval.

Approval means the owner accepts the current baseline for automated project work.

Approval does not imply approval of every future irreversible action.

Those remain subject to the project's approval and intervention policy.

## 19. Amendments

A material change requires a new ProjectSpec version.

Material changes include:

- project purpose or target users;
- major scope expansion;
- new high-risk integration;
- new release target with materially different requirements;
- major architecture constraint change;
- significant budget change;
- autonomy or permission expansion.

The previous approved ProjectSpec remains an immutable historical record. The newly approved ProjectSpec points to the previous record through `supersedes_spec_id`, and `Project.active_project_spec_id` selects the currently authoritative specification. The current persistence implementation does not mutate the old approved record to `SUPERSEDED`.

## 20. Relationship to Other Contracts

```text
ProjectSpec
  |
  +-- defines project boundaries and lifecycle policy
  |
  +-- contains many Tasks
  |      |
  |      +-- WorkflowRuns
  |             |
  |             +-- AgentRunRequests / AgentRunResults
  |
  +-- references Capabilities, Agents, Tools, Providers, Releases
```

Project Contract does not replace Agent Contract or Capability Model.

## 21. Machine Schema

Phase 0 defines the logical contract.

Phase 1 converts this document into validated machine models and schemas together with the other core platform contracts. Later phases may extend enforcement around the stable ProjectSpec boundary without silently rewriting approved historical records.
