# V0_4_PHASE7_PREIMPLEMENTATION_AUDIT

Pre-implementation audit for ROADMAP v0.4 Phase 7 — End-to-End Single-Node Product Qualification.

Version: 1.0
Status: COMPLETE — ACTIVATION PENDING
Date: 2026-09-23
Baseline main: bbf74fb68690a4f9b802d03fad50071eb50b6aec
Baseline tree: cb495f41f1bef2d8a0a38fa51eb043998758bde4
Validated runtime predecessor: bbf74fb68690a4f9b802d03fad50071eb50b6aec
Merged-main Core Validation: 35812514286 — PASS
Merged-main Supply Chain Attestation: 35812514276 — PASS
Runtime implementation authorized by this document: NO

## 1. Scope Authority

Phase 7 is the final ROADMAP v0.4 product qualification phase. It must prove the complete supported single-node owner/operator lifecycle without silently expanding the product into distributed execution or automatic publication.

Authorized implementation scope only after a separate owner activation checkpoint:

- close only integration/composition gaps that currently prevent the already-approved Phase 1-6 capabilities from being exercised through the production single-node Service/API/CLI composition;
- provide production composition of the existing governed MODEL path using the already-implemented MODEL provider, policy, SideEffectGateway, model selection and ModelBackedAgent contracts;
- wire the existing ReleaseManager into the production ServiceRuntime/ServiceApiV1 composition;
- add an explicit idempotent owner/operator release-preparation operation only if required to make FIRST_WORKING -> RELEASE_READY reachable through the supported API/CLI boundary;
- reuse ProjectFactory and governed repository adapters for release preparation rather than introducing a second repository control plane;
- add deterministic composition-level transport injection seams for protected CI where existing production adapters already support transport injection;
- implement full installed-wheel end-to-end qualification through API/CLI;
- qualify restart/reopen, backup/restore/upgrade, owner intervention, concurrency/isolation, telemetry/failure handling and release/package generation across the integrated path;
- synchronize final operations/product documentation and create the ROADMAP v0.4 completion checkpoint.

Explicitly outside Phase 7:

- new distributed worker or service topology;
- remote-agent federation;
- multi-node persistence, consensus or cross-region replication;
- new multi-tenant SaaS identity/billing;
- new broad cloud/server/database provisioning;
- automatic protected-branch merge;
- automatic PyPI, Plugin Directory, GPT Store or marketplace publication;
- provider-account OAuth on behalf of the owner;
- mandatory paid model/GitHub/observability services;
- mandatory external collector/SaaS;
- arbitrary untrusted-Python sandboxing;
- changing the owner publication boundary;
- redesigning the already-delivered Phase 1-6 domain contracts merely for test convenience.

`DEVELOPMENT_RESOURCE_POLICY.md` remains authoritative.

## 2. Frozen Phase 6 Predecessor

ROADMAP v0.4 Phase 6 is COMPLETE.

```text
Phase 6 completion merge main: bbf74fb68690a4f9b802d03fad50071eb50b6aec
Merged-main Core Validation: 35812514286 — PASS
Merged-main Supply Chain Attestation: 35812514276 — PASS
Qualification PR: #59
Qualification code/test head: 79024500a0e0dd03f898c3677683bf1e5a4dc60a
Python 3.13.15: 362 passed / 80.74% coverage
Python 3.14.7: 362 passed / 80.09% coverage
coverage gate >=80%: PASS on both supported stable minors
installed-wheel Phase 3/4/5/6 smokes: PASS
deterministic SPDX 2.3 evidence: PASS
machine-readable vulnerability evidence: PASS
trusted-main provenance/SBOM attestations: PASS
```

No Phase 7 runtime/source/test implementation exists at audit start.

## 3. Existing v0.4 Compatibility Floor

Phase 7 must compose and qualify, not replace, the completed Phase 1-6 surfaces.

Existing production/runtime boundaries include:

- ProjectRegistry lifecycle and operational authority;
- immutable ProjectSpec submission/approval/activation;
- HumanInterventionBroker and PolicyApprovalBroker;
- SupervisorKernel Task/Workflow execution;
- OpenAIResponsesProvider, PriorityModelSelector, ModelBackedAgent and SideEffectGateway;
- versioned ServiceApiV1, WSGI host, ServiceClientV1 and operator CLI;
- ProjectFactory with filesystem and governed GitHub repository adapters;
- GitHub provider policy/access-reference/idempotency/recovery handling;
- ReleaseManager, Plugin-native CHATGPT_PLUGIN packaging and owner publication handoff;
- SQLite online backup/restore/upgrade qualification;
- ProjectScheduler concurrency/isolation;
- structured production observability and bounded exporter semantics;
- Python 3.13/3.14 compatibility, deterministic dependency locks, SBOM/vulnerability evidence and trusted-main attestations.

Permanent compatibility invariants:

```text
API base path = /api/v1
config_version = 1
RELEASE_READY != externally published
publication remains explicit owner/workspace action
external provider credentials remain protected references
telemetry failure remains non-authoritative
protected main requires Core Validation
zero-cost development/qualification remains mandatory
```

## 4. Existing Qualification Evidence That Can Be Reused

The repository already proves many Phase 7 sub-properties separately.

### Service / operator

Existing tests prove:

- installed service startup/health/readiness;
- authenticated API access and CLI-over-HTTP behavior;
- graceful shutdown and SQLite reopen/integrity;
- trusted-proxy fail-closed behavior;
- durable idempotent command replay after restart.

### Repository

Existing tests prove:

- Service/API repository status/bootstrap;
- governed GitHub provider operations and normalized failures;
- policy/approval/access-reference enforcement;
- bootstrap replay/recovery and conflict safety;
- owner-action fallback.

### Model execution

Existing tests prove:

- non-reference ModelBackedAgent execution through OpenAIResponsesProvider;
- SideEffectGateway policy enforcement;
- protected credential handling;
- provider-neutral model selection;
- deterministic fake transport;
- safe normalized provider failures.

### Release / Plugin

Existing tests prove:

- FIRST_WORKING -> RELEASE_PREPARATION -> RELEASE_READY;
- Plugin-native package/marketplace/reference generation;
- publication stop at PUBLICATION_REQUIRED;
- persisted release/target/HumanAction recovery.

### Operational recovery / concurrency

Existing predecessor tests prove:

- DeploymentQualifier integration;
- backup/restore/upgrade qualification;
- owner-wait project isolation while another project progresses;
- persistence reopen/recovery of release and intervention state.

Phase 7 must prove these behaviors together through the production owner/operator path.

## 5. Integration Gap Inventory

### 5.1 No canonical full v0.4 end-to-end scenario

The repository has phase-specific tests and installed-wheel smokes, but no single qualification that begins with owner/operator Project registration and ends at Plugin-native RELEASE_READY/PUBLICATION_REQUIRED while also exercising governed model and repository paths.

This is the primary Phase 7 debt.

### 5.2 Production ServiceRuntime does not compose the MODEL execution stack

`build_service_runtime()` currently creates empty CapabilityRegistry/AgentRegistry plus LocalAgentDispatcher and SupervisorKernel.

The existing OpenAIResponsesProvider/ModelBackedAgent path is proven by direct Phase 1 composition tests, but it is not yet configured and registered in the standard ServiceRuntime used by `k-supervisor serve`.

Therefore an installed owner/operator task request cannot currently prove the delivered production MODEL adapter end to end without test-only direct control-plane construction.

Phase 7 must close this as a composition gap, not by inventing a parallel execution API.

### 5.3 Production ServiceRuntime does not wire ReleaseManager

`ServiceApiV1` already accepts a release-manager dependency for publication confirmation, but `build_service_runtime()` does not construct/pass ReleaseManager.

The API exposes release reads and publication confirmation, but there is no supported production operator operation that explicitly invokes `ReleaseManager.handle_first_working()`.

Therefore FIRST_WORKING -> RELEASE_READY currently exists as a domain contract but is not yet fully owner-operable through the standard production Service/API composition.

### 5.4 Release preparation needs the authoritative project repository context

ReleaseManager currently works with a repository adapter + ManagedRepository supplied by its caller.

Production ProjectFactory owns the configured repository adapters and repository bootstrap authority.

Phase 7 must reuse that authority to obtain/reconcile the active repository for release preparation. It must not introduce a duplicate raw GitHub/filesystem bypass.

### 5.5 Deterministic CI must not require live provider side effects

GitHub production repository composition already has a transport injection seam. OpenAIResponsesProvider also accepts an injected transport.

Phase 7 protected CI should use those production classes with deterministic transports at the composition boundary while all Project operations after startup traverse the public Service/API/CLI path.

No test-only business/control API is authorized.

### 5.6 No full installed-wheel state-continuity proof

Existing installed-wheel smokes prove individual Phase 3-6 surfaces. They do not yet prove the expanded v0.4 state as one lifecycle across:

- service restart/reopen;
- release/target/HumanAction recovery;
- backup/restore/upgrade;
- owner-wait concurrency;
- governed provider/repository idempotency.

## 6. Target Single-Node Qualification Architecture

```text
installed k-supervisor wheel
        |
        +--> PlatformConfig v1
        |
        +--> ServiceRuntime
               |
               +--> ProjectRegistry / SQLite
               +--> Policy + Approval + Human Intervention
               +--> governed MODEL composition
               +--> SupervisorKernel / WorkflowEngine
               +--> ProjectFactory
               |      +--> filesystem repository
               |      +--> governed GitHub adapter
               +--> ReleaseManager
               +--> production observability
               +--> ServiceApiV1 / WSGI host
                         |
                         +--> ServiceClientV1
                         +--> k-supervisor operator CLI
```

Qualification operations after ServiceRuntime startup must use API/CLI, not direct registry/kernel/release-manager mutation calls.

Direct Python is permitted only for test fixture/composition setup, deterministic transport injection, database backup/restore qualification, and final evidence inspection where no public operator mutation is being bypassed.

## 7. MODEL Production Composition Contract

Phase 7 may add minimal additive `PlatformConfig` fields needed to configure the already-existing OpenAI Responses MODEL provider while preserving `config_version = "1"`.

Minimum required configuration should include:

- enabled/disabled state;
- protected credential reference;
- explicit supported model profiles;
- explicit default model;
- bounded connect/request timeout;
- bounded max-output-token defaults/limits.

Requirements:

- no plaintext API key in configuration;
- configuration extra fields still fail closed;
- no provider is enabled implicitly without a protected credential reference;
- provider/model IDs remain explicit;
- existing PriorityModelSelector remains authoritative for selection;
- model invocation remains behind SideEffectGateway + PolicyEngine;
- built-in capability/agent registration uses stable identifiers and the existing CapabilityRegistry/AgentRegistry;
- LocalAgentDispatcher registers the ModelBackedAgent handler;
- provider transport injection is an internal composition seam for deterministic qualification, not a second product API;
- production default transport remains the real OpenAI Responses transport;
- `store=false`, safe failure normalization and no hidden reasoning persistence remain unchanged.

No additional model vendor is required for Phase 7.

## 8. Release Composition / Operator Contract

Phase 7 must compose ReleaseManager in ServiceRuntime and pass it to ServiceApiV1.

If an explicit operator release-preparation route is added, the preferred additive contract is:

```text
POST /api/v1/projects/{project_id}/releases
scope: releases:prepare
Idempotency-Key: REQUIRED
body:
  version
  satisfied_criteria[]   optional explicit project-specific evidence
```

Matching CLI:

```text
k-supervisor releases prepare <project_id> --body ... --config ...
```

Rules:

- the operation must delegate to ReleaseManager.handle_first_working();
- it must require the project already be FIRST_WORKING or an allowed release state;
- it must obtain/reconcile the active repository through ProjectFactory-owned adapter authority;
- it must not construct a raw repository provider independently;
- repeated same-key/same-payload calls must not duplicate release targets, package files, HumanActionRequests or external provider effects;
- same key/different payload fails with IDEMPOTENCY_CONFLICT;
- release-preparation failure is normalized and persisted safely;
- success reaches RELEASE_READY and then PUBLICATION_REQUIRED where owner publication is required;
- no external publication is performed;
- existing release read/confirm-publication routes remain compatible.

Automatic release preparation merely because a generic lifecycle transition entered FIRST_WORKING is not preferred; explicit owner/operator release preparation keeps the control boundary auditable and idempotent.

## 9. Repository Context Contract

ProjectFactory remains the repository authority.

Phase 7 may add a narrow method/result needed to recover the active release repository and its adapter, provided that:

- provider selection derives from the active approved ProjectSpec;
- bootstrap/reconcile remains idempotent;
- GitHub operations remain behind GovernedGitHubRepositoryAdapter;
- protected credential references remain unchanged;
- restart may reconstruct adapter target context safely;
- release packaging reads/writes through RepositoryAdapter only;
- no force push/protected-branch bypass is introduced.

## 10. Deterministic Full-Lifecycle Scenario

At least one authoritative protected-CI scenario must use the installed wheel and perform:

1. start ServiceRuntime/host with deterministic injected MODEL + GitHub transports;
2. register Project through API/CLI;
3. submit, approve and activate ProjectSpec through API/CLI;
4. bootstrap the configured governed GitHub repository through API/CLI;
5. transition through valid lifecycle states to a runnable state using API/CLI;
6. start a MODEL-backed Task through API/CLI;
7. prove the request reached OpenAIResponsesProvider through SideEffectGateway/Policy and succeeded via deterministic transport;
8. transition to FIRST_WORKING through the supported lifecycle boundary;
9. explicitly prepare the release through API/CLI;
10. generate/validate CHATGPT_PLUGIN package artifacts in the same governed repository lifecycle;
11. reach RELEASE_READY and PUBLICATION_REQUIRED;
12. verify a blocking owner HumanAction exists;
13. stop/reopen the service and verify state through API/CLI recovery/read surfaces;
14. prove no automatic external publication occurred.

The scenario must not directly call ProjectRegistry.transition_lifecycle(), SupervisorKernel.run_task(), ProjectFactory.bootstrap() or ReleaseManager.handle_first_working() after the service boundary is established.

## 11. GitHub Qualification Contract

Protected CI:

- uses GovernedGitHubRepositoryAdapter + GitHubRepositoryProvider;
- uses deterministic injected transport;
- proves policy/access-reference/idempotency/approval boundaries;
- proves create/resolve/bootstrap and at least one governed VCS handoff/repository operation relevant to the lifecycle;
- records safe side-effect/audit/telemetry evidence;
- does not require a real GitHub repository or token.

A live GitHub smoke may be run separately when zero-cost credentials/resources are available. It is supplemental unless a future explicit owner decision makes it a gate without violating the zero-cost policy.

## 12. MODEL Qualification Contract

Protected CI:

- uses the production OpenAIResponsesProvider and ModelBackedAgent;
- uses deterministic transport;
- uses a protected secret reference resolved only at provider boundary;
- proves ALLOW executes once;
- proves DENY executes zero transport calls;
- proves safe retryable provider failure normalization;
- proves model request uses `store=false`;
- proves result/usage/correlation is durable without secret/private-provider leakage.

A paid successful OpenAI request is not required. Existing no-cost reachability/failure evidence remains supplemental.

## 13. Release / Plugin Qualification Contract

The same lifecycle must prove:

- active approved ProjectSpec declares CHATGPT_PLUGIN;
- release readiness uses explicit + operational evidence;
- package generation creates the current Phase 5 native package;
- required references and registered app mappings remain fail-closed;
- marketplace export is validated when requested by the scenario;
- publication stops at PUBLICATION_REQUIRED;
- HumanAction remains WAITING_FOR_OWNER;
- restart preserves Release, ReleaseTarget, ReleaseValidationRecord and HumanAction;
- no Plugin installation/share/publication call occurs.

Legacy GPT_STORE compatibility remains a regression requirement, not the focal Phase 7 target.

## 14. Restart / Backup / Upgrade Qualification

Phase 7 must verify the integrated v0.4 state across:

- clean host stop and SQLite reopen;
- Service/API recovery projection;
- ProjectSpec/lifecycle state;
- Task/Workflow/AgentRun state;
- side-effect execution records;
- repository command/idempotency state;
- Release/ReleaseTarget/ReleaseValidationRecord state;
- HumanAction/PolicyApproval state;
- production telemetry records.

Backup/restore/upgrade qualification must use the existing SQLiteOperationalManager contract and prove that the integrated Phase 7 state survives a verified backup/restore cycle without duplicate external actions.

No new SQLite schema version is authorized unless an actual Phase 7 persistent-model change requires one. Any schema change would require explicit migration/rollback tests.

## 15. Concurrent Project Qualification

At least two projects must coexist.

Required scenario:

- Project A is WAITING_FOR_OWNER because of an explicit blocking owner action;
- Project B remains ACTIVE and can execute/qualify independently;
- scheduler/service limits remain bounded;
- Project A cannot accidentally consume Project B approvals, repository context, release targets, tasks or credentials;
- after restart, both projects reconstruct correctly;
- resolving Project A owner action resumes only Project A.

Existing v0.3 concurrency evidence remains a compatibility floor, but Phase 7 must include current v0.4-expanded state.

## 16. Observability / Failure Qualification

The integrated scenario must preserve Phase 6 invariants.

Required evidence:

- service/model/repository/release events share expected correlation where applicable;
- no bearer/API/GitHub token or provider-private body leaks to telemetry/logs;
- optional exporter failure does not alter task/repository/release business results;
- queue drop/failure accounting remains observable;
- deterministic model/GitHub transient failures normalize safely;
- uncertain/retried material operations reuse existing idempotency/recovery contracts;
- no recursive telemetry failure loop is introduced.

## 17. Installed-Wheel Qualification

Core Validation must add a Phase 7 installed-wheel smoke outside the repository checkout.

It must prove the package contains all production composition needed for the supported journey and does not depend on importing `tests.*` or source-checkout-only modules.

The installed-wheel smoke should exercise the same public/API/CLI composition as the main Phase 7 qualification, with deterministic external transports.

## 18. Live External Evidence Rule

Normal Phase 7 protected CI remains deterministic, credential-minimized and zero-cost.

Live MODEL/GitHub smoke evidence:

- is separately owner-controlled;
- must not expose credentials;
- must not modify production resources unintentionally;
- may use pre-authorized disposable resources;
- is supplemental when successful live access would require project-attributable payment;
- cannot block Phase 7 merely because a paid provider is unavailable.

No live Plugin publication is required.

## 19. Phase 7 Implementation Sequence

After separate owner activation:

1. **P7-A — Production composition gap closure**
   - MODEL config/composition;
   - ReleaseManager ServiceRuntime wiring;
   - repository context/reconcile boundary;
   - explicit idempotent release-preparation API/CLI if required;
   - focused compatibility/security tests.

2. **P7-B — Deterministic owner/operator E2E**
   - installed/runtime API/CLI lifecycle;
   - governed MODEL task;
   - governed GitHub repository path;
   - FIRST_WORKING -> release preparation -> RELEASE_READY/PUBLICATION_REQUIRED;
   - Plugin-native package validation.

3. **P7-C — Recovery, backup and concurrency**
   - restart/reopen;
   - backup/restore/upgrade;
   - expanded durable-state verification;
   - owner-wait vs active-project isolation;
   - deterministic failure/telemetry injection.

4. **P7-D — Installed-wheel and cumulative qualification**
   - Phase 7 installed-wheel smoke;
   - full Python 3.13 + 3.14 matrix;
   - branch-aware coverage >=80%;
   - ResourceWarning gate;
   - SBOM/vulnerability evidence;
   - protected Core Validation;
   - trusted-main attestation after merge.

5. **P7-E — ROADMAP v0.4 closure**
   - final operations/docs synchronization;
   - v0.4 completion checkpoint;
   - no automatic external publication claim.

Waves may be split further if protected validation or reviewability benefits, but they must preserve the above dependency order.

## 20. Required Phase 7 Verification

Phase 7 cannot be marked COMPLETE without:

- owner/operator Project registration/spec approval/activation through API/CLI;
- governed repository bootstrap through API/CLI;
- governed MODEL capability execution through API/CLI;
- FIRST_WORKING -> release preparation -> RELEASE_READY through supported boundaries;
- Plugin-native CHATGPT_PLUGIN package validation in the same lifecycle;
- explicit PUBLICATION_REQUIRED owner stop;
- restart/recovery of expanded v0.4 state;
- backup/restore/upgrade qualification;
- two-project owner-wait isolation;
- deterministic provider/repository/exporter failure handling;
- installed-wheel complete operator smoke;
- Python 3.13 and 3.14 PASS;
- branch-aware total coverage >=80% on both supported minors;
- ResourceWarning-as-error PASS;
- compileall PASS;
- wheel build/install PASS;
- deterministic SPDX/vulnerability evidence PASS;
- immutable Action SHA policy PASS;
- zero-cost development policy PASS;
- protected exact-head Core Validation PASS;
- synchronized completion docs.

## 21. Activation Boundary

This audit authorizes no runtime/source/test/workflow changes by itself.

Required next gate:

```text
PHASE_7_PREIMPLEMENTATION_AUDIT=COMPLETE
PHASE_7_ACTIVATION=NO
RUNTIME_IMPLEMENTATION_AUTHORIZATION=NONE
NEXT_GATE=OWNER_PHASE_7_ACTIVATION_DECISION
```

A separate owner-approved activation checkpoint must pass protected Core Validation and merge before P7-A begins.
