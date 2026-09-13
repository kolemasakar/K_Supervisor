from __future__ import annotations

from models.capability import CapabilityDescriptor, CapabilityRequirement

from .errors import CapabilityResolutionError, RegistryConflictError
from .versioning import matches_version, parse_version


class CapabilityRegistry:
    def __init__(self):
        self._descriptors: dict[tuple[str, str], CapabilityDescriptor] = {}

    def register(self, descriptor: CapabilityDescriptor) -> CapabilityDescriptor:
        key = (descriptor.capability_id, descriptor.capability_version)
        current = self._descriptors.get(key)
        if current is not None:
            if current == descriptor:
                return current
            raise RegistryConflictError(
                f"conflicting capability registration: {descriptor.capability_id}@{descriptor.capability_version}"
            )
        parse_version(descriptor.capability_version)
        self._descriptors[key] = descriptor
        return descriptor

    def unregister(self, capability_id: str, capability_version: str) -> CapabilityDescriptor:
        try:
            return self._descriptors.pop((capability_id, capability_version))
        except KeyError as exc:
            raise KeyError(f"{capability_id}@{capability_version}") from exc

    def get(self, capability_id: str, capability_version: str) -> CapabilityDescriptor | None:
        return self._descriptors.get((capability_id, capability_version))

    def list(self, capability_id: str | None = None) -> tuple[CapabilityDescriptor, ...]:
        values = self._descriptors.values()
        if capability_id is not None:
            values = (item for item in values if item.capability_id == capability_id)
        return tuple(
            sorted(
                values,
                key=lambda item: (item.capability_id, parse_version(item.capability_version)),
            )
        )

    def resolve(
        self,
        capability_id: str,
        version_constraint: str = "*",
        operation: str | None = None,
    ) -> CapabilityDescriptor:
        candidates = [
            item
            for item in self._descriptors.values()
            if item.capability_id == capability_id
            and matches_version(item.capability_version, version_constraint)
            and (operation is None or operation in item.operations)
        ]
        if not candidates:
            raise CapabilityResolutionError(
                f"no compatible capability: {capability_id} {version_constraint}"
            )
        return max(candidates, key=lambda item: parse_version(item.capability_version))

    def resolve_requirement(self, requirement: CapabilityRequirement) -> CapabilityDescriptor:
        return self.resolve(
            requirement.capability_id,
            requirement.version_constraint,
            requirement.operation,
        )
