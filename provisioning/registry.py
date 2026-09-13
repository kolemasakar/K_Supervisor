from __future__ import annotations

from .contracts import ProvisioningAdapter, ProvisioningKind


class ProvisioningRegistry:
    def __init__(self):
        self._adapters: dict[str, ProvisioningAdapter] = {}

    def register(self, adapter: ProvisioningAdapter) -> None:
        existing = self._adapters.get(adapter.provider_id)
        if existing is not None and existing is not adapter:
            raise ValueError(f"provisioning provider already registered: {adapter.provider_id}")
        self._adapters[adapter.provider_id] = adapter

    def resolve(self, provider_id: str, kind: ProvisioningKind) -> ProvisioningAdapter | None:
        adapter = self._adapters.get(provider_id)
        if adapter is None or kind not in adapter.supported_kinds or not adapter.available():
            return None
        return adapter
