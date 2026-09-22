from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from integrations.gateway import SideEffectGateway
from models.agent import AgentDescriptor, AgentRunRequest, CapabilityRef
from models.capability import CapabilityDescriptor
from models.side_effect import SideEffectExecutionStatus
from policy.approval import PolicyApprovalBroker
from policy.contracts import ApprovalStatus, PolicyEffect
from policy.engine import PolicyEngine
from registry.agent_registry import AgentRegistry

from .contracts import BootstrapFile, ManagedRepository, RepositoryTarget
from .errors import BootstrapBlockedError, RepositoryConflictError, RepositoryUnavailableError


REPOSITORY_CAPABILITY_ID = "repository.github"
REPOSITORY_CAPABILITY_VERSION = "1.0.0"
REPOSITORY_AGENT_ID = "agent.repository.github"


def register_github_repository_governance(agents: AgentRegistry) -> None:
    capability = CapabilityDescriptor(
        capability_id=REPOSITORY_CAPABILITY_ID,
        capability_version=REPOSITORY_CAPABILITY_VERSION,
        description="Governed GitHub repository and VCS side effects.",
        operations=(
            "resolve_repository",
            "create_repository",
            "bootstrap_files",
            "handoff_pull_request",
            "create_tag",
        ),
        input_schema="schema://repository/github/input",
        output_schema="schema://repository/github/output",
        side_effects=(
            "READ_EXTERNAL",
            "WRITE_EXTERNAL",
            "CREATE_RESOURCE",
            "MODIFY_RESOURCE",
        ),
        risk_class="MEDIUM",
    )
    agents.capabilities.register(capability)
    agents.register(
        AgentDescriptor(
            agent_id=REPOSITORY_AGENT_ID,
            agent_type="SYSTEM",
            agent_version="1.0.0",
            display_name="GitHub Repository Governance",
            capabilities=(
                CapabilityRef(
                    capability_id=REPOSITORY_CAPABILITY_ID,
                    capability_version=REPOSITORY_CAPABILITY_VERSION,
                ),
            ),
            status="AVAILABLE",
        )
    )


class GovernedGitHubRepositoryAdapter:
    """RepositoryAdapter-compatible GitHub bootstrap through SideEffectGateway."""

    provider = "GITHUB"

    def __init__(
        self,
        gateway: SideEffectGateway,
        policy: PolicyEngine,
        approvals: PolicyApprovalBroker,
    ) -> None:
        self.gateway = gateway
        self.policy = policy
        self.approvals = approvals
        self._targets: dict[str, RepositoryTarget] = {}
        self._files: dict[str, tuple[str, ...]] = {}

    def prepare(self, target: RepositoryTarget) -> ManagedRepository:
        self._validate_target(target)
        if target.provisioning != "AUTOMATABLE":
            raise RepositoryUnavailableError("GitHub repository provisioning requires owner action")
        result = self._execute(
            target,
            "create_repository",
            self._target_payload(target),
            side_effects=("READ_EXTERNAL", "CREATE_RESOURCE"),
            idempotency_key=self._key(target, "prepare"),
            resume_pending=True,
        )
        repository = ManagedRepository(
            provider="GITHUB",
            repository_id=str(result["repository_id"]),
            locator=str(result["locator"]),
            default_branch=str(result["default_branch"]),
            created=bool(result.get("created", False)),
        )
        self._targets[repository.repository_id] = target
        return repository

    def apply_files(
        self,
        repository: ManagedRepository,
        files: tuple[BootstrapFile, ...],
    ) -> None:
        target = self._target_for(repository)
        payload = {
            **self._target_payload(target),
            "files": [
                {"path": item.path, "content": item.content}
                for item in files
            ],
            "commit_message": "Bootstrap repository from approved ProjectSpec",
        }
        result = self._execute(
            target,
            "bootstrap_files",
            payload,
            side_effects=("READ_EXTERNAL", "WRITE_EXTERNAL", "MODIFY_RESOURCE"),
            idempotency_key=self._key(target, "bootstrap_files"),
            resume_pending=True,
        )
        listed = result.get("files")
        if not isinstance(listed, list) or any(not isinstance(item, str) for item in listed):
            raise RepositoryUnavailableError("GitHub bootstrap result did not include a safe file list")
        self._files[repository.repository_id] = tuple(sorted(listed))

    def list_files(self, repository: ManagedRepository) -> tuple[str, ...]:
        files = self._files.get(repository.repository_id)
        if files is None:
            raise RepositoryUnavailableError("GitHub repository files are not available before governed bootstrap")
        return files

    def handoff_pull_request(
        self,
        repository: ManagedRepository,
        files: tuple[BootstrapFile, ...],
        *,
        title: str,
        body: str = "",
        idempotency_key: str,
    ) -> dict:
        target = self._target_for(repository)
        payload = {
            **self._target_payload(target),
            "files": [{"path": item.path, "content": item.content} for item in files],
            "commit_message": title,
            "pull_request_title": title,
            "pull_request_body": body,
        }
        return self._execute(
            target,
            "handoff_pull_request",
            payload,
            side_effects=(
                "READ_EXTERNAL",
                "WRITE_EXTERNAL",
                "CREATE_RESOURCE",
                "MODIFY_RESOURCE",
            ),
            idempotency_key=idempotency_key,
            resume_pending=True,
        )

    def create_tag(
        self,
        repository: ManagedRepository,
        *,
        tag: str,
        commit_sha: str,
        idempotency_key: str,
    ) -> dict:
        target = self._target_for(repository)
        return self._execute(
            target,
            "create_tag",
            {
                **self._target_payload(target),
                "tag": tag,
                "commit_sha": commit_sha,
            },
            side_effects=("READ_EXTERNAL", "CREATE_RESOURCE"),
            idempotency_key=idempotency_key,
            resume_pending=True,
        )

    def _execute(
        self,
        target: RepositoryTarget,
        operation: str,
        payload: dict,
        *,
        side_effects: tuple[str, ...],
        idempotency_key: str,
        resume_pending: bool,
    ) -> dict:
        request = self._request(
            target,
            operation,
            side_effects=side_effects,
            idempotency_key=idempotency_key,
        )
        decision = self.policy.evaluate(request)
        if decision.effect == PolicyEffect.REQUIRE_APPROVAL:
            approval = self.approvals.request(request, datetime.now(timezone.utc))
            if approval.status != ApprovalStatus.APPROVED:
                raise BootstrapBlockedError(
                    "repository operation requires explicit policy approval",
                    approval.human_action_id,
                )
            request = request.model_copy(
                update={
                    "policy": {
                        **request.policy,
                        "approval_id": approval.approval_id,
                    }
                }
            )
        elif decision.effect != PolicyEffect.ALLOW:
            raise RepositoryUnavailableError(
                f"repository policy denied operation: {decision.reason_code}"
            )

        assert target.credential_ref is not None
        result = self.gateway.execute_provider(
            request,
            "github.repository",
            operation,
            payload,
            access_refs=(target.credential_ref,),
            idempotency_key=idempotency_key,
            resume_pending=resume_pending,
        )
        if result.status == SideEffectExecutionStatus.SUCCEEDED:
            return dict(result.output)
        if result.status == SideEffectExecutionStatus.BLOCKED:
            if result.error_code == "SIDE_EFFECT_IDEMPOTENCY_CONFLICT":
                raise RepositoryConflictError(result.error_message or "repository idempotency conflict")
            raise RepositoryUnavailableError(result.error_message or "repository operation was blocked")
        raise RepositoryUnavailableError(result.error_message or "repository operation failed")

    def _request(
        self,
        target: RepositoryTarget,
        operation: str,
        *,
        side_effects: tuple[str, ...],
        idempotency_key: str,
    ) -> AgentRunRequest:
        assert target.project_id is not None
        digest = hashlib.sha256(
            f"{target.project_id}|{target.project_spec_id}|{operation}|{idempotency_key}".encode("utf-8")
        ).hexdigest()[:24]
        assert target.credential_ref is not None
        return AgentRunRequest(
            request_id=f"REQ_REPOSITORY_{digest}",
            project_id=target.project_id,
            task_id=f"TASK_REPOSITORY_{digest}",
            workflow_run_id=f"WF_REPOSITORY_{digest}",
            run_id=f"RUN_REPOSITORY_{digest}",
            agent_id=REPOSITORY_AGENT_ID,
            capability_id=REPOSITORY_CAPABILITY_ID,
            capability_version=REPOSITORY_CAPABILITY_VERSION,
            operation=operation,
            input={},
            policy={
                "side_effects": list(side_effects),
                "access_refs": [target.credential_ref.uri],
            },
            idempotency_key=idempotency_key,
        )

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
    def _key(target: RepositoryTarget, operation: str) -> str:
        if target.project_spec_id is None:
            raise RepositoryUnavailableError("repository target is missing ProjectSpec correlation")
        return f"{target.project_spec_id}:{operation}"

    @staticmethod
    def _validate_target(target: RepositoryTarget) -> None:
        if target.provider != "GITHUB":
            raise ValueError("governed GitHub adapter requires a GITHUB target")
        if target.project_id is None or target.project_spec_id is None:
            raise RepositoryUnavailableError("GitHub target is missing project correlation")
        if target.owner is None:
            raise RepositoryUnavailableError("GitHub target requires explicit repository owner")
        if target.credential_ref is None:
            raise RepositoryUnavailableError("GitHub target requires protected credential reference")

    def _target_for(self, repository: ManagedRepository) -> RepositoryTarget:
        target = self._targets.get(repository.repository_id)
        if target is None:
            raise RepositoryUnavailableError("GitHub repository correlation is unavailable")
        return target
