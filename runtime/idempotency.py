from __future__ import annotations

from datetime import datetime, timezone
from json import dumps
from threading import RLock

from models.agent import AgentRunRequest, AgentRunResult
from models.control import RuntimeIdempotencyRecord
from persistence.base import PersistenceConflictError, PersistenceStore

from .errors import IdempotencyConflictError


def _scope(request: AgentRunRequest) -> str:
    return "|".join(
        (
            request.project_id,
            request.agent_id,
            request.capability_id,
            request.capability_version,
            request.operation,
            request.idempotency_key or "",
        )
    )


def _signature(request: AgentRunRequest) -> str:
    return dumps(request.input, sort_keys=True, separators=(",", ":"), default=str)


def _replay_result(request: AgentRunRequest, result: AgentRunResult) -> AgentRunResult:
    return result.model_copy(
        update={
            "request_id": request.request_id,
            "project_id": request.project_id,
            "task_id": request.task_id,
            "workflow_run_id": request.workflow_run_id,
            "run_id": request.run_id,
            "metadata": {**result.metadata, "idempotent_replay": True},
        }
    )


class MemoryIdempotencyStore:
    """Compatibility store for standalone runtimes that do not own persistence."""

    def __init__(self):
        self._records: dict[str, tuple[str, AgentRunResult]] = {}
        self._lock = RLock()

    def replay(self, request: AgentRunRequest) -> AgentRunResult | None:
        if request.idempotency_key is None:
            return None
        scope = _scope(request)
        signature = _signature(request)
        with self._lock:
            record = self._records.get(scope)
        if record is None:
            return None
        if record[0] != signature:
            raise IdempotencyConflictError(
                "idempotency key reused with a different input payload"
            )
        return _replay_result(request, record[1])

    def remember(self, request: AgentRunRequest, result: AgentRunResult) -> None:
        if request.idempotency_key is None:
            return
        scope = _scope(request)
        signature = _signature(request)
        with self._lock:
            current = self._records.get(scope)
            if current is not None and current[0] != signature:
                raise IdempotencyConflictError(
                    "idempotency key reused with a different input payload"
                )
            self._records[scope] = (signature, result)


class PersistenceIdempotencyStore:
    """Durable idempotency store backed by the platform persistence boundary."""

    def __init__(self, store: PersistenceStore):
        self.store = store

    @staticmethod
    def _record_id(request: AgentRunRequest) -> str:
        return f"runtime:{_scope(request)}"

    def replay(self, request: AgentRunRequest) -> AgentRunResult | None:
        if request.idempotency_key is None:
            return None
        record = self.store.get_runtime_idempotency(self._record_id(request))
        if record is None:
            return None
        if record.signature != _signature(request):
            raise IdempotencyConflictError(
                "idempotency key reused with a different input payload"
            )
        return _replay_result(request, record.result)

    def remember(self, request: AgentRunRequest, result: AgentRunResult) -> None:
        if request.idempotency_key is None:
            return
        record_id = self._record_id(request)
        signature = _signature(request)
        current = self.store.get_runtime_idempotency(record_id)
        if current is not None:
            if current.signature != signature:
                raise IdempotencyConflictError(
                    "idempotency key reused with a different input payload"
                )
            return
        record = RuntimeIdempotencyRecord(
            record_id=record_id,
            project_id=request.project_id,
            scope=_scope(request),
            signature=signature,
            result=result,
            created_at=datetime.now(timezone.utc),
        )
        try:
            self.store.save_runtime_idempotency(record)
        except PersistenceConflictError as exc:
            current = self.store.get_runtime_idempotency(record_id)
            if current is None or current.signature != signature:
                raise IdempotencyConflictError(
                    "idempotency key reused concurrently with a different input payload"
                ) from exc
