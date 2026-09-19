from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from integrations import AvailabilityState


class ModelSelectionHook(Protocol):
    def select_model(self, candidates: tuple[dict, ...], requirements: dict) -> dict | None: ...


class PriorityModelSelector:
    """Deterministic provider-neutral selector over projected MODEL candidates."""

    _SUPPORTED_REQUIREMENTS = frozenset(
        {"provider_id", "model_id", "features", "minimum_context_window"}
    )

    def select_model(
        self,
        candidates: tuple[dict, ...],
        requirements: dict,
    ) -> dict | None:
        if not isinstance(requirements, dict):
            raise ValueError("model requirements must be an object")
        unknown = set(requirements) - self._SUPPORTED_REQUIREMENTS
        if unknown:
            raise ValueError(
                "unsupported model requirements: " + ", ".join(sorted(unknown))
            )

        provider_id = requirements.get("provider_id")
        model_id = requirements.get("model_id")
        features = requirements.get("features", ())
        minimum_context_window = requirements.get("minimum_context_window")

        if provider_id is not None and not isinstance(provider_id, str):
            raise ValueError("provider_id requirement must be text")
        if model_id is not None and not isinstance(model_id, str):
            raise ValueError("model_id requirement must be text")
        if not isinstance(features, (list, tuple, set, frozenset)) or any(
            not isinstance(item, str) for item in features
        ):
            raise ValueError("features requirement must be a collection of text values")
        if minimum_context_window is not None and (
            isinstance(minimum_context_window, bool)
            or not isinstance(minimum_context_window, int)
            or minimum_context_window < 0
        ):
            raise ValueError("minimum_context_window must be a non-negative integer")

        required_features = set(features)
        compatible: list[dict[str, Any]] = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            candidate_provider = candidate.get("provider_id")
            candidate_model = candidate.get("model_id")
            candidate_features = candidate.get("features", ())
            candidate_context = candidate.get("context_window")
            if provider_id is not None and candidate_provider != provider_id:
                continue
            if model_id is not None and candidate_model != model_id:
                continue
            if not required_features.issubset(set(candidate_features or ())):
                continue
            if minimum_context_window is not None and (
                not isinstance(candidate_context, int)
                or isinstance(candidate_context, bool)
                or candidate_context < minimum_context_window
            ):
                continue
            compatible.append(dict(candidate))

        if not compatible:
            return None

        compatible.sort(
            key=lambda item: (
                -int(item.get("priority", 0)),
                str(item.get("provider_id", "")),
                str(item.get("model_id", "")),
            )
        )
        return compatible[0]


def model_candidates(registry) -> tuple[dict, ...]:
    items = []
    for provider in registry.list("MODEL"):
        if provider.check_availability().state == AvailabilityState.UNAVAILABLE:
            continue
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
