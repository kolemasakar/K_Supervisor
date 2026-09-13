from typing import Protocol


class ProviderSelectionHook(Protocol):
    def select(self, candidates: tuple[str, ...], requirements: dict) -> str | None: ...
