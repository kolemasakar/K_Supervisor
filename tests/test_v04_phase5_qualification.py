from __future__ import annotations

import json
from pathlib import Path

from factory.contracts import BootstrapFile
from models.enums import HumanActionStatus, ReleaseStatus
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry
from release_manager import ReleaseManager
from release_manager.gpt_store import GPTStorePreparationProfile
from release_manager.profiles import profile_for
from tests.phase13_support import NOW, build_release_stack


def _regression_cases():
    positives = [
        {
            "id": f"positive-{index:03d}",
            "type": "positive",
            "prompt": f"Run supported workflow {index}.",
            "expected_behavior": "Use the packaged skill within declared permissions.",
            "expected_result_shape": "project-defined response",
            "dependencies": ["repo-tools"],
        }
        for index in range(1, 6)
    ]
    negatives = [
        {
            "id": f"negative-{index:03d}",
            "type": "negative",
            "prompt": f"Attempt unsupported or unsafe workflow {index}.",
            "expected_behavior": "Stop and surface the required owner/workspace action.",
            "expected_result_shape": "explicit safe blocker",
            "dependencies": [],
        }
        for index in range(1, 4)
    ]
    return positives + negatives


def test_phase5_full_native_package_qualification_and_owner_handoff(tmp_path):
    config = {
        "plugin_name": "release-demo",
        "name": "Release Demo Plugin",
        "description": "Qualified native plugin packaging.",
        "developer_name": "K_Supervisor",
        "registered_apps": [
            {
                "alias": "repo-tools",
                "app_id": "asdk_app_repo_tools",
                "required": True,
            },
            {
                "alias": "optional-search",
                "app_id": "connector_search",
                "required": False,
            },
        ],
        "package_references": [
            {
                "source": "docs/REFERENCE.md",
                "destination": "reference.md",
                "required": True,
            }
        ],
        "custom_action_dependencies": ["legacy-openapi-action"],
        "mcp_integrations": ["legacy-custom-mcp"],
        "public_submission_ready": True,
        "regression_cases": _regression_cases(),
        "github_marketplace": {
            "enabled": True,
            "name": "release-demo-marketplace",
            "display_name": "Release Demo Marketplace",
            "plugin_id": "plugin_existing_release_demo",
        },
    }
    store, registry, human, repos, repository = build_release_stack(
        tmp_path,
        target="CHATGPT_PLUGIN",
        target_config=config,
    )
    try:
        repos.apply_files(
            repository,
            (BootstrapFile("docs/REFERENCE.md", "# Canonical reference\n"),),
        )
        manager = ReleaseManager(store, registry, repos, human)
        outcome = manager.handle_first_working(
            "P13",
            "0.1.0",
            repository,
            NOW,
            satisfied_criteria=("release tests pass",),
        )

        assert outcome.release.status == ReleaseStatus.PUBLICATION_REQUIRED
        target = outcome.targets[0]
        assert target.target_type == "CHATGPT_PLUGIN"
        assert target.status == ReleaseStatus.PUBLICATION_REQUIRED
        assert target.published_at is None
        assert target.human_action_id is not None
        action = store.get_human_action(target.human_action_id)
        assert action is not None
        assert action.status == HumanActionStatus.WAITING_FOR_OWNER

        root = Path(repository.locator) / "release" / "chatgpt_plugin"
        package = root / "package"
        marketplace = root / "marketplace"
        mirror = marketplace / "plugins" / "release-demo"

        expected_paths = {
            "release/chatgpt_plugin/package/plugin.json",
            "release/chatgpt_plugin/package/.app.json",
            "release/chatgpt_plugin/package/skills/release-demo/SKILL.md",
            "release/chatgpt_plugin/package/skills/release-demo/references/reference.md",
            "release/chatgpt_plugin/MIGRATION_INVENTORY.json",
            "release/chatgpt_plugin/REGRESSION_CASES.json",
            "release/chatgpt_plugin/marketplace/.agents/plugins/marketplace.json",
            "release/chatgpt_plugin/marketplace/plugins/release-demo/plugin.json",
            "release/chatgpt_plugin/marketplace/plugins/release-demo/.app.json",
            "release/chatgpt_plugin/marketplace/plugins/release-demo/skills/release-demo/SKILL.md",
            "release/chatgpt_plugin/marketplace/plugins/release-demo/skills/release-demo/references/reference.md",
        }
        files = set(repos.list_files(repository))
        assert expected_paths <= files
        assert expected_paths <= set(target.artifacts)

        manifest = json.loads((package / "plugin.json").read_text(encoding="utf-8"))
        apps = json.loads((package / ".app.json").read_text(encoding="utf-8"))
        inventory = json.loads((root / "MIGRATION_INVENTORY.json").read_text(encoding="utf-8"))
        regression = json.loads((root / "REGRESSION_CASES.json").read_text(encoding="utf-8"))
        catalog = json.loads(
            (marketplace / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

        assert manifest["extensions"]["com.openai"]["apps"] == "./.app.json"
        assert "pluginId" not in manifest
        assert "model" not in manifest
        assert "selected_model" not in manifest
        assert apps["apps"]["repo-tools"]["required"] is True
        assert apps["apps"]["optional-search"]["required"] is False

        assert inventory["custom_actions"] == [
            {"dependency": "legacy-openapi-action", "status": "REBUILD_REQUIRED"}
        ]
        assert inventory["mcp_integrations"] == [
            {"integration": "legacy-custom-mcp", "status": "EXPLICIT_MAPPING_REQUIRED"}
        ]
        assert inventory["selected_model"] == {"pinned": False, "transferred": False}
        assert inventory["sharing_access"]["transferred"] is False
        assert inventory["conversation_history"]["transferred"] is False
        assert inventory["packaged_references"][0]["status"] == "PACKAGED"

        assert regression["public_submission_ready"] is True
        assert sum(case["type"] == "positive" for case in regression["cases"]) == 5
        assert sum(case["type"] == "negative" for case in regression["cases"]) == 3

        entry = catalog["plugins"][0]
        assert entry["pluginId"] == "plugin_existing_release_demo"
        assert entry["source"] == {"source": "local", "path": "./plugins/release-demo"}

        assert (mirror / "plugin.json").read_text(encoding="utf-8") == (
            package / "plugin.json"
        ).read_text(encoding="utf-8")
        assert (mirror / ".app.json").read_text(encoding="utf-8") == (
            package / ".app.json"
        ).read_text(encoding="utf-8")
        assert (
            mirror / "skills" / "release-demo" / "SKILL.md"
        ).read_text(encoding="utf-8") == (
            package / "skills" / "release-demo" / "SKILL.md"
        ).read_text(encoding="utf-8")
        assert (
            mirror / "skills" / "release-demo" / "references" / "reference.md"
        ).read_text(encoding="utf-8") == "# Canonical reference\n"

        assert not any(path.endswith("/mcp.json") or path.endswith("/.mcp.json") for path in files)
        assert not any("/.codex-plugin/" in path for path in files)
    finally:
        store.close()

    with SQLitePersistenceStore(tmp_path / "state.db") as reopened:
        recovered = ProjectRegistry(reopened).recover("P13")
        assert recovered.releases[0].status == ReleaseStatus.PUBLICATION_REQUIRED
        assert recovered.release_targets[0].target_type == "CHATGPT_PLUGIN"
        assert recovered.release_targets[0].status == ReleaseStatus.PUBLICATION_REQUIRED
        assert recovered.release_targets[0].published_at is None
        assert recovered.human_actions[0].status == HumanActionStatus.WAITING_FOR_OWNER


def test_phase5_does_not_replace_legacy_gpt_store_profile():
    assert isinstance(profile_for("GPT_STORE"), GPTStorePreparationProfile)
