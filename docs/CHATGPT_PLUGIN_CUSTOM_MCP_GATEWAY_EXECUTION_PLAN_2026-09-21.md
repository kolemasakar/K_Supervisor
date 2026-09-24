# K_Supervisor — ChatGPT Plugin / Custom MCP Gateway Execution Plan

Date: 2026-09-21  
Status: **PLANNED / OWNER-TRIGGERED / DO NOT EXECUTE WITHOUT EXPLICIT USER REQUEST**

Related:
- `docs/OPENAI_CUSTOM_GPT_TO_PLUGIN_IMPACT_2026-09-16.md`
- `docs/ROADMAP.md` — v0.4 Phase 5 Plugin-Native ChatGPT/Codex Release Packaging

## Purpose

Prepare a controlled migration path from legacy Custom GPT + Custom Actions to the newer ChatGPT Plugin model using Skills/Apps and a custom MCP server where direct connector/app replacement is not sufficient.

This document is a dormant execution plan. It does **not** activate implementation, deployment, migration, publication, privilege expansion, infrastructure mutation, or write-capable MCP tools.

Execution requires a new explicit owner instruction.

## Target Architecture

```text
ChatGPT
   |
   | Plugin / Skill / App
   v
K MCP Gateway
   |
   +-- KRC
   +-- K_AI
   +-- K-Trader
   +-- KGM
   +-- future K_* services
```

The ChatGPT Plugin layer should contain user-facing instructions, skill logic, app references and permissions.

The custom MCP layer should act as a narrow, governed protocol gateway between ChatGPT and existing K_* project APIs/services. Business logic remains in the projects and repositories, not in ChatGPT configuration.

## Design Principle

Do not rewrite existing K_* systems merely to fit ChatGPT.

Prefer a thin adapter:

```text
ChatGPT MCP tool
   -> K MCP Gateway
   -> existing service/API/function
   -> normalized structured result
```

Example:

```text
kai_market_context(symbol, market)
   -> K MCP Gateway
   -> K_AI acquire_market_context()
   -> MT4 bridge/provider
   -> structured result
```

## Proposed Deployment Model

Preferred initial model: **single K MCP Gateway** with strict project/tool boundaries.

Possible host:
- Oracle Cloud VM or another existing always-on controlled host;
- Docker container;
- HTTPS endpoint;
- reverse proxy/TLS;
- private connections/tunnels to local-only systems where required.

Do not expose local project hosts directly to the public Internet solely to satisfy MCP connectivity.

For local K_AI / MT4 access, use a secure controlled tunnel or approved private connectivity pattern rather than inbound public exposure.

## Resource Envelope

The MCP gateway itself is expected to be lightweight because it routes and validates tool calls rather than performing AI inference or heavy media processing.

Planning envelope:
- CPU: 1 vCPU minimum, 1-2 vCPU preferred;
- RAM: 256-512 MB minimum, ~1 GB comfortable;
- Disk: 1-2 GB minimum, 5-10 GB comfortable;
- network: HTTPS;
- Docker: preferred;
- GPU: not required.

These are engineering planning estimates, not OpenAI platform requirements.

Heavy work remains on the underlying service:
- KRC media workers process media;
- K-Trader performs research/market processing;
- K_AI/MT4 performs broker/context operations;
- KGM performs geopolitical processing.

## Initial Tool Classification

### READ

Safe initial candidates:
- `krc_media_capabilities`
- `krc_media_status`
- `kai_market_context`
- `kai_scanner_status`
- `kai_signal_status`
- `ktrader_research_status`
- `ktrader_dataset_query`
- `kgm_project_status`
- `kgm_intelligence_query`

Phase 1 of implementation should be **read-only** unless the owner explicitly authorizes otherwise.

### CONTROLLED_WRITE

Potential later candidates:
- `start_scan`
- `start_media_job`
- `create_research_job`

These require explicit policy and confirmation boundaries before exposure.

### HIGH_RISK

Examples:
- trade execution;
- infrastructure deployment;
- deletion;
- permission changes;
- credential changes;
- publication.

Default: **do not expose through MCP**.

Any future exception requires separate owner authorization, least privilege, explicit approval gates, audit logging and rollback/recovery design.

## Migration Strategy

### Stage 0 — Inventory

Create a canonical inventory:

```text
Custom GPT
 -> Instructions
 -> Knowledge files
 -> Connected Apps
 -> Custom Actions
 -> auth model
 -> current backend
 -> replacement path
```

Classify each dependency as:
- migrate to Skill;
- migrate to reference file;
- reuse existing Plugin/App/connector;
- rebuild behind custom MCP;
- retire.

### Stage 1 — MCP Contract

Define:
- tool names;
- JSON schemas;
- read/write class;
- authentication requirements;
- project/backend mapping;
- timeout/error semantics;
- audit fields;
- idempotency requirements;
- permission/approval policy.

No runtime deployment is required at this stage.

### Stage 2 — K MCP Gateway v1

Implement a minimal read-only gateway.

First candidate integrations:
- KRC capability/status;
- K_AI market-context/status.

Acceptance:
- tool discovery works;
- calls are schema validated;
- no privileged mutation path exists;
- secrets are not returned;
- errors are normalized;
- calls are auditable.

### Stage 3 — ChatGPT Plugin Integration

Connect the MCP gateway through the supported ChatGPT Plugin/App mechanism available to the owner's account/workspace at execution time.

Validate:
- installation/connection;
- authentication;
- permission prompts;
- tool discovery;
- read operations;
- structured results;
- regression prompts.

Do not assume current product UI or plan capabilities remain unchanged; re-check OpenAI requirements immediately before execution.

### Stage 4 — Additional K_* Integrations

Add K-Trader and KGM read-only interfaces after gateway v1 is stable.

Prefer adapters around existing service boundaries.

Do not create duplicate business logic in MCP.

### Stage 5 — Controlled Mutations

Only after separate owner approval, evaluate controlled-write tools.

Requirements:
- explicit allowlist;
- least privilege;
- confirmation gate;
- idempotency;
- durable audit;
- retry/recovery semantics;
- project-specific authorization;
- no privilege expansion by default.

### Stage 6 — Custom GPT Retirement Migration

For each legacy Custom GPT:
- freeze latest approved/published source configuration;
- map instructions to Skill;
- map knowledge/reference files;
- map supported Apps;
- replace Custom Actions through approved Apps/connectors or MCP;
- run regression tests;
- verify auth/access/sharing;
- retain rollback/reference evidence until retirement is complete.

## Security Baseline

Permanent principles:
- least privilege;
- read-only first;
- no secret contents returned to ChatGPT;
- no broad Docker/root/admin access solely for MCP;
- explicit per-tool authorization;
- project isolation;
- structured audit logging;
- high-risk actions excluded by default;
- no automatic external publication;
- no silent privilege expansion.

## K_AI / MT4 Specific Boundary

Preferred topology:

```text
ChatGPT
   -> K MCP Gateway
      -> secure private path/tunnel
         -> K_AI
            -> MT4
```

Initial permitted surface should be read-only:
- market context;
- scanner status;
- signal status.

Trade execution is excluded from the initial MCP plan.

## KRC Specific Boundary

Initial surface:
- capabilities;
- job/status lookup;
- read-only diagnostics.

Media start or other provider work belongs to a later controlled-write stage and must preserve existing confirmation/authorization rules.

## K-Trader Specific Boundary

Initial surface:
- research status;
- dataset/catalogue queries;
- read-only research outputs.

Do not grant Docker-group or generalized sudo privileges for MCP access.

Use existing constrained interfaces where possible.

## KGM Specific Boundary

Initial surface:
- project/status;
- intelligence query/read operations;
- read-only evidence/status retrieval.

No automatic publication, deployment or external mutation.

## Relationship to K_Supervisor

K_Supervisor should treat MCP as one governed integration/release surface, not as the place where domain logic lives.

Potential future K_Supervisor responsibilities:
- generate MCP integration inventory;
- produce tool manifests/contracts;
- validate tool schemas;
- classify read/write/high-risk tools;
- package Plugin/Skill assets;
- preserve regression prompts;
- validate release evidence;
- require owner confirmation before availability/publication.

This plan complements v0.4 Phase 5 but does not activate or amend that phase.

## Execution Gate

```text
PLAN_STATUS=PLANNED
IMPLEMENTATION_AUTHORIZED=NO
DEPLOYMENT_AUTHORIZED=NO
PLUGIN_MIGRATION_AUTHORIZED=NO
MCP_WRITE_TOOLS_AUTHORIZED=NO
TRADE_EXECUTION_VIA_MCP=NO
PRIVILEGE_EXPANSION=NO
OWNER_TRIGGER_REQUIRED=YES
```

Valid activation requires a future explicit owner instruction such as:

```text
Start the K MCP Gateway plan.
```

Before any implementation, re-check:
- current OpenAI Plugin/MCP product requirements;
- current account/workspace MCP capabilities;
- active K_Supervisor roadmap phase;
- existing KRC/K_AI/K-Trader/KGM service interfaces;
- available zero-cost infrastructure and security boundaries.

## First Execution Package When Activated

1. inventory existing Custom GPTs and Custom Actions;
2. map Actions -> Apps/connectors/MCP candidates;
3. define K MCP Gateway v1 read-only contract;
4. select approved host;
5. prepare threat model and auth model;
6. implement KRC + K_AI read-only adapters;
7. run local/protocol validation;
8. connect one test Plugin;
9. execute regression suite;
10. stop for owner review before any controlled-write capability.

## Non-Goals Until Separately Approved

- automatic trade execution;
- unrestricted shell/server control;
- generalized sudo or Docker access;
- automatic deployment;
- automatic public Plugin Directory publication;
- automatic credential management;
- migration of every Custom GPT in one batch;
- replacing existing K_* domain logic with MCP-specific logic.
