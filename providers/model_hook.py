from typing import Protocol


class ModelSelectionHook(Protocol):
    def select_model(self, candidates: tuple[dict, ...], requirements: dict) -> dict | None: ...
