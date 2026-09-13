from typing import Protocol


class ModelSelectionHook(Protocol):
    def select_model(self, candidates: tuple[dict, ...], requirements: dict) -> dict | None: ...


def model_candidates(registry) -> tuple[dict, ...]:
    items = []
    for provider in registry.list("MODEL"):
        for model in provider.descriptor.models:
            items.append(
                {
                    "provider_id": provider.descriptor.provider_id,
                    "provider_version": provider.descriptor.version,
                    "model_id": model.model_id,
                    "features": model.features,
                    "context_window": model.context_window,
                    "priority": model.priority,
                }
            )
    return tuple(items)
