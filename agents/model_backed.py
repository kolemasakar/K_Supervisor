from __future__ import annotations

from collections.abc import Mapping

from access import AccessReference
from integrations.gateway import SideEffectGateway
from models.agent import AgentError, AgentRunRequest, AgentRunResult
from models.enums import ExecutionStatus
from models.side_effect import SideEffectExecutionStatus
from providers.model_hook import ModelSelectionHook, model_candidates
from runtime.contracts import ExecutionControl


class ModelBackedAgent:
    """Provider-neutral runtime handler that invokes MODEL providers through SideEffectGateway."""

    def __init__(
        self,
        gateway: SideEffectGateway,
        selector: ModelSelectionHook,
        *,
        provider_access_refs: Mapping[str, tuple[AccessReference, ...]] | None = None,
    ) -> None:
        self.gateway = gateway
        self.selector = selector
        self.provider_access_refs = {
            key: tuple(value)
            for key, value in (provider_access_refs or {}).items()
        }

    def __call__(
        self,
        request: AgentRunRequest,
        control: ExecutionControl,
    ) -> AgentRunResult:
        control.check_cancelled()

        prompt = request.input.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            return self._error(
                request,
                ExecutionStatus.FAILED,
                "MODEL_INPUT_INVALID",
                "INVALID_REQUEST",
                "model-backed capability requires non-empty prompt text",
            )

        requirements = request.input.get("model_requirements", {})
        if not isinstance(requirements, dict):
            return self._error(
                request,
                ExecutionStatus.FAILED,
                "MODEL_REQUIREMENTS_INVALID",
                "INVALID_REQUEST",
                "model_requirements must be an object",
            )

        try:
            selected = self.selector.select_model(
                model_candidates(self.gateway.providers),
                requirements,
            )
        except ValueError as exc:
            return self._error(
                request,
                ExecutionStatus.FAILED,
                "MODEL_REQUIREMENTS_INVALID",
                "INVALID_REQUEST",
                str(exc),
            )

        if selected is None:
            return self._error(
                request,
                ExecutionStatus.BLOCKED,
                "MODEL_UNAVAILABLE",
                "DEPENDENCY_UNAVAILABLE",
                "no compatible MODEL provider is available",
                retryable=True,
            )

        provider_id = selected.get("provider_id")
        provider_version = selected.get("provider_version")
        model_id = selected.get("model_id")
        if (
            not isinstance(provider_id, str)
            or not provider_id
            or not isinstance(provider_version, str)
            or not provider_version
            or not isinstance(model_id, str)
            or not model_id
        ):
            return self._error(
                request,
                ExecutionStatus.FAILED,
                "MODEL_SELECTION_INVALID",
                "CONFIGURATION",
                "selected MODEL candidate is missing provider/model identity",
            )

        payload: dict = {"model": model_id, "input": prompt}
        instructions = request.input.get("instructions")
        if instructions is not None:
            if not isinstance(instructions, str):
                return self._error(
                    request,
                    ExecutionStatus.FAILED,
                    "MODEL_INPUT_INVALID",
                    "INVALID_REQUEST",
                    "instructions must be text",
                )
            payload["instructions"] = instructions

        if control.limits.max_tokens is not None:
            if control.limits.max_tokens <= 0:
                return self._error(
                    request,
                    ExecutionStatus.BLOCKED,
                    "MODEL_TOKEN_BUDGET_EXHAUSTED",
                    "LIMIT_EXCEEDED",
                    "model token budget is exhausted",
                )
            payload["max_output_tokens"] = control.limits.max_tokens

        result = self.gateway.execute_provider(
            request,
            provider_id,
            "generate",
            payload,
            access_refs=self.provider_access_refs.get(provider_id, ()),
            idempotency_key=request.idempotency_key,
            version_constraint=provider_version,
        )

        if result.status == SideEffectExecutionStatus.SUCCEEDED:
            usage = result.metadata.get("usage")
            if isinstance(usage, dict):
                output_tokens = usage.get("output_tokens")
                if (
                    isinstance(output_tokens, int)
                    and not isinstance(output_tokens, bool)
                    and output_tokens >= 0
                ):
                    control.consume("tokens", output_tokens)
            return AgentRunResult(
                request_id=request.request_id,
                project_id=request.project_id,
                task_id=request.task_id,
                workflow_run_id=request.workflow_run_id,
                run_id=request.run_id,
                agent_id=request.agent_id,
                capability_id=request.capability_id,
                capability_version=request.capability_version,
                status=ExecutionStatus.SUCCEEDED,
                output=dict(result.output),
                metadata={
                    "model_execution": {
                        "execution_id": result.execution_id,
                        "provider_id": provider_id,
                        "provider_version": provider_version,
                        "model_id": model_id,
                        "policy_decision_id": result.policy_decision_id,
                        **dict(result.metadata),
                    }
                },
            )

        status = (
            ExecutionStatus.BLOCKED
            if result.status == SideEffectExecutionStatus.BLOCKED
            else ExecutionStatus.FAILED
        )
        details = {
            "execution_id": result.execution_id,
            "provider_id": provider_id,
            "provider_version": provider_version,
            "model_id": model_id,
            "policy_decision_id": result.policy_decision_id,
        }
        provider_code = result.metadata.get("provider_code")
        if isinstance(provider_code, str):
            details["provider_code"] = provider_code
        return self._error(
            request,
            status,
            result.error_code or "MODEL_EXECUTION_FAILED",
            str(result.metadata.get("error_category") or "PROVIDER_FAILURE"),
            result.error_message or "MODEL provider execution failed",
            retryable=bool(result.metadata.get("retryable", False)),
            details=details,
        )

    @staticmethod
    def _error(
        request: AgentRunRequest,
        status: ExecutionStatus,
        code: str,
        category: str,
        message: str,
        *,
        retryable: bool = False,
        details: dict | None = None,
    ) -> AgentRunResult:
        return AgentRunResult(
            request_id=request.request_id,
            project_id=request.project_id,
            task_id=request.task_id,
            workflow_run_id=request.workflow_run_id,
            run_id=request.run_id,
            agent_id=request.agent_id,
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            status=status,
            error=AgentError(
                code=code,
                category=category,
                message=message,
                retryable=retryable,
                details=details or {},
            ),
        )
