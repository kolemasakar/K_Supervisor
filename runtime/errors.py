from __future__ import annotations

from models.enums import ExecutionStatus


class AgentRuntimeError(RuntimeError):
    code = "RUNTIME_ERROR"
    category = "EXECUTION_ERROR"
    retryable = False
    status = ExecutionStatus.FAILED


class RuntimeDependencyUnavailable(AgentRuntimeError):
    code = "RUNTIME_DEPENDENCY_UNAVAILABLE"
    category = "DEPENDENCY_UNAVAILABLE"
    retryable = True


class RuntimeProviderError(AgentRuntimeError):
    code = "RUNTIME_PROVIDER_ERROR"
    category = "PROVIDER_ERROR"
    retryable = True


class RuntimeToolError(AgentRuntimeError):
    code = "RUNTIME_TOOL_ERROR"
    category = "TOOL_ERROR"


class RuntimeTimeout(AgentRuntimeError):
    code = "RUNTIME_TIMEOUT"
    category = "TIMEOUT"
    retryable = True
    status = ExecutionStatus.TIMED_OUT


class RuntimeCancelled(AgentRuntimeError):
    code = "RUNTIME_CANCELLED"
    category = "CANCELLED"
    status = ExecutionStatus.CANCELLED


class RuntimeLimitExceeded(AgentRuntimeError):
    code = "RUNTIME_LIMIT_EXCEEDED"
    category = "POLICY_BLOCKED"
    status = ExecutionStatus.BLOCKED


class RuntimeValidationError(AgentRuntimeError):
    code = "RUNTIME_VALIDATION_ERROR"
    category = "VALIDATION_ERROR"


class IdempotencyConflictError(RuntimeValidationError):
    code = "RUNTIME_IDEMPOTENCY_CONFLICT"


class RuntimeWorkerCrashed(AgentRuntimeError):
    code = "RUNTIME_WORKER_CRASH"
    category = "WORKER_CRASH"
    retryable = True


class RuntimeWorkerTerminationError(AgentRuntimeError):
    code = "RUNTIME_WORKER_TERMINATION_ERROR"
    category = "TERMINATION_ERROR"


class RuntimeWorkerReportedError(AgentRuntimeError):
    def __init__(self, message: str, *, code: str, category: str, retryable: bool, status: ExecutionStatus):
        super().__init__(message)
        self.code = code
        self.category = category
        self.retryable = retryable
        self.status = status
