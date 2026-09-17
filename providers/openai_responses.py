from __future__ import annotations

import http.client
import json
import ssl
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import urlsplit

from access import AccessReference, SecretBackend, SecretNotFoundError
from integrations import AvailabilityReport, AvailabilityState

from .contracts import ModelProfile, ProviderDescriptor, ProviderRequest, ProviderResponse
from .errors import ProviderExecutionError


@dataclass(frozen=True)
class OpenAITransportResponse:
    status_code: int
    payload: Mapping[str, Any]
    request_id: str | None = None


class OpenAITransportTimeout(TimeoutError):
    pass


class OpenAITransportCancelled(RuntimeError):
    pass


class OpenAITransportNetworkError(OSError):
    pass


class OpenAIResponsesTransport(Protocol):
    def create_response(
        self,
        *,
        api_key: str,
        body: Mapping[str, Any],
        connect_timeout_seconds: float,
        request_timeout_seconds: float,
        idempotency_key: str | None,
    ) -> OpenAITransportResponse: ...


class HTTPSOpenAIResponsesTransport:
    """Small stdlib transport so OpenAI SDK is not a mandatory dependency."""

    def __init__(self, base_url: str = "https://api.openai.com/v1") -> None:
        parsed = urlsplit(base_url.rstrip("/"))
        if parsed.scheme != "https" or not parsed.hostname or parsed.query or parsed.fragment:
            raise ValueError("OpenAI base_url must be an https origin/path without query or fragment")
        self._host = parsed.hostname
        self._port = parsed.port
        self._base_path = parsed.path.rstrip("/")

    def create_response(
        self,
        *,
        api_key: str,
        body: Mapping[str, Any],
        connect_timeout_seconds: float,
        request_timeout_seconds: float,
        idempotency_key: str | None,
    ) -> OpenAITransportResponse:
        connection = http.client.HTTPSConnection(
            self._host,
            self._port,
            timeout=connect_timeout_seconds,
            context=ssl.create_default_context(),
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "k-supervisor/0.1 openai-responses-provider/1.0",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        encoded = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        try:
            connection.connect()
            if connection.sock is not None:
                connection.sock.settimeout(request_timeout_seconds)
            connection.request("POST", f"{self._base_path}/responses", body=encoded, headers=headers)
            response = connection.getresponse()
            raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                raise OpenAITransportNetworkError("OpenAI response exceeded transport size limit")
            try:
                decoded = json.loads(raw.decode("utf-8")) if raw else {}
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise OpenAITransportNetworkError("OpenAI response was not valid JSON") from exc
            if not isinstance(decoded, dict):
                raise OpenAITransportNetworkError("OpenAI response JSON was not an object")
            return OpenAITransportResponse(
                status_code=response.status,
                payload=decoded,
                request_id=response.getheader("x-request-id"),
            )
        except TimeoutError as exc:
            raise OpenAITransportTimeout("OpenAI transport timed out") from exc
        except OpenAITransportNetworkError:
            raise
        except OSError as exc:
            raise OpenAITransportNetworkError("OpenAI transport failed") from exc
        finally:
            connection.close()


class OpenAIResponsesProvider:
    PROVIDER_ID = "openai.responses"
    VERSION = "1.0"
    OPERATION = "generate"
    _ALLOWED_PAYLOAD_FIELDS = frozenset({"model", "input", "instructions", "max_output_tokens"})

    def __init__(
        self,
        *,
        secret_backend: SecretBackend,
        credential_ref: AccessReference,
        models: tuple[ModelProfile, ...],
        default_model: str | None = None,
        transport: OpenAIResponsesTransport | None = None,
        connect_timeout_seconds: float = 5.0,
        request_timeout_seconds: float = 60.0,
        max_retries: int = 0,
        retry_backoff_seconds: float = 0.0,
        default_max_output_tokens: int = 1024,
        max_output_tokens_limit: int = 8192,
    ) -> None:
        if not models:
            raise ValueError("OpenAI provider requires at least one configured model profile")
        model_ids = {model.model_id for model in models}
        if default_model is None:
            default_model = models[0].model_id
        if default_model not in model_ids:
            raise ValueError("default_model must be present in configured model profiles")
        if connect_timeout_seconds <= 0 or request_timeout_seconds <= 0:
            raise ValueError("OpenAI timeouts must be positive")
        if max_retries < 0 or max_retries > 5:
            raise ValueError("max_retries must be between 0 and 5")
        if retry_backoff_seconds < 0 or retry_backoff_seconds > 30:
            raise ValueError("retry_backoff_seconds must be between 0 and 30")
        if default_max_output_tokens <= 0 or max_output_tokens_limit <= 0:
            raise ValueError("output token limits must be positive")
        if default_max_output_tokens > max_output_tokens_limit:
            raise ValueError("default_max_output_tokens exceeds max_output_tokens_limit")

        self.secret_backend = secret_backend
        self.credential_ref = credential_ref
        self.transport = transport or HTTPSOpenAIResponsesTransport()
        self.default_model = default_model
        self.connect_timeout_seconds = float(connect_timeout_seconds)
        self.request_timeout_seconds = float(request_timeout_seconds)
        self.max_retries = max_retries
        self.retry_backoff_seconds = float(retry_backoff_seconds)
        self.default_max_output_tokens = default_max_output_tokens
        self.max_output_tokens_limit = max_output_tokens_limit
        self._model_ids = frozenset(model_ids)
        self.descriptor = ProviderDescriptor(
            provider_id=self.PROVIDER_ID,
            version=self.VERSION,
            provider_type="MODEL",
            operations=(self.OPERATION,),
            models=models,
            metadata={"transport": "responses", "stateless": True},
        )

    def check_availability(self) -> AvailabilityReport:
        available = False
        detail: str | None = None
        try:
            available = self.secret_backend.available(self.credential_ref)
        except Exception:
            detail = "credential backend availability check failed"
        if not available and detail is None:
            detail = "configured credential reference is unavailable"
        return AvailabilityReport(
            component_id=self.PROVIDER_ID,
            state=AvailabilityState.AVAILABLE if available else AvailabilityState.UNAVAILABLE,
            checked_at=datetime.now(timezone.utc),
            detail=detail,
            metadata={"configured_models": len(self._model_ids)},
        )

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        if request.operation != self.OPERATION:
            raise self._error("PROVIDER_INVALID_REQUEST", "unsupported provider operation", "invalid_request")
        if self.credential_ref not in request.access_refs:
            raise self._error(
                "PROVIDER_CONFIGURATION_ERROR",
                "required provider credential reference was not authorized for this request",
                "configuration",
            )
        body = self._build_body(request.payload)
        api_key = self._resolve_api_key()
        response = self._perform_request(api_key, body, request.idempotency_key)
        return self._normalize_response(response)

    def _resolve_api_key(self) -> str:
        try:
            protected = self.secret_backend.resolve(self.credential_ref)
        except SecretNotFoundError as exc:
            raise self._error(
                "PROVIDER_CONFIGURATION_ERROR",
                "configured provider credential is unavailable",
                "configuration",
            ) from exc
        except Exception as exc:
            raise self._error(
                "PROVIDER_CONFIGURATION_ERROR",
                "provider credential backend failed",
                "configuration",
            ) from exc
        value = protected.reveal()
        if not value or not value.strip():
            raise self._error(
                "PROVIDER_CONFIGURATION_ERROR",
                "configured provider credential is empty",
                "configuration",
            )
        return value

    def _build_body(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        extra = set(payload) - self._ALLOWED_PAYLOAD_FIELDS
        if extra:
            raise self._error(
                "PROVIDER_INVALID_REQUEST",
                "unsupported OpenAI provider request fields",
                "invalid_request",
            )
        model = payload.get("model", self.default_model)
        if not isinstance(model, str) or model not in self._model_ids:
            raise self._error(
                "PROVIDER_INVALID_REQUEST",
                "requested model is not in the configured provider model set",
                "invalid_request",
            )
        input_text = payload.get("input")
        if not isinstance(input_text, str) or not input_text.strip():
            raise self._error("PROVIDER_INVALID_REQUEST", "input must be non-empty text", "invalid_request")
        instructions = payload.get("instructions")
        if instructions is not None and not isinstance(instructions, str):
            raise self._error("PROVIDER_INVALID_REQUEST", "instructions must be text", "invalid_request")
        max_output_tokens = payload.get("max_output_tokens", self.default_max_output_tokens)
        if isinstance(max_output_tokens, bool) or not isinstance(max_output_tokens, int):
            raise self._error("PROVIDER_INVALID_REQUEST", "max_output_tokens must be an integer", "invalid_request")
        if max_output_tokens <= 0 or max_output_tokens > self.max_output_tokens_limit:
            raise self._error(
                "PROVIDER_INVALID_REQUEST",
                "max_output_tokens is outside the configured provider bound",
                "invalid_request",
            )
        body: dict[str, Any] = {
            "model": model,
            "input": input_text,
            "max_output_tokens": max_output_tokens,
            "store": False,
        }
        if instructions is not None:
            body["instructions"] = instructions
        return body

    def _perform_request(
        self,
        api_key: str,
        body: Mapping[str, Any],
        idempotency_key: str | None,
    ) -> OpenAITransportResponse:
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                response = self.transport.create_response(
                    api_key=api_key,
                    body=body,
                    connect_timeout_seconds=self.connect_timeout_seconds,
                    request_timeout_seconds=self.request_timeout_seconds,
                    idempotency_key=idempotency_key,
                )
            except OpenAITransportCancelled as exc:
                raise self._error("PROVIDER_CANCELLED", "provider request was cancelled", "cancellation") from exc
            except OpenAITransportTimeout as exc:
                error = self._error("PROVIDER_TIMEOUT", "provider request timed out", "timeout", retryable=True)
                if not self._should_retry(error, attempt, attempts, idempotency_key):
                    raise error from exc
                self._backoff()
                continue
            except OpenAITransportNetworkError as exc:
                error = self._error(
                    "PROVIDER_TRANSIENT_ERROR",
                    "provider transport failed",
                    "transient",
                    retryable=True,
                )
                if not self._should_retry(error, attempt, attempts, idempotency_key):
                    raise error from exc
                self._backoff()
                continue

            if 200 <= response.status_code < 300:
                return response
            error = self._http_error(response)
            if not self._should_retry(error, attempt, attempts, idempotency_key):
                raise error
            self._backoff()
        raise AssertionError("provider retry loop exhausted without returning or raising")

    def _should_retry(
        self,
        error: ProviderExecutionError,
        attempt: int,
        attempts: int,
        idempotency_key: str | None,
    ) -> bool:
        return bool(error.retryable and idempotency_key and attempt + 1 < attempts)

    def _backoff(self) -> None:
        if self.retry_backoff_seconds:
            time.sleep(self.retry_backoff_seconds)

    def _http_error(self, response: OpenAITransportResponse) -> ProviderExecutionError:
        provider_code = self._safe_provider_error_code(response.payload)
        status = response.status_code
        if status in {401, 403}:
            return self._error(
                "PROVIDER_AUTHENTICATION_ERROR",
                "provider authentication or authorization failed",
                "authentication",
                provider_code=provider_code,
            )
        if status == 408:
            return self._error(
                "PROVIDER_TIMEOUT",
                "provider request timed out",
                "timeout",
                retryable=True,
                provider_code=provider_code,
            )
        if status == 429:
            return self._error(
                "PROVIDER_RATE_LIMITED",
                "provider rate limit was reached",
                "rate_limit",
                retryable=True,
                provider_code=provider_code,
            )
        if 400 <= status < 500:
            return self._error(
                "PROVIDER_INVALID_REQUEST",
                "provider rejected the request",
                "invalid_request",
                provider_code=provider_code,
            )
        if status in {500, 502, 503, 504}:
            return self._error(
                "PROVIDER_TRANSIENT_ERROR",
                "provider service is temporarily unavailable",
                "transient",
                retryable=True,
                provider_code=provider_code,
            )
        return self._error(
            "PROVIDER_FAILURE",
            "provider request failed",
            "provider_failure",
            provider_code=provider_code,
        )

    def _normalize_response(self, response: OpenAITransportResponse) -> ProviderResponse:
        payload = response.payload
        response_id = payload.get("id")
        model = payload.get("model")
        status = payload.get("status")
        if not isinstance(response_id, str) or not response_id:
            raise self._error("PROVIDER_MALFORMED_RESPONSE", "provider response id is missing", "malformed_response")
        if not isinstance(model, str) or not model:
            raise self._error("PROVIDER_MALFORMED_RESPONSE", "provider response model is missing", "malformed_response")
        if not isinstance(status, str) or not status:
            raise self._error("PROVIDER_MALFORMED_RESPONSE", "provider response status is missing", "malformed_response")
        if status != "completed":
            if status == "cancelled":
                raise self._error("PROVIDER_CANCELLED", "provider response was cancelled", "cancellation")
            if status == "incomplete":
                raise self._error(
                    "PROVIDER_FAILURE",
                    "provider response was incomplete",
                    "provider_failure",
                    provider_code=self._safe_incomplete_reason(payload),
                )
            if status == "failed":
                code = self._safe_provider_error_code(payload)
                retryable = code in {"server_error", "rate_limit_exceeded"}
                return_error = self._error(
                    "PROVIDER_TRANSIENT_ERROR" if retryable else "PROVIDER_FAILURE",
                    "provider response reported failure",
                    "transient" if retryable else "provider_failure",
                    retryable=retryable,
                    provider_code=code,
                )
                raise return_error
            raise self._error(
                "PROVIDER_MALFORMED_RESPONSE",
                "provider returned an unexpected non-terminal response status",
                "malformed_response",
            )
        text = self._extract_output_text(payload)
        if not text:
            raise self._error(
                "PROVIDER_MALFORMED_RESPONSE",
                "provider response did not contain output text",
                "malformed_response",
            )
        usage = self._normalize_usage(payload.get("usage"))
        metadata: dict[str, Any] = {
            "provider_response_id": response_id,
            "model": model,
            "status": status,
            "usage": usage,
        }
        if response.request_id:
            metadata["provider_request_id"] = response.request_id
        return ProviderResponse(payload={"text": text}, metadata=metadata)

    @staticmethod
    def _extract_output_text(payload: Mapping[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct
        parts: list[str] = []
        output = payload.get("output")
        if not isinstance(output, list):
            return ""
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    text = block.get("text")
                    if isinstance(text, str) and text:
                        parts.append(text)
        return "".join(parts)

    @staticmethod
    def _normalize_usage(raw: Any) -> dict[str, int]:
        if not isinstance(raw, dict):
            return {}
        normalized: dict[str, int] = {}
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            value = raw.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                normalized[key] = value
        return normalized

    @staticmethod
    def _safe_provider_error_code(payload: Mapping[str, Any]) -> str | None:
        error = payload.get("error")
        if not isinstance(error, dict):
            return None
        for key in ("code", "type"):
            value = error.get(key)
            if isinstance(value, str) and 0 < len(value) <= 128:
                return value
        return None

    @staticmethod
    def _safe_incomplete_reason(payload: Mapping[str, Any]) -> str | None:
        details = payload.get("incomplete_details")
        if not isinstance(details, dict):
            return None
        reason = details.get("reason")
        return reason if isinstance(reason, str) and 0 < len(reason) <= 128 else None

    @staticmethod
    def _error(
        code: str,
        message: str,
        category: str,
        *,
        retryable: bool = False,
        provider_code: str | None = None,
    ) -> ProviderExecutionError:
        return ProviderExecutionError(
            code,
            message,
            category=category,
            retryable=retryable,
            provider_code=provider_code,
        )
