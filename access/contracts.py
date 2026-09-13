from __future__ import annotations

import re
from typing import Protocol

from pydantic import field_validator

from models.base import ContractModel

_SECRET_REF_RE = re.compile(r"^secret://([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_./-]+)$")


class AccessReference(ContractModel):
    uri: str

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, value: str) -> str:
        if _SECRET_REF_RE.fullmatch(value) is None:
            raise ValueError("access reference must use secret://<scope>/<name>")
        return value

    @property
    def scope(self) -> str:
        match = _SECRET_REF_RE.fullmatch(self.uri)
        assert match is not None
        return match.group(1)

    @property
    def name(self) -> str:
        match = _SECRET_REF_RE.fullmatch(self.uri)
        assert match is not None
        return match.group(2)


class ProtectedSecret:
    __slots__ = ("_value",)

    def __init__(self, value: str):
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "ProtectedSecret(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"


class SecretBackend(Protocol):
    def resolve(self, reference: AccessReference) -> ProtectedSecret: ...
    def available(self, reference: AccessReference) -> bool: ...
