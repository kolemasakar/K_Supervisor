from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ServiceClientResponse:
    status_code: int
    body: dict[str, Any]
    headers: dict[str, str]


class ServiceClientError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.retryable = retryable


class ServiceClientV1:
    """Transport-only HTTP client for the versioned Service/API boundary."""

    def __init__(self, base_url: str, bearer_token: str, *, timeout_seconds: float = 30.0):
        if not bearer_token:
            raise ValueError("service bearer token must not be empty")
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise ValueError("service client timeout must be in (0, 300]")
        normalized = base_url.rstrip("/")
        parsed = urlsplit(normalized)
        if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
            raise ValueError("service base_url must use http or https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("service base_url must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("service base_url must not contain query or fragment")
        if parsed.scheme == "http":
            host = parsed.hostname.lower()
            loopback = host == "localhost"
            if not loopback:
                try:
                    loopback = ip_address(host).is_loopback
                except ValueError:
                    loopback = False
            if not loopback:
                raise ValueError("cleartext service URLs are allowed only on loopback")
        self.base_url = normalized + "/"
        self._bearer_token = bearer_token
        self.timeout_seconds = timeout_seconds
    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        idempotency_key: str | None = None,
    ) -> ServiceClientResponse:
        if not path.startswith("/"):
            raise ValueError("service request path must be absolute")
        payload = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._bearer_token}",
        }
        if body is not None:
            payload = json.dumps(
                body,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        request = Request(
            urljoin(self.base_url, path.lstrip("/")),
            data=payload,
            headers=headers,
            method=method.upper(),
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
                return ServiceClientResponse(
                    status_code=int(response.status),
                    body=self._decode_json(raw),
                    headers={key: value for key, value in response.headers.items()},
                )
        except HTTPError as exc:
            try:
                raw = exc.read()
                body_value = self._decode_json(raw, allow_invalid=True)
                error = body_value.get("error") if isinstance(body_value, dict) else None
                code = error.get("code") if isinstance(error, dict) else "HTTP_ERROR"
                message = error.get("message") if isinstance(error, dict) else "service request failed"
                raise ServiceClientError(
                    str(code),
                    str(message),
                    status_code=exc.code,
                    retryable=exc.code >= 500,
                ) from None
            finally:
                exc.close()
        except (TimeoutError, socket.timeout):
            raise ServiceClientError(
                "TRANSPORT_TIMEOUT",
                "service request timed out; mutation outcome may be uncertain",
                retryable=True,
            ) from None
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise ServiceClientError(
                    "TRANSPORT_TIMEOUT",
                    "service request timed out; mutation outcome may be uncertain",
                    retryable=True,
                ) from None
            raise ServiceClientError(
                "TRANSPORT_UNAVAILABLE",
                "service transport is unavailable",
                retryable=True,
            ) from None

    @staticmethod
    def _decode_json(raw: bytes, *, allow_invalid: bool = False) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if allow_invalid:
                return {}
            raise ServiceClientError(
                "INVALID_RESPONSE",
                "service returned an invalid JSON response",
            ) from None
        if not isinstance(value, dict):
            if allow_invalid:
                return {}
            raise ServiceClientError(
                "INVALID_RESPONSE",
                "service returned a non-object JSON response",
            )
        return value
