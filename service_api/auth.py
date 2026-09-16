from __future__ import annotations

import hmac
from collections.abc import Mapping
from typing import Protocol

from .contracts import ServicePrincipal


class ServiceAuthenticator(Protocol):
    def authenticate(self, authorization: str | None) -> ServicePrincipal | None: ...


class StaticBearerAuthenticator:
    """Host-supplied in-memory Bearer mapping; tokens are never persisted by the API."""

    def __init__(self, tokens: Mapping[str, ServicePrincipal]):
        if any(not token for token in tokens):
            raise ValueError("bearer token must not be empty")
        self._tokens = tuple(tokens.items())

    def authenticate(self, authorization: str | None) -> ServicePrincipal | None:
        if authorization is None:
            return None
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token:
            return None
        for expected, principal in self._tokens:
            if hmac.compare_digest(token, expected):
                return principal
        return None
