# K_Supervisor — OpenAI Custom GPT → Plugin impact

Date: 2026-09-16  
Status: **PLUGIN-FIRST RELEASE TARGET REQUIRED / LEGACY GPT_STORE RETAINED FOR COMPATIBILITY**

## Assessment

K_Supervisor does not expose a standalone `custom_gpt/` deployment package and its Supervisor orchestration/runtime is not coupled to GPT Builder or a selected ChatGPT model.

However, the Release Manager does contain a first-class `GPT_STORE` target and `release_manager/gpt_store.py` preparation profile. That is a real legacy platform assumption and must not remain the preferred ChatGPT release target after OpenAI's announced Custom GPT retirement.

## Compatibility Decision

The preferred ChatGPT-facing release target is now:

```text
CHATGPT_PLUGIN
```

`GPT_STORE` remains supported as a legacy compatibility target for existing Custom GPT migration/retirement work. It is not removed because existing projects and persisted release targets must remain readable and resumable.

New ChatGPT-oriented projects should use `CHATGPT_PLUGIN` unless they explicitly need the legacy migration path.

## Plugin-first Release Evidence

The `CHATGPT_PLUGIN` preparation profile generates portable release evidence rather than pretending to own OpenAI's evolving product packaging format:

- reusable workflow/instructions as a skill source asset;
- reference-file inventory;
- required/optional app inventory and app-template inventory;
- explicit Custom Action dependency inventory;
- custom MCP integration inventory;
- regression prompts for normal and difficult cases;
- access, authorization, sharing and migration checklist;
- machine-readable plugin profile.

Custom Action dependencies are never marked as automatically migrated. They require explicit rebuild/verification through a supported app/connector or custom MCP server.

The profile does not pin a ChatGPT model. Access and sharing must be reviewed independently because GPT sharing/Store visibility does not automatically transfer to a replacement plugin.

## Publication Semantics

For `CHATGPT_PLUGIN`, K_Supervisor's existing `PUBLICATION_REQUIRED -> PUBLISHED` boundary is retained for compatibility, but `PUBLISHED` means the owner has confirmed the intended plugin availability state for that project (for example private, shared, workspace-available, installed, or publicly listed where supported). It does not imply public Plugin Directory listing.

## Boundary

```text
CUSTOM_GPT_DEPENDENCY=LEGACY_RELEASE_TARGET_ONLY
PREFERRED_CHATGPT_TARGET=CHATGPT_PLUGIN
LEGACY_GPT_STORE_REMOVAL=NO
SUPERVISOR_ORCHESTRATION_CHANGE=NONE
SELECTED_MODEL_COUPLING=NONE
CUSTOM_ACTION_AUTO_MIGRATION=FORBIDDEN
PHASE_8_ACTIVATION=NO
```

This compatibility correction does not authorize automatic external publication, bypass owner/workspace permissions, or change the policy/approval boundary.

Source context: `kolemasakar/AI_general/docs/openai-custom-gpts-retirement-to-plugins-2026-09-16.md` and current OpenAI Help Center guidance for Custom GPT retirement, Plugins, Skills and Apps.
