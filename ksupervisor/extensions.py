from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from typing import Any, Mapping


EXTENSION_GROUPS = {
    "agent": "k_supervisor.agents",
    "capability": "k_supervisor.capabilities",
    "project_template": "k_supervisor.project_templates",
    "adapter": "k_supervisor.adapters",
}


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


def discover_extensions(kind: str | None = None) -> tuple[DiscoveredExtension, ...]:
    kinds = (kind,) if kind is not None else tuple(EXTENSION_GROUPS)
    unknown = [item for item in kinds if item not in EXTENSION_GROUPS]
    if unknown:
        raise ValueError(f"unknown extension kind: {unknown[0]}")
    found = []
    for item in kinds:
        group = EXTENSION_GROUPS[item]
        for point in _select(group):
            dist = getattr(getattr(point, "dist", None), "name", None)
            found.append(DiscoveredExtension(item, point.name, group, point.value, dist))
    return tuple(sorted(found, key=lambda value: (value.kind, value.name, value.value)))


def activate_extension(kind: str, name: str, context: ExtensionContext) -> Any:
    if kind not in EXTENSION_GROUPS:
        raise ValueError(f"unknown extension kind: {kind}")
    matches = [point for point in _select(EXTENSION_GROUPS[kind]) if point.name == name]
    if len(matches) != 1:
        raise LookupError(f"expected one extension {kind}:{name}, found {len(matches)}")
    extension = matches[0].load()
    registrar = getattr(extension, "register", extension)
    if not callable(registrar):
        raise TypeError("extension must be callable or expose register(context)")
    return registrar(context)
