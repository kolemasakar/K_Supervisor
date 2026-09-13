from __future__ import annotations

from providers import Provider

from .errors import RegistryConflictError
from .versioning import matches_version, parse_version


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[tuple[str, str], Provider] = {}

    def register(self, provider: Provider) -> None:
        descriptor = provider.descriptor
        parse_version(descriptor.version)
        key = (descriptor.provider_id, descriptor.version)
        existing = self._providers.get(key)
        if existing is not None and existing.descriptor != descriptor:
            raise RegistryConflictError(
                f"conflicting provider registration: {descriptor.provider_id}@{descriptor.version}"
            )
        if existing is None:
            self._providers[key] = provider

    def list(self, provider_type: str | None = None) -> tuple[Provider, ...]:
        values = tuple(self._providers.values())
        if provider_type is not None:
            values = tuple(
                item for item in values if item.descriptor.provider_type == provider_type
            )
        return tuple(sorted(values, key=lambda item: (item.descriptor.provider_id, parse_version(item.descriptor.version))))

    def resolve(self, provider_id: str, constraint: str = "*", operation: str | None = None) -> Provider | None:
        candidates = [
            provider
            for (registered_id, version), provider in self._providers.items()
            if registered_id == provider_id
            and matches_version(version, constraint)
            and (operation is None or operation in provider.descriptor.operations)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda item: parse_version(item.descriptor.version))
