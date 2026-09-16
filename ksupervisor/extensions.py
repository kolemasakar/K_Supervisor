from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib import metadata
import json
import re
from typing import Any, Mapping

from models.extension import ExtensionSignatureStatus, ExtensionTrustRecord
from persistence.base import PersistenceStore
from registry.versioning import VersionConstraintError, matches_version


EXTENSION_GROUPS = {
    "agent": "k_supervisor.agents",
    "capability": "k_supervisor.capabilities",
    "project_template": "k_supervisor.project_templates",
    "adapter": "k_supervisor.adapters",
}

_FALLBACK_PLATFORM_VERSION = "0.1.0"
_PLATFORM_REQUIREMENT = re.compile(
    r"^k[-_.]supervisor\s*(?:\(([^)]+)\)|([<>=~^].*))?$", re.IGNORECASE
)


class ExtensionActivationError(RuntimeError):
    """Raised before import when an installed extension fails governance checks."""


class NamedExtensionRegistry:
    def __init__(self):
        self._items: dict[str, Any] = {}

    def register(self, name: str, value: Any) -> None:
        if not name.strip():
            raise ValueError("extension name must not be empty")
        existing = self._items.get(name)
        if existing is not None and existing is not value:
            raise ValueError(f"extension already registered: {name}")
        self._items[name] = value

    def get(self, name: str) -> Any:
        try:
            return self._items[name]
        except KeyError as exc:
            raise KeyError(f"extension is not registered: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))


@dataclass(frozen=True)
class DiscoveredExtension:
    kind: str
    name: str
    group: str
    value: str
    distribution: str | None = None
    distribution_version: str | None = None
    platform_constraint: str | None = None
    identity: str | None = None


@dataclass(frozen=True)
class ExtensionContext:
    services: Mapping[str, Any]

    def require(self, name: str) -> Any:
        try:
            return self.services[name]
        except KeyError as exc:
            raise KeyError(f"extension service is unavailable: {name}") from exc


def _select(group: str):
    points = metadata.entry_points()
    if hasattr(points, "select"):
        return tuple(points.select(group=group))
    return tuple(points.get(group, ()))


def _platform_constraint(distribution: Any) -> str | None:
    if distribution is None:
        return None
    for raw in getattr(distribution, "requires", None) or ():
        requirement = raw.split(";", 1)[0].strip()
        match = _PLATFORM_REQUIREMENT.fullmatch(requirement)
        if match:
            constraint = (match.group(1) or match.group(2) or "*").strip()
            return constraint
    return None


def _identity_payload(
    *,
    kind: str,
    name: str,
    group: str,
    value: str,
    distribution: str | None,
    distribution_version: str | None,
    platform_constraint: str | None,
) -> str:
    payload = json.dumps(
        {
            "kind": kind,
            "name": name,
            "group": group,
            "value": value,
            "distribution": distribution,
            "distribution_version": distribution_version,
            "platform_constraint": platform_constraint,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _describe_point(kind: str, point: Any) -> DiscoveredExtension:
    distribution = getattr(point, "dist", None)
    distribution_name = getattr(distribution, "name", None)
    distribution_version = getattr(distribution, "version", None)
    constraint = _platform_constraint(distribution)
    group = EXTENSION_GROUPS[kind]
    identity = _identity_payload(
        kind=kind,
        name=point.name,
        group=group,
        value=point.value,
        distribution=distribution_name,
        distribution_version=distribution_version,
        platform_constraint=constraint,
    )
    return DiscoveredExtension(
        kind=kind,
        name=point.name,
        group=group,
        value=point.value,
        distribution=distribution_name,
        distribution_version=distribution_version,
        platform_constraint=constraint,
        identity=identity,
    )


def _current_platform_version() -> str:
    try:
        return metadata.version("k-supervisor")
    except metadata.PackageNotFoundError:
        return _FALLBACK_PLATFORM_VERSION


class ExtensionGovernance:
    """Durable pre-import authorization for installed Python extensions."""

    def __init__(self, store: PersistenceStore, *, platform_version: str | None = None):
        self.store = store
        self.platform_version = platform_version or _current_platform_version()

    def set_policy(
        self,
        extension: DiscoveredExtension,
        *,
        enabled: bool,
        trusted: bool,
        signature_status: ExtensionSignatureStatus,
        provenance: str,
        verification_reference: str | None = None,
    ) -> ExtensionTrustRecord:
        if extension.distribution is None or extension.distribution_version is None:
            raise ValueError("installed extension distribution provenance is required")
        if extension.platform_constraint is None:
            raise ValueError("installed extension must declare K_Supervisor compatibility")
        if extension.identity is None:
            raise ValueError("extension identity is required")
        record = ExtensionTrustRecord(
            record_id=extension.identity,
            extension_identity=extension.identity,
            kind=extension.kind,
            name=extension.name,
            group=extension.group,
            value=extension.value,
            distribution=extension.distribution,
            distribution_version=extension.distribution_version,
            platform_constraint=extension.platform_constraint,
            provenance=provenance,
            enabled=enabled,
            trusted=trusted,
            signature_status=signature_status,
            verification_reference=verification_reference,
        )
        self.store.save_extension_trust(record)
        return record

    def authorize(self, extension: DiscoveredExtension) -> ExtensionTrustRecord:
        if extension.distribution is None:
            raise ExtensionActivationError("installed extension distribution provenance is missing")
        if extension.distribution_version is None:
            raise ExtensionActivationError("installed extension distribution version is missing")
        if extension.platform_constraint is None:
            raise ExtensionActivationError("installed extension compatibility declaration is missing")
        try:
            compatible = matches_version(self.platform_version, extension.platform_constraint)
        except VersionConstraintError as exc:
            raise ExtensionActivationError("installed extension compatibility declaration is invalid") from exc
        if not compatible:
            raise ExtensionActivationError(
                f"extension is incompatible with K_Supervisor {self.platform_version}"
            )
        if extension.identity is None:
            raise ExtensionActivationError("extension identity is missing")
        record = self.store.get_extension_trust(extension.identity)
        if record is None:
            raise ExtensionActivationError("extension has no trust decision for this exact identity")
        expected = (
            extension.identity, extension.kind, extension.name, extension.group,
            extension.value, extension.distribution, extension.distribution_version,
            extension.platform_constraint,
        )
        actual = (
            record.extension_identity, record.kind, record.name, record.group,
            record.value, record.distribution, record.distribution_version,
            record.platform_constraint,
        )
        if actual != expected:
            raise ExtensionActivationError("extension trust record does not match exact identity")
        if not record.enabled:
            raise ExtensionActivationError("extension is disabled")
        if not record.trusted:
            raise ExtensionActivationError("extension is not trusted")
        if record.signature_status != ExtensionSignatureStatus.VERIFIED:
            raise ExtensionActivationError("extension signature is not verified")
        if record.verification_reference is None or not record.verification_reference.strip():
            raise ExtensionActivationError("extension signature verification evidence is missing")
        return record


def discover_extensions(kind: str | None = None) -> tuple[DiscoveredExtension, ...]:
    kinds = (kind,) if kind is not None else tuple(EXTENSION_GROUPS)
    unknown = [item for item in kinds if item not in EXTENSION_GROUPS]
    if unknown:
        raise ValueError(f"unknown extension kind: {unknown[0]}")
    found = []
    for item in kinds:
        for point in _select(EXTENSION_GROUPS[item]):
            found.append(_describe_point(item, point))
    return tuple(sorted(found, key=lambda value: (value.kind, value.name, value.value)))


def activate_extension(
    kind: str,
    name: str,
    context: ExtensionContext,
    governance: ExtensionGovernance | None = None,
) -> Any:
    if kind not in EXTENSION_GROUPS:
        raise ValueError(f"unknown extension kind: {kind}")
    matches = [point for point in _select(EXTENSION_GROUPS[kind]) if point.name == name]
    if len(matches) != 1:
        raise LookupError(f"expected one extension {kind}:{name}, found {len(matches)}")
    point = matches[0]
    descriptor = _describe_point(kind, point)
    if getattr(point, "dist", None) is not None:
        if governance is None:
            raise ExtensionActivationError("installed extension activation requires governance")
        governance.authorize(descriptor)
    extension = point.load()
    registrar = getattr(extension, "register", extension)
    if not callable(registrar):
        raise TypeError("extension must be callable or expose register(context)")
    return registrar(context)
