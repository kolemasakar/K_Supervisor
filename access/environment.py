from __future__ import annotations

import os
import re
from collections.abc import Mapping

from .contracts import AccessReference, ProtectedSecret


class SecretNotFoundError(KeyError):
    pass


def environment_key(reference: AccessReference, prefix: str = "KSUP_SECRET") -> str:
    raw = f"{reference.scope}__{reference.name}"
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()
    return f"{prefix}__{normalized}"


class EnvironmentSecretBackend:
    def __init__(
        self,
        values: Mapping[str, str] | None = None,
        *,
        prefix: str = "KSUP_SECRET",
    ):
        self._values = os.environ if values is None else values
        self.prefix = prefix

    def resolve(self, reference: AccessReference) -> ProtectedSecret:
        key = environment_key(reference, self.prefix)
        value = self._values.get(key)
        if value is None:
            raise SecretNotFoundError(reference.uri)
        return ProtectedSecret(value)

    def available(self, reference: AccessReference) -> bool:
        return environment_key(reference, self.prefix) in self._values
