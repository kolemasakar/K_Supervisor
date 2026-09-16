from __future__ import annotations

import json
from http import HTTPStatus
from typing import Any

from .auth import ServiceAuthenticator
from .service import ServiceApiV1


class WsgiServiceAppV1:
    """Thin WSGI adapter for ServiceApiV1; deployment/hosting remains external."""

    MAX_BODY_BYTES = 64 * 1024

    def __init__(self, api: ServiceApiV1, authenticator: ServiceAuthenticator):
        self.api = api
        self.authenticator = authenticator

    def __call__(self, environ: dict[str, Any], start_response):
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        principal = self.authenticator.authenticate(environ.get("HTTP_AUTHORIZATION"))
        idempotency_key = environ.get("HTTP_IDEMPOTENCY_KEY")

        if principal is None:
            response = self.api.dispatch(
                method,
                path,
                principal=None,
                body=None,
                idempotency_key=idempotency_key,
            )
        else:
            try:
                body = self._read_json_body(environ, method)
            except ValueError as exc:
                response = self.api.error_response("INVALID_REQUEST", 400, str(exc))
            else:
                response = self.api.dispatch(
                    method,
                    path,
                    principal=principal,
                    body=body,
                    idempotency_key=idempotency_key,
                )

        payload = json.dumps(response.body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        status = HTTPStatus(response.status_code)
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(payload))),
            ("Cache-Control", "no-store"),
        ]
        headers.extend(response.headers.items())
        start_response(f"{status.value} {status.phrase}", headers)
        return [payload]

    def _read_json_body(self, environ: dict[str, Any], method: str):
        if method not in {"POST", "PUT", "PATCH"}:
            return None
        raw_length = environ.get("CONTENT_LENGTH", "")
        try:
            length = int(raw_length) if raw_length else 0
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > self.MAX_BODY_BYTES:
            raise ValueError("request body is too large")
        stream = environ.get("wsgi.input")
        raw = b"" if stream is None else stream.read(length)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be valid UTF-8 JSON") from exc
