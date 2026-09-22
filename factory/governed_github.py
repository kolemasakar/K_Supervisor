from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from access import AccessReference
from integrations.gateway import SideEffectGateway
from models.agent import AgentRunRequest
from models.side_effect import SideEffectExecutionStatus
from policy.approval import PolicyApprovalBroker
from policy.contracts import PolicyEffect, SideEffect

from .contracts import BootstrapFile, ManagedRepository, RepositoryOperationContext, RepositoryTarget
from .errors import (
    RepositoryGovernanceBlockedError,
    RepositoryUnavailableError,
)


class GovernedGitHubRepositoryAdapter:
    """ProjectFactory adapter that routes every GitHub operation through SideEffectGateway."""

    provider = "GITHUB"
    provider_id = "github.repository"

    def __init__(
        self,
        gateway: SideEffectGateway,
        approval_broker: PolicyApprovalBroker | None = None,
    ) -> None:
        self.gateway = gateway
        self.approval_broker = approval_broker
        self._targets: dict[str, RepositoryTarget] = {}

    def prepare(
        self,
        target: RepositoryTarget,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> ManagedRepository:
        context = self._require_context(context)
        credential = self._require_credential(target)
        operation = "create_repository" if target.provisioning == "AUTOMATABLE" else "resolve_repository"
        result = self._execute(
            context,
            operation,
            self._target_payload(target),
            credential,
            side_effects=(
                SideEffect.READ_EXTERNAL,
                SideEffect.CREATE_RESOURCE,
            ) if operation == "create_repository" else (SideEffect.READ_EXTERNAL,),
            key_suffix="prepare",
        )
        repository = ManagedRepository(
            provider="GITHUB",
            repository_id=str(result.output["repository_id"]),
            locator=str(result.output["locator"]),
            default_branch=str(result.output["default_branch"]),
            created=bool(result.output.get("created", False)),
        )
        self._targets[repository.repository_id] = target
        return repository

    def apply_files(
        self,
        repository: ManagedRepository,
        files: tuple[BootstrapFile, ...],
        *,
        context: RepositoryOperationContext | None = None,
    ) -> None:
        context = self._require_context(context)
        target = self._target_for(repository)
        credential = self._require_credential(target)
        payload = self._target_payload(target)
        payload["files"] = [{"path": item.path, "content": item.content} for item in files]
        payload["commit_message"] = "K_Supervisor governed bootstrap"
        self._execute(
            context,
            "bootstrap_files",
            payload,
            credential,
            side_effects=(
                SideEffect.READ_EXTERNAL,
                SideEffect.WRITE_EXTERNAL,
                SideEffect.MODIFY_RESOURCE,
            ),
            key_suffix="bootstrap-files",
        )

    def list_files(
        self,
        repository: ManagedRepository,
        *,
        context: RepositoryOperationContext | None = None,
    ) -> tuple[str, ...]:
        context = self._require_context(context)
        target = self._target_for(repository)
        credential = self._require_credential(target)
        result = self._execute(
            context,
            "list_files",
            self._target_payload(target),
            credential,
            side_effects=(SideEffect.READ_EXTERNAL,),
            key_suffix="list-files",
        )
        files = result.output.get("files")
        if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
            raise RepositoryUnavailableError("GitHub repository file listing was invalid")
        return tuple(sorted(files))

    def _execute(
        self,
        context: RepositoryOperationContext,
        provider_operation: str,
        payload: dict,
        credential: AccessReference,
        *,
        side_effects: tuple[SideEffect, ...],
        key_suffix: str,
    ):
        request = AgentRunRequest(
            request_id=f"REQ_REPO_{uuid4().hex}",
            project_id=context.project_id,
            task_id=f"TASK_REPO_{context.project_spec_id}",
            workflow_run_id=f"WF_REPO_{context.project_spec_id}",
            run_id=f"RUN_REPO_{uuid4().hex}",
            agent_id="system.repository.github",
            capability_id="repository.github",
            capability_version="1.0.0",
            operation=provider_operation,
            input={},
            policy={
                "side_effects": [item.value for item in side_effects],
                "access_refs": [credential.uri],
            },
            idempotency_key=f"{context.idempotency_key}:{key_suffix}",
        )
        approval = None
        decision = self.gateway.policy.evaluate(request)
        if decision.effect == PolicyEffect.REQUIRE_APPROVAL and self.approval_broker is not None:
            approval = self.approval_broker.request(request, datetime.now(timezone.utc))
            request = request.model_copy(
                update={
                    "policy": {
                        **request.policy,
                        "approval_id": approval.approval_id,
                    }
                }
            )

        result = self.gateway.execute_provider(
            request,
            self.provider_id,
            provider_operation,
            payload,
            access_refs=(credential,),
            idempotency_key=request.idempotency_key,
        )
        if result.status == SideEffectExecutionStatus.SUCCEEDED:
            return result
        category = str(result.metadata.get("error_category") or "").upper()
        message = result.error_message or "GitHub repository operation failed"
        if result.status == SideEffectExecutionStatus.BLOCKED:
            raise RepositoryGovernanceBlockedError(
                message,
                None if approval is None else approval.human_action_id,
            )
        if category in {
            "AUTHENTICATION",
            "PERMISSION",
            "CONFLICT",
            "VALIDATION",
            "CONFIGURATION",
        }:
            raise RepositoryGovernanceBlockedError(message)
        raise RepositoryUnavailableError(message)

    @staticmethod
    def _target_payload(target: RepositoryTarget) -> dict:
        return {
            "owner": target.owner,
            "name": target.name,
            "visibility": target.visibility,
            "default_branch": target.default_branch,
            "ci_required": target.ci_required,
            "provisioning": target.provisioning,
        }

    @staticmethod
    def _require_context(context: RepositoryOperationContext | None) -> RepositoryOperationContext:
        if context is None:
            raise RepositoryUnavailableError("governed GitHub repository operation requires project context")
        return context

    @staticmethod
    def _require_credential(target: RepositoryTarget) -> AccessReference:
        if target.credential_ref is None:
            raise RepositoryGovernanceBlockedError("GitHub repository credential reference is required")
        return target.credential_ref

    def _target_for(self, repository: ManagedRepository) -> RepositoryTarget:
        target = self._targets.get(repository.repository_id)
        if target is None:
            raise RepositoryUnavailableError("GitHub repository target context is unavailable")
        return target


def build_governed_github_repository_adapter(
    store,
    projects,
    human,
    secret_backend,
) -> GovernedGitHubRepositoryAdapter:
    """Build an isolated repository-governance stack without polluting runtime agent routing."""

    from models.agent import AgentDescriptor, CapabilityRef
    from models.capability import CapabilityDescriptor
    from policy.approval import PolicyApprovalBroker
    from policy.engine import PolicyEngine
    from providers import GitHubRepositoryProvider
    from registry import AgentRegistry, CapabilityRegistry, ProviderRegistry

    from .github import GitHubRestClient

    capabilities = CapabilityRegistry()
    capability = CapabilityDescriptor(
        capability_id="repository.github",
        capability_version="1.0.0",
        description="Governed GitHub repository and VCS operations.",
        operations=GitHubRepositoryProvider.OPERATIONS,
        input_schema="schema://internal/repository/github/input",
        output_schema="schema://internal/repository/github/output",
        side_effects=(
            SideEffect.READ_EXTERNAL.value,
            SideEffect.WRITE_EXTERNAL.value,
            SideEffect.CREATE_RESOURCE.value,
            SideEffect.MODIFY_RESOURCE.value,
        ),
        risk_class="HIGH",
    )
    capabilities.register(capability)

    agents = AgentRegistry(capabilities)
    agents.register(
        AgentDescriptor(
            agent_id="system.repository.github",
            agent_type="SYSTEM",
            agent_version="1.0.0",
            display_name="Governed GitHub Repository",
            capabilities=(
                CapabilityRef(
                    capability_id=capability.capability_id,
                    capability_version=capability.capability_version,
                ),
            ),
            status="AVAILABLE",
        )
    )

    approval_broker = PolicyApprovalBroker(store, agents, human)
    policy = PolicyEngine(
        projects,
        agents,
        approvals=approval_broker,
    )
    providers = ProviderRegistry()
    providers.register(
        GitHubRepositoryProvider(
            GitHubRestClient(secret_backend)
        )
    )
    gateway = SideEffectGateway(
        store,
        policy,
        providers=providers,
    )
    return GovernedGitHubRepositoryAdapter(
        gateway,
        approval_broker=approval_broker,
    )
