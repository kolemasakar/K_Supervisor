# VISION
Бачення K_Supervisor як системи автоматизованого життєвого циклу AI-проєктів і модульної мультиагентної платформи.

Version: 0.2
Status: ACTIVE
Phase: 0

## 1. Vision

K_Supervisor is an AI Project Lifecycle Supervisor built on a domain-neutral Modular Multi-Agent Platform.

Its goal is to automate as much of the creation, development, validation, and release preparation of AI projects and agents as safely and technically possible.

The system combines:

```text
Project Lifecycle Control Plane
+
Modular Multi-Agent Execution Core
```

The Control Plane manages projects.
The Multi-Agent Core performs project work.

## 2. Primary User Experience

A new project begins with an onboarding conversation.

The onboarding process should establish:

- project concept and boundaries;
- target users and intended outcomes;
- documentation profile;
- repository ownership and access;
- roadmap expectations;
- required agents and capabilities;
- external services, servers, databases, and accounts;
- required access and owner actions;
- autonomy and approval policy;
- notification policy;
- release targets;
- first-working and success criteria.

The structured result is a Draft ProjectSpec.

After owner approval, K_Supervisor should automate the project lifecycle within the approved boundaries.

## 3. Project Automation Goal

The long-term project flow is:

```text
Onboarding
-> ProjectSpec approval
-> Provisioning
-> Repository/bootstrap
-> Roadmap execution
-> Agent/workflow creation
-> Validation
-> FIRST_WORKING
-> Release preparation
-> RELEASE_READY
-> Owner publication when required
-> Maintenance
```

K_Supervisor should request owner intervention only when automation is unavailable, inappropriate, restricted, high-risk, irreversible, or explicitly owner-reserved.

## 4. Platform Identity

```text
Project: K_Supervisor
Repository: kolemasakar/K_Supervisor
Product type: AI Project Lifecycle Supervisor + Modular Multi-Agent Platform
Architecture style: control-plane managed, contract-driven, capability-based, supervisor-orchestrated
Roadmap origin: Phase 0
```

## 5. Project Control Plane

The baseline Control Plane includes:

```text
Project Factory
Project Registry
Project Scheduler
Human Intervention Broker
Notification Broker
Secret Manager
Release Manager
```

The Control Plane is responsible for long-lived project state and project lifecycle coordination.

It does not perform specialized domain work directly.

## 6. Modular Multi-Agent Core

The execution core provides:

- Supervisor orchestration;
- Agent Contract;
- Capability Model;
- Agent and Capability registries;
- capability discovery and routing;
- composable workflows;
- controlled agent execution;
- tool and provider adapters;
- task, workflow, run, and artifact state;
- policy and permission enforcement;
- auditability.

A workflow should request capabilities rather than hard-code agent implementations.

## 7. Core Architectural Rule

```text
Project != Task
Agent != Capability
Lifecycle state != Operational state
Notification delivery != Owner action completion
Release readiness != Publication
```

These distinctions are required for reliable automation and parallel project work.

## 8. Parallel Project Operation

Parallel work across independent projects is a first-class requirement.

A project waiting for owner action or an external dependency must not block unrelated projects.

K_Supervisor must preserve project-level isolation for:

- state;
- workspaces;
- credentials;
- budgets;
- locks;
- logs and audit records;
- tasks and agent runs.

Global concurrency and resource policies may limit total activity.

## 9. Human Intervention

Human intervention is a structured platform mechanism, not an ad-hoc chat interruption.

The Human Intervention Broker creates explicit HumanActionRequests for situations such as:

- owner approval;
- access or account setup that cannot be automated;
- identity or interactive verification;
- payments or subscriptions;
- legal acceptance;
- high-risk or irreversible operations;
- owner-reserved publication actions.

The affected project may wait while other projects continue.

When possible, K_Supervisor should verify completion automatically and resume work without requiring a separate owner confirmation message.

## 10. Notification Strategy

Email is the first and primary owner notification channel.

The initial platform implementation requires only email delivery.

Future messaging integrations such as WhatsApp, Viber, or other channels are planned extension points but are intentionally deferred.

Agents and workflows must emit transport-neutral NotificationEvents and must not depend directly on a specific communication channel.

## 11. Secret Strategy

Secrets must not be stored in project documentation, repositories, notification bodies, or agent descriptors.

Projects and platform components use secret references through a replaceable Secret Manager boundary.

## 12. Release and GPT Store Strategy

Release Manager treats publication destinations as release targets.

Potential targets include:

```text
GPT Store
API service
web application
CLI/package
internal agent
other targets
```

For GPT Store projects, K_Supervisor should automate all feasible preparation and validation needed to reach publication readiness.

Automatic publication is not required.

Publication remains a separate per-project owner action unless a future explicitly approved capability changes that boundary.

## 13. First Working State

Each project defines measurable first-working criteria in ProjectSpec.

`FIRST_WORKING` means the primary intended project function is demonstrably operational under the approved minimum criteria.

It is a milestone, not necessarily a production release.

Reaching FIRST_WORKING should normally trigger an owner email and a release-readiness assessment.

## 14. Strategic Separation

K_Supervisor is separate from K-Research & Critic.

K-Research & Critic v1.0.0 remains a completed production reference product.

K_Supervisor may reuse validated architectural lessons and behavior patterns, but must not inherit the old runtime as its architecture baseline.

A Research-Critic system should later be expressed as one reference workflow on top of K_Supervisor contracts and capabilities.

## 15. Platform Qualities

K_Supervisor prioritizes:

- maximum safe automation;
- modularity;
- explicit contracts;
- replaceability;
- project isolation;
- parallelism;
- interoperability;
- controlled autonomy;
- auditability;
- resumability;
- testability;
- provider independence;
- failure isolation;
- deterministic boundaries around non-deterministic AI behavior;
- versioned evolution.

## 16. Non-Goals for the Core

The core must not:

- hard-code one project type or domain;
- make ResearchAgent or CriticAgent mandatory roles;
- require one LLM provider;
- require direct agent-to-agent implementation coupling;
- expose secrets in ordinary project state;
- persist hidden chain-of-thought;
- assume every project has the same roadmap or release target;
- silently expand permissions;
- treat GPT Store publication as automatic by default.

## 17. Success Definition

K_Supervisor reaches its product objective when an owner can approve a structured project concept and the platform can independently bootstrap, coordinate, implement, validate, and prepare that project for release while using owner intervention only at explicit boundaries.

At the same time, multiple independent projects must be able to progress concurrently through the same reusable multi-agent platform without requiring Supervisor-core rewrites for each new project or agent type.
