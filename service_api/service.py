from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from models.control import ServiceMutationRecord
from models.project import Project
from persistence.base import PersistenceConflictError, PersistenceStore
from registry.project_registry import ProjectRegistry

from .operator import OperatorApiError, OperatorControlApi

from .contracts import (
    API_VERSION,
    LIFECYCLE_WRITE_SCOPE,
    OPERATIONAL_WRITE_SCOPE,
    READ_SCOPE,
    ApiResponse,
    LifecycleTransitionRequest,
    OperationalTransitionRequest,
    ServicePrincipal,
)


class ServiceApiError(RuntimeError):
    def __init__(self, code: str, status_code: int, message: str):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message


class ServiceApiV1:
    """Versioned service boundary over the authoritative ProjectRegistry control plane."""

    BASE_PATH = "/api/v1"
    MAX_IDEMPOTENCY_KEY_LENGTH = 256

    def __init__(
        self,
        projects: ProjectRegistry,
        store: PersistenceStore,
        telemetry=None,
        *,
        kernel=None,
        workflows=None,
        human=None,
        approvals=None,
        releases=None,
        project_factory=None,
    ):
        if projects.store is not store:
            raise ValueError("ProjectRegistry and ServiceApiV1 must share one PersistenceStore")
        self.projects = projects
        self.store = store
        self.telemetry = telemetry
        self.operator = OperatorControlApi(
            projects,
            store,
            kernel=kernel,
            workflows=workflows,
            human=human,
            approvals=approvals,
            releases=releases,
            project_factory=project_factory,
        )

    def dispatch(
        self,
        method: str,
        path: str,
        *,
        principal: ServicePrincipal | None,
        body: Any = None,
        idempotency_key: str | None = None,
    ) -> ApiResponse:
        method = method.upper()
        project_id = self._project_id_from_path(path)
        if (
            project_id is None
            and method == "POST"
            and path.rstrip("/") == f"{self.BASE_PATH}/projects"
            and isinstance(body, dict)
        ):
            candidate = body.get("project_id")
            project_id = candidate if isinstance(candidate, str) and candidate else None
        try:
            response = self._dispatch(
                method,
                path,
                principal=principal,
                body=body,
                idempotency_key=idempotency_key,
            )
        except (ServiceApiError, OperatorApiError) as exc:
            response = self.error_response(
                exc.code,
                exc.status_code,
                exc.message,
                details=getattr(exc, "details", None),
            )
        except Exception:
            response = self.error_response(
                "INTERNAL_ERROR",
                500,
                "internal service error",
            )
        self._telemetry(project_id, method, path, response.status_code, principal)
        return response


    def _telemetry(self, project_id, method, path, status_code, principal) -> None:
        if self.telemetry is None or project_id is None:
            return
        try:
            self.telemetry.record(
                project_id=project_id,
                event_name="service.request.completed",
                correlation_id=None,
                service_operation=f"{method} {path}",
                status=str(status_code),
                attributes={"method": method, "path": path, "principal_id": None if principal is None else principal.principal_id},
            )
        except Exception:
            pass

    @classmethod
    def _project_id_from_path(cls, path: str) -> str | None:
        normalized = path.rstrip("/")
        prefix = f"{cls.BASE_PATH}/projects/"
        if not normalized.startswith(prefix):
            return None
        value = normalized[len(prefix):].split("/", 1)[0]
        return value or None

    def _dispatch(
        self,
        method: str,
        path: str,
        *,
        principal: ServicePrincipal | None,
        body: Any,
        idempotency_key: str | None,
    ) -> ApiResponse:
        normalized = path.rstrip("/") or "/"
        operator_response = self.operator.dispatch_if_supported(
            method,
            normalized,
            principal=principal,
            body=body,
            idempotency_key=idempotency_key,
        )
        if operator_response is not None:
            return operator_response

        if normalized == f"{self.BASE_PATH}/projects":
            if method != "GET":
                raise ServiceApiError("METHOD_NOT_ALLOWED", 405, "method not allowed")
            self._require_scope(principal, READ_SCOPE)
            projects = [self._project_payload(item) for item in self.projects.list()]
            return self._success({"projects": projects})

        prefix = f"{self.BASE_PATH}/projects/"
        if not normalized.startswith(prefix):
            raise ServiceApiError("NOT_FOUND", 404, "route not found")

        remainder = normalized[len(prefix):]
        parts = remainder.split("/")
        if not parts[0] or len(parts) > 2:
            raise ServiceApiError("NOT_FOUND", 404, "route not found")
        project_id = parts[0]

        if len(parts) == 1:
            if method != "GET":
                raise ServiceApiError("METHOD_NOT_ALLOWED", 405, "method not allowed")
            self._require_scope(principal, READ_SCOPE)
            project = self.projects.get(project_id)
            if project is None:
                raise ServiceApiError("NOT_FOUND", 404, "project not found")
            return self._success({"project": self._project_payload(project)})

        action = parts[1]
        if method != "POST":
            raise ServiceApiError("METHOD_NOT_ALLOWED", 405, "method not allowed")

        if action == "lifecycle-transitions":
            self._require_scope(principal, LIFECYCLE_WRITE_SCOPE)
            key = self._require_idempotency_key(idempotency_key)
            request = self._validate(LifecycleTransitionRequest, body)
            return self._mutate(
                project_id,
                operation="lifecycle-transition",
                idempotency_key=key,
                request_payload=request.model_dump(mode="json"),
                mutate=lambda at: self.projects.transition_lifecycle(
                    project_id,
                    request.to_state,
                    request.reason,
                    request.trigger,
                    at,
                ),
            )

        if action == "operational-transitions":
            self._require_scope(principal, OPERATIONAL_WRITE_SCOPE)
            key = self._require_idempotency_key(idempotency_key)
            request = self._validate(OperationalTransitionRequest, body)
            return self._mutate(
                project_id,
                operation="operational-transition",
                idempotency_key=key,
                request_payload=request.model_dump(mode="json"),
                mutate=lambda at: self.projects.transition_operational(
                    project_id,
                    request.to_state,
                    at,
                ),
            )

        raise ServiceApiError("NOT_FOUND", 404, "route not found")

    def _mutate(
        self,
        project_id: str,
        *,
        operation: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
        mutate: Callable[[datetime], Project],
    ) -> ApiResponse:
        signature = self._signature(request_payload)
        record_id = self._record_id(project_id, operation, idempotency_key)
        now = datetime.now(timezone.utc)

        try:
            with self.store.transaction():
                existing = self.store.get_service_mutation(record_id)
                if existing is not None:
                    if existing.signature != signature:
                        raise ServiceApiError(
                            "IDEMPOTENCY_CONFLICT",
                            409,
                            "idempotency key was already used with a different request",
                        )
                    return self._success(
                        {"project": self._project_payload(existing.result)},
                        meta={"idempotent_replay": True},
                    )

                try:
                    project = mutate(now)
                except KeyError as exc:
                    raise ServiceApiError("NOT_FOUND", 404, "project not found") from exc
                except (ValidationError, ValueError) as exc:
                    raise ServiceApiError(
                        "INVALID_TRANSITION",
                        409,
                        "invalid project state transition",
                    ) from exc

                record = ServiceMutationRecord(
                    record_id=record_id,
                    project_id=project_id,
                    api_version=API_VERSION,
                    operation=operation,
                    idempotency_key=idempotency_key,
                    signature=signature,
                    result=project,
                    created_at=now,
                )
                self.store.save_service_mutation(record)
        except PersistenceConflictError as exc:
            raise ServiceApiError(
                "IDEMPOTENCY_CONFLICT",
                409,
                "idempotency key conflict",
            ) from exc

        return self._success(
            {"project": self._project_payload(project)},
            meta={"idempotent_replay": False},
        )

    @staticmethod
    def _validate(model, body):
        try:
            return model.model_validate(body)
        except ValidationError as exc:
            raise ServiceApiError("INVALID_REQUEST", 400, "invalid request body") from exc

    def _require_idempotency_key(self, value: str | None) -> str:
        if value is None or not value.strip():
            raise ServiceApiError(
                "IDEMPOTENCY_REQUIRED",
                400,
                "Idempotency-Key is required for mutations",
            )
        key = value.strip()
        if len(key) > self.MAX_IDEMPOTENCY_KEY_LENGTH:
            raise ServiceApiError(
                "INVALID_REQUEST",
                400,
                "Idempotency-Key is too long",
            )
        return key

    @staticmethod
    def _require_scope(principal: ServicePrincipal | None, scope: str) -> None:
        if principal is None:
            raise ServiceApiError("AUTH_REQUIRED", 401, "authentication required")
        if scope not in principal.scopes:
            raise ServiceApiError("ACCESS_DENIED", 403, "required scope is missing")

    @staticmethod
    def _signature(payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _record_id(project_id: str, operation: str, idempotency_key: str) -> str:
        scope = f"{API_VERSION}\0{project_id}\0{operation}\0{idempotency_key}".encode("utf-8")
        return "SERVICE_MUTATION_" + hashlib.sha256(scope).hexdigest()

    @staticmethod
    def _project_payload(project: Project) -> dict[str, Any]:
        return project.model_dump(mode="json")

    @staticmethod
    def _success(data: dict[str, Any], *, meta: dict[str, Any] | None = None) -> ApiResponse:
        body: dict[str, Any] = {"api_version": API_VERSION, "data": data}
        if meta is not None:
            body["meta"] = meta
        return ApiResponse(status_code=200, body=body)

    @staticmethod
    def error_response(
        code: str,
        status_code: int,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> ApiResponse:
        error: dict[str, Any] = {"code": code, "message": message}
        if details:
            error["details"] = details
        return ApiResponse(
            status_code=status_code,
            body={
                "api_version": API_VERSION,
                "error": error,
            },
        )
