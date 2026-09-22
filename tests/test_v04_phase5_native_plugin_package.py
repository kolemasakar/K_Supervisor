import json
from pathlib import Path

import pytest

from release_manager import ReleaseManager, ReleaseProfileValidationError
from release_manager.plugin_native import (
    AGENT_PLUGIN_SCHEMA,
    NativePluginPackageValidator,
    normalize_plugin_slug,
    validate_plugin_name,
    validate_plugin_version,
    validate_relative_package_path,
)
from tests.phase13_support import NOW, build_release_stack


def test_native_plugin_package_is_generated_without_replacing_legacy_evidence(tmp_path):
    config = {
        "name": "Release Demo Plugin",
        "description": "Controlled release preparation for a demo project.",
        "developer_name": "K_Supervisor",
        "regression_prompts": [
            "Run the normal release workflow.",
            "Handle an unavailable integration safely.",
        ],
    }
    store, registry, human, repos, repository = build_release_stack(
        tmp_path,
        target="CHATGPT_PLUGIN",
        target_config=config,
    )
    try:
        outcome = ReleaseManager(store, registry, repos, human).handle_first_working(
            "P13",
            "0.1.0",
            repository,
            NOW,
            satisfied_criteria=("release tests pass",),
        )

        root = Path(repository.locator) / "release" / "chatgpt_plugin"
        profile = json.loads((root / "PLUGIN_PROFILE.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "package" / "plugin.json").read_text(encoding="utf-8"))
        skill = (root / "package" / "skills" / "release-demo" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        assert profile["native_plugin_manifest_path"] == (
            "release/chatgpt_plugin/package/plugin.json"
        )
        assert profile["native_skill_path"] == (
            "release/chatgpt_plugin/package/skills/release-demo/SKILL.md"
        )
        assert profile["native_plugin_name"] == "release-demo"
        assert profile["native_plugin_version"] == "0.1.0"
        assert profile["agent_plugins_schema"] == AGENT_PLUGIN_SCHEMA

        assert manifest["$schema"] == AGENT_PLUGIN_SCHEMA
        assert manifest["name"] == "release-demo"
        assert manifest["version"] == "0.1.0"
        assert manifest["description"] == config["description"]
        interface = manifest["extensions"]["com.openai"]["interface"]
        assert interface["displayName"] == "Release Demo Plugin"
        assert interface["developerName"] == "K_Supervisor"
        assert interface["defaultPrompt"] == config["regression_prompts"]
        assert "model" not in manifest
        assert "selected_model" not in manifest

        assert skill.startswith("---\nname: release-demo\ndescription: ")
        assert "## Workflow" in skill
        assert "Do not assume legacy Custom Actions migrated automatically." in skill
        assert "Do not pin or infer a selected ChatGPT model." in skill

        files = set(repos.list_files(repository))
        assert {
            "release/chatgpt_plugin/PLUGIN_PROFILE.json",
            "release/chatgpt_plugin/SKILL.md",
            "release/chatgpt_plugin/package/plugin.json",
            "release/chatgpt_plugin/package/skills/release-demo/SKILL.md",
        } <= files
        assert outcome.targets[0].artifacts
    finally:
        store.close()


def test_explicit_plugin_name_must_already_be_lowercase_kebab_case(tmp_path):
    store, registry, human, repos, repository = build_release_stack(
        tmp_path,
        target="CHATGPT_PLUGIN",
        target_config={"plugin_name": "../Unsafe Plugin"},
    )
    try:
        with pytest.raises(ReleaseProfileValidationError, match="PLUGIN_NAME_INVALID"):
            ReleaseManager(store, registry, repos, human).handle_first_working(
                "P13",
                "0.1.0",
                repository,
                NOW,
                satisfied_criteria=("release tests pass",),
            )
    finally:
        store.close()


def test_plugin_release_version_must_be_semver(tmp_path):
    store, registry, human, repos, repository = build_release_stack(
        tmp_path,
        target="CHATGPT_PLUGIN",
        target_config={"plugin_name": "release-demo"},
    )
    try:
        with pytest.raises(ReleaseProfileValidationError, match="PLUGIN_VERSION_INVALID"):
            ReleaseManager(store, registry, repos, human).handle_first_working(
                "P13",
                "release-1",
                repository,
                NOW,
                satisfied_criteria=("release tests pass",),
            )
    finally:
        store.close()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Release Demo", "release-demo"),
        ("  K Supervisor  ", "k-supervisor"),
        ("A__B///C", "a-b-c"),
    ],
)
def test_default_plugin_slug_normalization_is_deterministic(raw, expected):
    assert normalize_plugin_slug(raw) == expected


@pytest.mark.parametrize("value", ["Release-Demo", "release_demo", "../release", "", "a/b"])
def test_explicit_plugin_name_rejects_ambiguous_or_unsafe_values(value):
    with pytest.raises(ReleaseProfileValidationError, match="PLUGIN_NAME_INVALID"):
        validate_plugin_name(value)


@pytest.mark.parametrize(
    "value",
    ["0.1", "v1.0.0", "1.0.0.0", "01.2.3", "release-1"],
)
def test_plugin_version_validator_rejects_non_semver(value):
    with pytest.raises(ReleaseProfileValidationError, match="PLUGIN_VERSION_INVALID"):
        validate_plugin_version(value)


def test_package_relative_path_validator_rejects_escape():
    assert validate_relative_package_path("./.app.json") == "./.app.json"
    for value in ("../.app.json", "./../.app.json", "/.app.json", ".app.json", "./a//b"):
        with pytest.raises(ReleaseProfileValidationError, match="PLUGIN_SCHEMA_INVALID"):
            validate_relative_package_path(value)


def test_native_validator_rejects_model_pinning_and_invalid_skill_metadata():
    validator = NativePluginPackageValidator()
    manifest = {
        "$schema": AGENT_PLUGIN_SCHEMA,
        "name": "release-demo",
        "version": "0.1.0",
        "description": "Demo",
        "selected_model": "some-model",
        "extensions": {
            "com.openai": {
                "interface": {
                    "displayName": "Release Demo",
                    "shortDescription": "Demo",
                    "longDescription": "Demo workflow",
                    "defaultPrompt": ["Run the demo."],
                }
            }
        },
    }
    with pytest.raises(ReleaseProfileValidationError, match="selected model pinning"):
        validator.validate_manifest(manifest)

    with pytest.raises(ReleaseProfileValidationError, match="PLUGIN_SKILL_INVALID"):
        validator.validate_skill(
            "---\nname: other-skill\ndescription: \"Demo\"\n---\n\nDo work.\n",
            expected_name="release-demo",
        )
