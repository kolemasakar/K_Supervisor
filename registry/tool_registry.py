from __future__ import annotations

from tools import Tool

from .errors import RegistryConflictError
from .versioning import matches_version, parse_version


class ToolRegistry:
    def __init__(self):
        self._tools: dict[tuple[str, str], Tool] = {}

    def register(self, tool: Tool) -> None:
        descriptor = tool.descriptor
        parse_version(descriptor.version)
        key = (descriptor.tool_id, descriptor.version)
        existing = self._tools.get(key)
        if existing is not None and existing.descriptor != descriptor:
            raise RegistryConflictError(
                f"conflicting tool registration: {descriptor.tool_id}@{descriptor.version}"
            )
        if existing is None:
            self._tools[key] = tool

    def list(self) -> tuple[Tool, ...]:
        return tuple(
            sorted(
                self._tools.values(),
                key=lambda item: (item.descriptor.tool_id, parse_version(item.descriptor.version)),
            )
        )

    def resolve(self, tool_id: str, constraint: str = "*", operation: str | None = None) -> Tool | None:
        candidates = [
            tool
            for (registered_id, version), tool in self._tools.items()
            if registered_id == tool_id
            and matches_version(version, constraint)
            and (operation is None or operation in tool.descriptor.operations)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda item: parse_version(item.descriptor.version))
