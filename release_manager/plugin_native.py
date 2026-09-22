from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Mapping, Any

from .errors import ReleaseProfileValidationError


AGENT_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PLUGIN_PACKAGE_ROOT = "release/chatgpt_plugin/package"
PLUGIN_MANIFEST_PATH = f"{PLUGIN_PACKAGE_ROOT}/plugin.json"
PLUGIN_APP_PATH = f"{PLUGIN_PACKAGE_ROOT}/.app.json"
MIGRATION_INVENTORY_PATH = "release/chatgpt_plugin/MIGRATION_INVENTORY.json"
REGRESSION_CASES_PATH = "release/chatgpt_plugin/REGRESSION_CASES.json"
MARKETPLACE_ROOT = "release/chatgpt_plugin/marketplace"
MARKETPLACE_CATALOG_PATH = f"{MARKETPLACE_ROOT}/.agents/plugins/marketplace.json"

_PLUGIN_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_APP_ID_RE = re.compile(r"^(?:asdk_app_|connector_|templated_apps_)[A-Za-z0-9._:-]+$")
_MARKETPLACE_PLUGIN_ID_RE = re.compile(r"^plugin_[A-Za-z0-9._:-]+$")
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@dataclass(frozen=True)
class NativePluginPackage:
    plugin_name: str
    plugin_version: str
    manifest_path: str
    skill_path: str
    manifest_content: str
    skill_content: str
    app_path: str | None = None
    app_content: str | None = None
    migration_inventory_path: str = MIGRATION_INVENTORY_PATH
    migration_inventory_content: str = ""
    regression_cases_path: str = REGRESSION_CASES_PATH
    regression_cases_content: str = ""
    marketplace_files: tuple[tuple[str, str], ...] = ()


def normalize_plugin_slug(value: str) -> str:
    source = str(value).strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", source).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug or not _PLUGIN_NAME_RE.fullmatch(slug):
        raise ReleaseProfileValidationError("PLUGIN_NAME_INVALID: plugin name cannot be normalized safely")
    return slug


def validate_plugin_name(value: str) -> str:
    name = str(value).strip()
    if not name or not _PLUGIN_NAME_RE.fullmatch(name):
        raise ReleaseProfileValidationError(
            "PLUGIN_NAME_INVALID: plugin name must use lowercase kebab-case"
        )
    return name


def validate_plugin_version(value: str) -> str:
    version = str(value).strip()
    if not version or not _SEMVER_RE.fullmatch(version):
        raise ReleaseProfileValidationError(
            "PLUGIN_VERSION_INVALID: plugin version must use semantic versioning"
        )
    return version


def validate_relative_package_path(value: str) -> str:
    path = str(value).strip()
    if not path.startswith("./"):
        raise ReleaseProfileValidationError(
            "PLUGIN_SCHEMA_INVALID: package-relative paths must start with ./"
        )
    remainder = path[2:]
    if not remainder or remainder.startswith("/") or "\\" in remainder:
        raise ReleaseProfileValidationError(
            "PLUGIN_SCHEMA_INVALID: package-relative path is invalid"
        )
    parts = remainder.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ReleaseProfileValidationError(
            "PLUGIN_SCHEMA_INVALID: package-relative path escapes plugin root"
        )
    return path


def _single_line(value: str, *, field: str) -> str:
    normalized = " ".join(str(value).split())
    if not normalized:
        raise ReleaseProfileValidationError(f"PLUGIN_CONFIG_INVALID: {field} must not be empty")
    return normalized


def _json_yaml_scalar(value: str) -> str:
    return json.dumps(_single_line(value, field="skill metadata"), ensure_ascii=False)


def build_native_plugin_package(spec, release, config: Mapping[str, Any]) -> NativePluginPackage:
    explicit_name = config.get("plugin_name")
    plugin_name = (
        validate_plugin_name(str(explicit_name))
        if explicit_name is not None
        else normalize_plugin_slug(spec.short_name)
    )
    plugin_version = validate_plugin_version(release.version)
    description = _single_line(
        config.get("description") or spec.purpose,
        field="plugin description",
    )
    display_name = _single_line(
        config.get("name") or spec.name,
        field="plugin display name",
    )
    skill_name = validate_plugin_name(
        str(config.get("skill_name"))
        if config.get("skill_name") is not None
        else plugin_name
    )
    skill_description = _single_line(
        config.get("skill_description") or description,
        field="skill description",
    )

    regression_prompts = config.get("regression_prompts") or (
        f"Help me use {spec.name}.",
        f"Run a representative end-to-end workflow for {spec.name}.",
        "Handle a difficult edge case while preserving permissions and output requirements.",
    )
    if isinstance(regression_prompts, str):
        regression_prompts = (regression_prompts,)
    prompts = tuple(
        _single_line(item, field="regression prompt")
        for item in regression_prompts
        if str(item).strip()
    )
    if not prompts:
        raise ReleaseProfileValidationError(
            "PLUGIN_CONFIG_INVALID: at least one regression prompt is required"
        )

    interface: dict[str, Any] = {
        "displayName": display_name,
        "shortDescription": _single_line(
            config.get("short_description") or description,
            field="short description",
        ),
        "longDescription": _single_line(
            config.get("long_description") or description,
            field="long description",
        ),
        "defaultPrompt": list(prompts[:3]),
    }
    developer_name = config.get("developer_name")
    if developer_name is not None:
        interface["developerName"] = _single_line(
            developer_name,
            field="developer name",
        )

    manifest = {
        "$schema": AGENT_PLUGIN_SCHEMA,
        "name": plugin_name,
        "version": plugin_version,
        "description": description,
        "extensions": {
            "com.openai": {
                "interface": interface,
            }
        },
    }

    skill_path = f"{PLUGIN_PACKAGE_ROOT}/skills/{skill_name}/SKILL.md"
    skill_body = (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {_json_yaml_scalar(skill_description)}\n"
        "---\n\n"
        f"Use this skill when the user needs to work with {display_name}.\n\n"
        "## Purpose\n\n"
        f"{spec.purpose}\n\n"
        "## Problem\n\n"
        f"{spec.problem_statement}\n\n"
        "## Workflow\n\n"
        "1. Confirm the requested task is within this plugin's declared purpose and available integrations.\n"
        "2. Use only configured skills, apps, resources, and approved external actions.\n"
        "3. Preserve permission, approval, privacy, and owner-publication boundaries.\n"
        "4. If a required dependency is unavailable or ambiguous, stop and request the missing owner/workspace action instead of inventing access.\n"
        "5. Return the requested result in the project's expected format.\n\n"
        "## Success criteria\n\n"
        + "\n".join(f"- {item}" for item in spec.success_criteria)
        + "\n\n"
        "## Boundaries\n\n"
        "- Do not assume legacy Custom Actions migrated automatically.\n"
        "- Do not assume prior GPT sharing or access settings transferred.\n"
        "- Do not pin or infer a selected ChatGPT model.\n"
        "- Do not perform external publication unless the owner/workspace explicitly does so.\n"
    )

    manifest_content = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    validator = NativePluginPackageValidator()
    validator.validate_manifest(manifest)
    validator.validate_skill(skill_body, expected_name=skill_name)

    return NativePluginPackage(
        plugin_name=plugin_name,
        plugin_version=plugin_version,
        manifest_path=PLUGIN_MANIFEST_PATH,
        skill_path=skill_path,
        manifest_content=manifest_content,
        skill_content=skill_body,
    )


class NativePluginPackageValidator:
    """Pinned, network-free validator for the audited Agent Plugins 1.0 subset."""

    def validate_manifest(self, manifest: Mapping[str, Any]) -> None:
        if manifest.get("$schema") != AGENT_PLUGIN_SCHEMA:
            raise ReleaseProfileValidationError(
                "PLUGIN_SCHEMA_INVALID: unsupported Agent Plugins schema"
            )
        validate_plugin_name(str(manifest.get("name") or ""))
        validate_plugin_version(str(manifest.get("version") or ""))
        _single_line(manifest.get("description") or "", field="plugin description")

        extensions = manifest.get("extensions")
        if not isinstance(extensions, Mapping):
            raise ReleaseProfileValidationError(
                "PLUGIN_SCHEMA_INVALID: extensions.com.openai is required"
            )
        openai = extensions.get("com.openai")
        if not isinstance(openai, Mapping):
            raise ReleaseProfileValidationError(
                "PLUGIN_SCHEMA_INVALID: extensions.com.openai is required"
            )

        apps = openai.get("apps")
        if apps is not None:
            if validate_relative_package_path(str(apps)) != "./.app.json":
                raise ReleaseProfileValidationError(
                    "PLUGIN_SCHEMA_INVALID: OpenAI apps must reference ./.app.json"
                )

        interface = openai.get("interface")
        if not isinstance(interface, Mapping):
            raise ReleaseProfileValidationError(
                "PLUGIN_SCHEMA_INVALID: OpenAI interface metadata is required"
            )
        for key in ("displayName", "shortDescription", "longDescription"):
            _single_line(interface.get(key) or "", field=f"interface.{key}")
        default_prompt = interface.get("defaultPrompt")
        if isinstance(default_prompt, str):
            prompts = (default_prompt,)
        elif isinstance(default_prompt, (list, tuple)):
            prompts = tuple(default_prompt)
        else:
            prompts = ()
        if not prompts or not all(isinstance(item, str) and item.strip() for item in prompts):
            raise ReleaseProfileValidationError(
                "PLUGIN_SCHEMA_INVALID: interface.defaultPrompt must contain prompt text"
            )

        forbidden = {"model", "model_id", "selected_model", "selectedModel"}
        if any(key in manifest for key in forbidden) or any(key in openai for key in forbidden):
            raise ReleaseProfileValidationError(
                "PLUGIN_SCHEMA_INVALID: selected model pinning is not allowed"
            )

    def validate_skill(self, content: str, *, expected_name: str) -> None:
        if not content.startswith("---\n"):
            raise ReleaseProfileValidationError(
                "PLUGIN_SKILL_INVALID: SKILL.md must start with YAML metadata"
            )
        marker = "\n---\n"
        end = content.find(marker, 4)
        if end < 0:
            raise ReleaseProfileValidationError(
                "PLUGIN_SKILL_INVALID: SKILL.md metadata block is incomplete"
            )
        metadata_lines = content[4:end].splitlines()
        metadata: dict[str, str] = {}
        for line in metadata_lines:
            if ":" not in line:
                raise ReleaseProfileValidationError(
                    "PLUGIN_SKILL_INVALID: malformed skill metadata"
                )
            key, raw = line.split(":", 1)
            metadata[key.strip()] = raw.strip()

        name = metadata.get("name", "")
        if name != expected_name:
            raise ReleaseProfileValidationError(
                "PLUGIN_SKILL_INVALID: skill name does not match package path"
            )
        validate_plugin_name(name)

        raw_description = metadata.get("description")
        if raw_description is None:
            raise ReleaseProfileValidationError(
                "PLUGIN_SKILL_INVALID: skill description is required"
            )
        try:
            description = json.loads(raw_description)
        except json.JSONDecodeError as exc:
            raise ReleaseProfileValidationError(
                "PLUGIN_SKILL_INVALID: skill description metadata must be a JSON/YAML string"
            ) from exc
        if not isinstance(description, str):
            raise ReleaseProfileValidationError(
                "PLUGIN_SKILL_INVALID: skill description must be text"
            )
        _single_line(description, field="skill description")

        body = content[end + len(marker):].strip()
        if not body:
            raise ReleaseProfileValidationError(
                "PLUGIN_SKILL_INVALID: skill instructions are required"
            )
