from __future__ import annotations

import json

from factory.contracts import BootstrapFile

from .plugin_native import (
    MIGRATION_INVENTORY_PATH,
    PLUGIN_MANIFEST_PATH,
    REGRESSION_CASES_PATH,
    build_native_plugin_package,
    package_reference_requests,
)


_REQUIRED_PLUGIN_FILES = (
    "release/chatgpt_plugin/PLUGIN_PROFILE.json",
    "release/chatgpt_plugin/SKILL.md",
    "release/chatgpt_plugin/INTEGRATIONS.md",
    "release/chatgpt_plugin/REGRESSION_PROMPTS.md",
    "release/chatgpt_plugin/ACCESS_AND_MIGRATION_CHECKLIST.md",
    PLUGIN_MANIFEST_PATH,
    MIGRATION_INVENTORY_PATH,
    REGRESSION_CASES_PATH,
)


def _items(value):
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def _markdown_items(values) -> str:
    values = tuple(values)
    if not values:
        return "- None declared."
    return "\n".join(
        f"- {json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else item}"
        for item in values
    )


class ChatGPTPluginPreparationProfile:
    """Portable Plugin-first release evidence for ChatGPT/Codex workflows."""

    target_type = "CHATGPT_PLUGIN"

    def reference_requests(self, spec) -> tuple[str, ...]:
        config = spec.release.get("chatgpt_plugin", {})
        return package_reference_requests(config)

    def generate(
        self,
        spec,
        release,
        target,
        *,
        reference_contents=None,
    ) -> tuple[BootstrapFile, ...]:
        config = spec.release.get("chatgpt_plugin", {})
        reference_files = _items(config.get("reference_files", config.get("knowledge_files", ())))
        required_apps = _items(config.get("required_apps", ()))
        optional_apps = _items(config.get("optional_apps", ()))
        app_templates = _items(config.get("app_templates", ()))
        custom_actions = _items(config.get("custom_action_dependencies", config.get("actions", ())))
        mcp_integrations = _items(config.get("mcp_integrations", ()))
        regression_prompts = _items(config.get("regression_prompts")) or (
            f"Help me use {spec.name}.",
            f"Run a representative end-to-end workflow for {spec.name}.",
            "Handle a difficult edge case while preserving permissions and output requirements.",
        )
        native = build_native_plugin_package(
            spec,
            release,
            config,
            reference_contents=reference_contents,
        )
        profile = {
            "schema_version": "1.0",
            "target": self.target_type,
            "release_id": release.release_id,
            "name": config.get("name") or spec.name,
            "description": config.get("description") or spec.purpose,
            "skill_source_path": _REQUIRED_PLUGIN_FILES[1],
            "reference_files": list(reference_files),
            "required_apps": list(required_apps),
            "optional_apps": list(optional_apps),
            "app_templates": list(app_templates),
            "custom_action_dependencies": list(custom_actions),
            "mcp_integrations": list(mcp_integrations),
            "regression_prompts_path": _REQUIRED_PLUGIN_FILES[3],
            "custom_actions_auto_migrated": False,
            "selected_model_pinned": False,
            "access_review_required": True,
            "native_plugin_manifest_path": native.manifest_path,
            "native_skill_path": native.skill_path,
            "native_plugin_name": native.plugin_name,
            "native_plugin_version": native.plugin_version,
            "agent_plugins_schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "native_app_mapping_path": native.app_path,
            "migration_inventory_path": native.migration_inventory_path,
            "structured_regression_cases_path": native.regression_cases_path,
            "marketplace_catalog_path": next(
                (path for path, _ in native.marketplace_files if path.endswith("/.agents/plugins/marketplace.json")),
                None,
            ),
        }
        skill = (
            f"# {profile['name']} Skill Source\n\n"
            f"Description: {profile['description']}\n\n"
            f"Purpose: {spec.purpose}\n\n"
            f"Problem: {spec.problem_statement}\n\n"
            "## Success criteria\n\n"
            + "\n".join(f"- {item}" for item in spec.success_criteria)
            + "\n\n"
            "This is a portable skill source asset. Validate the current OpenAI plugin/skill "
            "packaging and workspace requirements before installation or publication.\n"
        )
        integrations = (
            "# ChatGPT Plugin Integration Inventory\n\n"
            "## Required apps\n"
            + _markdown_items(required_apps)
            + "\n\n## Optional apps\n"
            + _markdown_items(optional_apps)
            + "\n\n## App templates\n"
            + _markdown_items(app_templates)
            + "\n\n## Legacy Custom Action dependencies requiring rebuild\n"
            + _markdown_items(custom_actions)
            + "\n\n## Custom MCP integrations\n"
            + _markdown_items(mcp_integrations)
            + "\n\nCustom Action dependencies are inventory only and are not considered migrated. "
            "Rebuild required integrations using a supported connector/app or custom MCP server.\n"
        )
        prompts = (
            "# Plugin Regression Prompts\n\n"
            + "\n".join(f"- {item}" for item in regression_prompts)
            + "\n"
        )
        checklist = """# ChatGPT Plugin Access and Migration Checklist

Automatically prepared:
- [x] Portable skill source generated.
- [x] Machine-readable plugin profile generated.
- [x] Integration dependency inventory generated.
- [x] Regression prompts generated.
- [x] Custom Actions explicitly marked as non-automatic migration dependencies.

Owner/platform actions:
- [ ] Review the skill instructions, description, examples, and reference assets.
- [ ] Rebuild every required legacy Custom Action through a supported app/connector or custom MCP server.
- [ ] Connect and authorize required apps with least-privilege access.
- [ ] Test familiar prompts and at least one difficult edge case.
- [ ] Verify output format, permissions, approvals, and integration behavior.
- [ ] Review plugin installation/sharing state; do not assume GPT sharing or Store visibility transfers.
- [ ] Follow the current account/workspace migration notice and publication controls.
- [ ] Confirm intended plugin availability back to K_Supervisor.
"""
        generated = [
            BootstrapFile(_REQUIRED_PLUGIN_FILES[0], json.dumps(profile, indent=2, sort_keys=True) + "\n"),
            BootstrapFile(_REQUIRED_PLUGIN_FILES[1], skill),
            BootstrapFile(_REQUIRED_PLUGIN_FILES[2], integrations),
            BootstrapFile(_REQUIRED_PLUGIN_FILES[3], prompts),
            BootstrapFile(_REQUIRED_PLUGIN_FILES[4], checklist),
            BootstrapFile(native.manifest_path, native.manifest_content),
            BootstrapFile(native.skill_path, native.skill_content),
            BootstrapFile(native.migration_inventory_path, native.migration_inventory_content),
            BootstrapFile(native.regression_cases_path, native.regression_cases_content),
        ]
        if native.app_path is not None and native.app_content is not None:
            generated.append(BootstrapFile(native.app_path, native.app_content))
        generated.extend(BootstrapFile(path, content) for path, content in native.reference_files)
        generated.extend(BootstrapFile(path, content) for path, content in native.marketplace_files)
        return tuple(generated)

    def validate(self, files: tuple[str, ...]) -> tuple[str, ...]:
        available = set(files)
        missing = [path for path in _REQUIRED_PLUGIN_FILES if path not in available]
        native_skills = tuple(
            path
            for path in available
            if path.startswith("release/chatgpt_plugin/package/skills/")
            and path.endswith("/SKILL.md")
        )
        if not native_skills:
            missing.append("release/chatgpt_plugin/package/skills/<skill>/SKILL.md")
        return tuple(missing)

    @property
    def checklist(self) -> tuple[str, ...]:
        return (
            "review_plugin_skill_and_reference_assets",
            "rebuild_legacy_custom_actions",
            "connect_and_authorize_required_apps",
            "run_plugin_regression_prompts",
            "review_plugin_access_and_sharing",
            "confirm_plugin_availability_to_k_supervisor",
        )
