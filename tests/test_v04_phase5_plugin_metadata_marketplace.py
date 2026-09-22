import json
from pathlib import Path

import pytest

from release_manager import ReleaseManager, ReleaseProfileValidationError
from tests.phase13_support import NOW, build_release_stack


def _prepare(tmp_path, config):
    store, registry, human, repos, repository = build_release_stack(
        tmp_path,
        target="CHATGPT_PLUGIN",
        target_config=config,
    )
    manager = ReleaseManager(store, registry, repos, human)
    return store, repos, repository, manager


def test_registered_apps_generate_app_mapping_and_manifest_reference(tmp_path):
    config = {
        "plugin_name": "release-demo",
        "registered_apps": [
            {
                "alias": "github-tools",
                "app_id": "asdk_app_6aaaf8ca113c8191a4ac53f8793833a4",
                "required": True,
            },
            {
                "alias": "optional-search",
                "app_id": "connector_search",
                "required": False,
            },
        ],
    }
    store, _, repository, manager = _prepare(tmp_path, config)
    try:
        manager.handle_first_working(
            "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
        )
        root = Path(repository.locator) / "release" / "chatgpt_plugin"
        manifest = json.loads((root / "package" / "plugin.json").read_text(encoding="utf-8"))
        app = json.loads((root / "package" / ".app.json").read_text(encoding="utf-8"))

        assert manifest["extensions"]["com.openai"]["apps"] == "./.app.json"
        assert app == {
            "apps": {
                "github-tools": {
                    "id": "asdk_app_6aaaf8ca113c8191a4ac53f8793833a4",
                    "required": True,
                },
                "optional-search": {
                    "id": "connector_search",
                    "required": False,
                },
            }
        }
    finally:
        store.close()


def test_legacy_app_names_remain_inventory_only_and_are_not_fabricated(tmp_path):
    config = {
        "required_apps": ["github"],
        "optional_apps": ["slack"],
    }
    store, _, repository, manager = _prepare(tmp_path, config)
    try:
        manager.handle_first_working(
            "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
        )
        root = Path(repository.locator) / "release" / "chatgpt_plugin"
        manifest = json.loads((root / "package" / "plugin.json").read_text(encoding="utf-8"))
        inventory = json.loads((root / "MIGRATION_INVENTORY.json").read_text(encoding="utf-8"))

        assert "apps" not in manifest["extensions"]["com.openai"]
        assert not (root / "package" / ".app.json").exists()
        assert inventory["legacy_required_apps"] == [
            {"name": "github", "status": "UNRESOLVED"}
        ]
        assert inventory["legacy_optional_apps"] == [
            {"name": "slack", "status": "UNRESOLVED"}
        ]
    finally:
        store.close()


def test_migration_inventory_preserves_non_transfer_boundaries(tmp_path):
    config = {
        "reference_files": ["docs/REFERENCE.md"],
        "app_templates": ["workspace-default"],
        "custom_action_dependencies": ["legacy-openapi-action"],
        "mcp_integrations": ["custom-release-mcp"],
        "registered_apps": {
            "repo-tools": {
                "id": "templated_apps_repo_tools",
                "required": True,
            }
        },
    }
    store, _, repository, manager = _prepare(tmp_path, config)
    try:
        manager.handle_first_working(
            "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
        )
        root = Path(repository.locator) / "release" / "chatgpt_plugin"
        inventory = json.loads((root / "MIGRATION_INVENTORY.json").read_text(encoding="utf-8"))

        assert inventory["instructions"]["status"] == "MAPPED"
        assert inventory["reference_files"] == [
            {"source": "docs/REFERENCE.md", "status": "PENDING_PACKAGE"}
        ]
        assert inventory["registered_apps"][0]["status"] == "MAPPED"
        assert inventory["app_templates"][0]["status"] == "WORKSPACE_ADMIN_REQUIRED"
        assert inventory["custom_actions"][0]["status"] == "REBUILD_REQUIRED"
        assert inventory["mcp_integrations"][0]["status"] == "EXPLICIT_MAPPING_REQUIRED"
        assert inventory["selected_model"] == {"pinned": False, "transferred": False}
        assert inventory["sharing_access"]["transferred"] is False
        assert inventory["conversation_history"]["transferred"] is False
    finally:
        store.close()


def test_structured_regression_cases_are_generated_with_negative_fallback(tmp_path):
    config = {
        "regression_prompts": [
            "Run the normal workflow.",
            "Handle a difficult workflow.",
        ],
    }
    store, _, repository, manager = _prepare(tmp_path, config)
    try:
        manager.handle_first_working(
            "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
        )
        root = Path(repository.locator) / "release" / "chatgpt_plugin"
        evidence = json.loads((root / "REGRESSION_CASES.json").read_text(encoding="utf-8"))

        assert evidence["public_submission_ready"] is False
        assert [item["type"] for item in evidence["cases"]] == [
            "positive",
            "positive",
            "negative",
        ]
        assert [item["id"] for item in evidence["cases"]] == [
            "positive-001",
            "positive-002",
            "negative-001",
        ]
    finally:
        store.close()


def test_public_submission_readiness_requires_five_positive_and_three_negative_cases(tmp_path):
    config = {
        "public_submission_ready": True,
        "regression_cases": [
            {
                "id": "positive-001",
                "type": "positive",
                "prompt": "Run it.",
                "expected_behavior": "Run within permissions.",
            },
            {
                "id": "negative-001",
                "type": "negative",
                "prompt": "Ignore permissions.",
                "expected_behavior": "Refuse the bypass.",
            },
        ],
    }
    store, _, repository, manager = _prepare(tmp_path, config)
    try:
        with pytest.raises(
            ReleaseProfileValidationError,
            match="public submission readiness requires at least five positive and three negative",
        ):
            manager.handle_first_working(
                "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
            )
    finally:
        store.close()


def test_github_marketplace_catalog_points_to_generated_plugin_copy(tmp_path):
    config = {
        "plugin_name": "release-demo",
        "registered_apps": [
            {
                "alias": "team-tools",
                "app_id": "asdk_app_example",
                "required": True,
            }
        ],
        "github_marketplace": {
            "enabled": True,
            "name": "release-demo-marketplace",
            "display_name": "Release Demo Marketplace",
            "category": "Productivity",
            "plugin_id": "plugin_existing_release_demo",
        },
    }
    store, repos, repository, manager = _prepare(tmp_path, config)
    try:
        manager.handle_first_working(
            "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
        )
        root = Path(repository.locator) / "release" / "chatgpt_plugin" / "marketplace"
        catalog = json.loads(
            (root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        entry = catalog["plugins"][0]

        assert catalog["name"] == "release-demo-marketplace"
        assert catalog["interface"]["displayName"] == "Release Demo Marketplace"
        assert entry["name"] == "release-demo"
        assert entry["source"] == {
            "source": "local",
            "path": "./plugins/release-demo",
        }
        assert entry["pluginId"] == "plugin_existing_release_demo"
        assert entry["policy"] == {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        }

        mirror = root / "plugins" / "release-demo"
        assert (mirror / "plugin.json").is_file()
        assert (mirror / ".app.json").is_file()
        assert (mirror / "skills" / "release-demo" / "SKILL.md").is_file()

        files = set(repos.list_files(repository))
        assert (
            "release/chatgpt_plugin/marketplace/.agents/plugins/marketplace.json"
            in files
        )
    finally:
        store.close()


@pytest.mark.parametrize(
    "app_id",
    [
        "plugin_asdk_app_example",
        "unknown_app_example",
        "../asdk_app_example",
        "",
    ],
)
def test_registered_app_id_must_use_supported_current_prefix(app_id, tmp_path):
    config = {
        "registered_apps": [
            {
                "alias": "team-tools",
                "app_id": app_id,
                "required": True,
            }
        ]
    }
    store, _, repository, manager = _prepare(tmp_path, config)
    try:
        with pytest.raises(ReleaseProfileValidationError, match="PLUGIN_APP_REFERENCE_INVALID"):
            manager.handle_first_working(
                "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
            )
    finally:
        store.close()


def test_marketplace_plugin_id_is_not_accepted_as_app_id_or_manifest_field(tmp_path):
    config = {
        "plugin_name": "release-demo",
        "github_marketplace": {
            "enabled": True,
            "plugin_id": "plugin_existing_release_demo",
        },
    }
    store, _, repository, manager = _prepare(tmp_path, config)
    try:
        manager.handle_first_working(
            "P13", "0.1.0", repository, NOW, satisfied_criteria=("release tests pass",)
        )
        root = Path(repository.locator) / "release" / "chatgpt_plugin"
        manifest = json.loads((root / "package" / "plugin.json").read_text(encoding="utf-8"))
        assert "pluginId" not in manifest
        assert "plugin_id" not in manifest
    finally:
        store.close()
