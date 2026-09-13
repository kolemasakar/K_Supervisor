from __future__ import annotations

from dataclasses import dataclass
from json import dumps
from threading import RLock

from models.agent import AgentRunRequest, AgentRunResult

from .errors import IdempotencyConflictError


@dataclass(frozen=True)
class IdempotencyRecord:
    signature: str
    result: AgentRunResult


class MemoryIdempotencyStore:
    def __init__(self):
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = RLock()

    @staticmethod
    def _scope(request: AgentRunRequest) -> str:
        return "|".join(
            (
                request.agent_id,
                request.capability_id,
                request.capability_version,
                request.operation,
                request.idempotency_key or "",
            )
        )

    @staticmethod
    def _signature(request: AgentRunRequest) -> str:
        return dumps(request.input, sort_keys=True, separators=(",", ":"), default=str)

    def replay(self, request: AgentRunRequest) -> AgentRunResult | None:
        if request.idempotency_key is None:
            return None
        scope = self._scope(request)
        signature = self._signature(request)
        with self._lock:
            record = self._records.get(scope)
        if record is None:
            return None
        if record.signature != signature:
            raise IdempotencyConflictError(
                "idempotency key reused with a different input payload"
            )
        return record.result.model_copy(
            update={
                "request_id": request.request_id,
                "project_id": request.project_id,
                "task_id": request.task_id,
                "workflow_run_id": request.workflow_run_id,
                "run_id": request.run_id,
                "metadata": {
                    **record.result.metadata,
                    "idempotent_replay": True,
                },
            }
        )

    def remember(self, request: AgentRunRequest, result: AgentRunResult) -> None:
        if request.idempotency_key is None:
            return
        scope = self._scope(request)
        record = IdempotencyRecord(self._signature(request), result)
        with self._lock:
            current = self._records.get(scope)
            if current is not None and current.signature != record.signature:
                raise IdempotencyConflictError(
                    "idempotency key reused with a different input payload"
                )
            self._records[scope] = record
