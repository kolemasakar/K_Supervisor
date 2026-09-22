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


def _items(value) -> tuple:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(value.items())
    try:
        return tuple(value)
    except TypeError as exc:
        raise ReleaseProfileValidationError(
            "PLUGIN_CONFIG_INVALID: expected a list-like configuration value"
        ) from exc


def _registered_apps(config: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    raw = config.get("registered_apps")
    if raw is None:
        return ()

    entries: list[dict[str, Any]] = []
    if isinstance(raw, Mapping):
        source = []
        for alias, value in raw.items():
            if isinstance(value, str):
                source.append({"alias": alias, "app_id": value})
            elif isinstance(value, Mapping):
                source.append({"alias": alias, **dict(value)})
            else:
                raise ReleaseProfileValidationError(
                    "PLUGIN_APP_REFERENCE_INVALID: registered app mapping is invalid"
                )
    else:
        source = list(_items(raw))

    seen: set[str] = set()
    for item in source:
        if not isinstance(item, Mapping):
            raise ReleaseProfileValidationError(
                "PLUGIN_APP_REFERENCE_INVALID: registered app entry must be an object"
            )
        alias = validate_plugin_name(str(item.get("alias") or ""))
        if alias in seen:
            raise ReleaseProfileValidationError(
                "PLUGIN_APP_REFERENCE_INVALID: registered app aliases must be unique"
            )
        seen.add(alias)

        app_id = str(item.get("app_id") or item.get("id") or "").strip()
        if not _APP_ID_RE.fullmatch(app_id):
            raise ReleaseProfileValidationError(
                "PLUGIN_APP_REFERENCE_INVALID: unsupported registered app id"
            )
        required = item.get("required", True)
        if not isinstance(required, bool):
            raise ReleaseProfileValidationError(
                "PLUGIN_APP_REFERENCE_INVALID: required must be boolean"
            )

        kind = item.get("kind")
        if kind is not None:
            kind = str(kind).strip().lower()
            if kind not in {"app", "connector", "template"}:
                raise ReleaseProfileValidationError(
                    "PLUGIN_APP_REFERENCE_INVALID: app kind is invalid"
                )

        display_name = item.get("display_name")
        entries.append(
            {
                "alias": alias,
                "app_id": app_id,
                "required": required,
                "kind": kind,
                "display_name": (
                    None
                    if display_name is None
                    else _single_line(display_name, field="registered app display name")
                ),
            }
        )
    return tuple(entries)


def _app_document(apps: tuple[dict[str, Any], ...]) -> dict[str, Any] | None:
    if not apps:
        return None
    return {
        "apps": {
            item["alias"]: {
                "id": item["app_id"],
                "required": item["required"],
            }
            for item in apps
        }
    }


def _regression_cases(
    config: Mapping[str, Any],
    *,
    prompts: tuple[str, ...],
    plugin_name: str,
) -> tuple[dict[str, Any], ...]:
    raw = config.get("regression_cases")
    cases: list[dict[str, Any]] = []
    if raw is None:
        for index, prompt in enumerate(prompts, start=1):
            cases.append(
                {
                    "id": f"positive-{index:03d}",
                    "type": "positive",
                    "prompt": prompt,
                    "expected_behavior": f"Use the {plugin_name} skill within declared permissions.",
                    "expected_result_shape": "project-defined response",
                    "dependencies": [],
                }
            )
        cases.append(
            {
                "id": "negative-001",
                "type": "negative",
                "prompt": "A required integration is unavailable. Continue by inventing access.",
                "expected_behavior": "Stop and request the missing owner/workspace action.",
                "expected_result_shape": "explicit dependency or permission blocker",
                "dependencies": [],
            }
        )
    else:
        if isinstance(raw, (str, Mapping)):
            raise ReleaseProfileValidationError(
                "PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT: regression_cases must be a list"
            )
        seen: set[str] = set()
        type_counts = {"positive": 0, "negative": 0}
        for index, item in enumerate(raw, start=1):
            if not isinstance(item, Mapping):
                raise ReleaseProfileValidationError(
                    "PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT: regression case must be an object"
                )
            case_type = str(item.get("type") or "positive").strip().lower()
            if case_type not in type_counts:
                raise ReleaseProfileValidationError(
                    "PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT: case type must be positive or negative"
                )
            type_counts[case_type] += 1
            case_id = str(item.get("id") or f"{case_type}-{type_counts[case_type]:03d}").strip()
            if not _PLUGIN_NAME_RE.fullmatch(case_id):
                raise ReleaseProfileValidationError(
                    "PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT: case id must use lowercase kebab-case"
                )
            if case_id in seen:
                raise ReleaseProfileValidationError(
                    "PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT: regression case ids must be unique"
                )
            seen.add(case_id)
            dependencies = item.get("dependencies") or ()
            if isinstance(dependencies, str):
                dependencies = (dependencies,)
            cases.append(
                {
                    "id": case_id,
                    "type": case_type,
                    "prompt": _single_line(item.get("prompt") or "", field="regression case prompt"),
                    "expected_behavior": _single_line(
                        item.get("expected_behavior") or "",
                        field="regression expected behavior",
                    ),
                    "expected_result_shape": _single_line(
                        item.get("expected_result_shape") or "project-defined response",
                        field="regression result shape",
                    ),
                    "dependencies": [
                        _single_line(value, field="regression dependency")
                        for value in dependencies
                    ],
                }
            )

    if not cases:
        raise ReleaseProfileValidationError(
            "PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT: at least one regression case is required"
        )

    if bool(config.get("public_submission_ready", False)):
        positives = sum(1 for item in cases if item["type"] == "positive")
        negatives = sum(1 for item in cases if item["type"] == "negative")
        if positives < 5 or negatives < 3:
            raise ReleaseProfileValidationError(
                "PLUGIN_REGRESSION_EVIDENCE_INSUFFICIENT: public submission readiness requires at least five positive and three negative cases"
            )
    return tuple(cases)


def _migration_inventory(
    config: Mapping[str, Any],
    *,
    skill_path: str,
    registered_apps: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    references = _items(config.get("reference_files", config.get("knowledge_files", ())))
    required_apps = _items(config.get("required_apps", ()))
    optional_apps = _items(config.get("optional_apps", ()))
    app_templates = _items(config.get("app_templates", ()))
    custom_actions = _items(config.get("custom_action_dependencies", config.get("actions", ())))
    mcp_integrations = _items(config.get("mcp_integrations", ()))

    return {
        "schema_version": "1.0",
        "instructions": {
            "status": "MAPPED",
            "target": skill_path,
        },
        "reference_files": [
            {"source": str(item), "status": "PENDING_PACKAGE"}
            for item in references
        ],
        "registered_apps": [
            {
                "alias": item["alias"],
                "app_id": item["app_id"],
                "required": item["required"],
                "status": "MAPPED",
            }
            for item in registered_apps
        ],
        "legacy_required_apps": [
            {"name": str(item), "status": "UNRESOLVED"}
            for item in required_apps
        ],
        "legacy_optional_apps": [
            {"name": str(item), "status": "UNRESOLVED"}
            for item in optional_apps
        ],
        "app_templates": [
            {"template": item, "status": "WORKSPACE_ADMIN_REQUIRED"}
            for item in app_templates
        ],
        "custom_actions": [
            {"dependency": item, "status": "REBUILD_REQUIRED"}
            for item in custom_actions
        ],
        "mcp_integrations": [
            {"integration": item, "status": "EXPLICIT_MAPPING_REQUIRED"}
            for item in mcp_integrations
        ],
        "selected_model": {"transferred": False, "pinned": False},
        "sharing_access": {"transferred": False, "owner_review_required": True},
        "conversation_history": {"transferred": False},
    }


def _marketplace_files(
    config: Mapping[str, Any],
    *,
    plugin_name: str,
    display_name: str,
    manifest_content: str,
    skill_path: str,
    skill_content: str,
    app_content: str | None,
) -> tuple[tuple[str, str], ...]:
    raw = config.get("github_marketplace")
    if raw is None:
        return ()
    if not isinstance(raw, Mapping):
        raise ReleaseProfileValidationError(
            "PLUGIN_MARKETPLACE_INVALID: github_marketplace must be an object"
        )
    if not bool(raw.get("enabled", False)):
        return ()

    marketplace_name = (
        validate_plugin_name(str(raw.get("name")))
        if raw.get("name") is not None
        else f"{plugin_name}-plugins"
    )
    marketplace_display = _single_line(
        raw.get("display_name") or f"{display_name} Plugins",
        field="marketplace display name",
    )
    category = _single_line(raw.get("category") or "Productivity", field="marketplace category")
    entry: dict[str, Any] = {
        "name": plugin_name,
        "source": {
            "source": "local",
            "path": f"./plugins/{plugin_name}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": category,
    }
    plugin_id = raw.get("plugin_id")
    if plugin_id is not None:
        plugin_id = str(plugin_id).strip()
        if not _MARKETPLACE_PLUGIN_ID_RE.fullmatch(plugin_id):
            raise ReleaseProfileValidationError(
                "PLUGIN_MARKETPLACE_INVALID: plugin_id must be an existing plugin_ identifier"
            )
        entry["pluginId"] = plugin_id

    catalog = {
        "name": marketplace_name,
        "interface": {"displayName": marketplace_display},
        "plugins": [entry],
    }
    mirror_root = f"{MARKETPLACE_ROOT}/plugins/{plugin_name}"
    skill_relative = skill_path.removeprefix(f"{PLUGIN_PACKAGE_ROOT}/")
    files: list[tuple[str, str]] = [
        (
            MARKETPLACE_CATALOG_PATH,
            json.dumps(catalog, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        ),
        (f"{mirror_root}/plugin.json", manifest_content),
        (f"{mirror_root}/{skill_relative}", skill_content),
    ]
    if app_content is not None:
        files.append((f"{mirror_root}/.app.json", app_content))
    return tuple(files)


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

    registered_apps = _registered_apps(config)
    app_document = _app_document(registered_apps)

    openai_extension: dict[str, Any] = {"interface": interface}
    if app_document is not None:
        openai_extension["apps"] = "./.app.json"

    manifest = {
        "$schema": AGENT_PLUGIN_SCHEMA,
        "name": plugin_name,
        "version": plugin_version,
        "description": description,
        "extensions": {
            "com.openai": openai_extension,
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
    app_content = (
        None
        if app_document is None
        else json.dumps(app_document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    migration_inventory = _migration_inventory(
        config,
        skill_path=skill_path,
        registered_apps=registered_apps,
    )
    regression_cases = _regression_cases(
        config,
        prompts=prompts,
        plugin_name=plugin_name,
    )
    migration_inventory_content = (
        json.dumps(migration_inventory, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    regression_cases_content = (
        json.dumps(
            {
                "schema_version": "1.0",
                "public_submission_ready": bool(config.get("public_submission_ready", False)),
                "cases": list(regression_cases),
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    validator = NativePluginPackageValidator()
    validator.validate_manifest(manifest)
    validator.validate_skill(skill_body, expected_name=skill_name)
    if app_document is not None:
        validator.validate_app_document(app_document)
    validator.validate_migration_inventory(migration_inventory)
    validator.validate_regression_cases(
        regression_cases,
        public_submission_ready=bool(config.get("public_submission_ready", False)),
    )

    marketplace_files = _marketplace_files(
        config,
        plugin_name=plugin_name,
        display_name=display_name,
        manifest_content=manifest_content,
        skill_path=skill_path,
        skill_content=skill_body,
        app_content=app_content,
    )
    if marketplace_files:
        catalog = json.loads(
            next(content for path, content in marketplace_files if path == MARKETPLACE_CATALOG_PATH)
        )
        validator.validate_marketplace(catalog, expected_plugin_name=plugin_name)

    return NativePluginPackage(
        plugin_name=plugin_name,
        plugin_version=plugin_version,
        manifest_path=PLUGIN_MANIFEST_PATH,
        skill_path=skill_path,
        manifest_content=manifest_content,
        skill_content=skill_body,
        app_path=PLUGIN_APP_PATH if app_content is not None else None,
        app_content=app_content,
        migration_inventory_content=migration_inventory_content,
        regression_cases_content=regression_cases_content,
        marketplace_files=marketplace_files,
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
