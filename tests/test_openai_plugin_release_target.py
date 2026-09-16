import json
from pathlib import Path

from models.enums import ReleaseStatus
from release_manager import ReleaseManager
from release_manager.chatgpt_plugin import ChatGPTPluginPreparationProfile
from release_manager.gpt_store import GPTStorePreparationProfile
from release_manager.profiles import profile_for

from tests.phase13_support import NOW, build_release_stack


def test_chatgpt_plugin_release_generates_plugin_first_evidence_and_owner_handoff(tmp_path):
    config = {
        "name": "Release Demo Plugin",
        "reference_files": ["docs/REFERENCE.md"],
        "required_apps": ["github"],
        "optional_apps": ["slack"],
        "app_templates": ["workspace-default"],
        "custom_action_dependencies": ["legacy-openapi-action"],
        "mcp_integrations": ["custom-release-mcp"],
        "regression_prompts": ["Run the normal release workflow.", "Handle a permission-denied edge case."],
    }
    store, registry, human, repos, repository = build_release_stack(
        tmp_path,
        target="CHATGPT_PLUGIN",
        target_config=config,
    )
    try:
        manager = ReleaseManager(store, registry, repos, human)
        outcome = manager.handle_first_working(
            "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
        )
        assert outcome.release.status == ReleaseStatus.PUBLICATION_REQUIRED
        assert outcome.targets[0].target_type == "CHATGPT_PLUGIN"
        assert outcome.targets[0].status == ReleaseStatus.PUBLICATION_REQUIRED

        files = set(repos.list_files(repository))
        expected = {
            "release/chatgpt_plugin/PLUGIN_PROFILE.json",
            "release/chatgpt_plugin/SKILL.md",
            "release/chatgpt_plugin/INTEGRATIONS.md",
            "release/chatgpt_plugin/REGRESSION_PROMPTS.md",
            "release/chatgpt_plugin/ACCESS_AND_MIGRATION_CHECKLIST.md",
        }
        assert expected <= files

        profile = json.loads(
            (Path(repository.locator) / "release/chatgpt_plugin/PLUGIN_PROFILE.json").read_text(encoding="utf-8")
        )
        assert profile["target"] == "CHATGPT_PLUGIN"
        assert profile["custom_action_dependencies"] == ["legacy-openapi-action"]
        assert profile["custom_actions_auto_migrated"] is False
        assert profile["selected_model_pinned"] is False
        assert profile["access_review_required"] is True

        integrations = (Path(repository.locator) / "release/chatgpt_plugin/INTEGRATIONS.md").read_text(encoding="utf-8")
        assert "legacy-openapi-action" in integrations
        assert "not considered migrated" in integrations
        assert "custom-release-mcp" in integrations

        checklist = (Path(repository.locator) / "release/chatgpt_plugin/ACCESS_AND_MIGRATION_CHECKLIST.md").read_text(encoding="utf-8")
        assert "do not assume GPT sharing or Store visibility transfers" in checklist
        assert "supported app/connector or custom MCP server" in checklist
    finally:
        store.close()


def test_chatgpt_plugin_is_preferred_additive_target_while_gpt_store_stays_compatible():
    assert isinstance(profile_for("CHATGPT_PLUGIN"), ChatGPTPluginPreparationProfile)
    assert isinstance(profile_for("GPT_STORE"), GPTStorePreparationProfile)
