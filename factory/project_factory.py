from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.base import ensure_tz
from models.enums import ProjectLifecycleState, ProjectOperationalState, ProjectSpecStatus
from models.intervention import HumanActionRequest
from registry.project_registry import ProjectRegistry
from supervisor.human_intervention import HumanInterventionBroker

from .contracts import BootstrapResult, RepositoryOperationContext, RepositoryTarget
from .errors import (
    BootstrapBlockedError,
    BootstrapValidationError,
    RepositoryGovernanceBlockedError,
    RepositoryUnavailableError,
)
from .repository import RepositoryAdapter
from .templates import generate_bootstrap_files
from .validator import validate_bootstrap


class ProjectFactory:
    def __init__(
        self,
        registry: ProjectRegistry,
        adapters: tuple[RepositoryAdapter, ...],
        human_intervention: HumanInterventionBroker | None = None,
    ):
        self.registry = registry
        self.adapters = {adapter.provider.upper(): adapter for adapter in adapters}
        self.human_intervention = human_intervention

    def bootstrap(self, project_id: str, at: datetime) -> BootstrapResult:
        at = ensure_tz(at)
        project = self.registry.get(project_id)
        if project is None:
            raise KeyError(project_id)
        if project.operational_state != ProjectOperationalState.ACTIVE:
            raise BootstrapBlockedError("project is not operationally ACTIVE")
        if project.lifecycle_state not in {
            ProjectLifecycleState.APPROVED,
            ProjectLifecycleState.PROVISIONING,
            ProjectLifecycleState.BOOTSTRAPPED,
        }:
            raise BootstrapValidationError("project must be APPROVED, PROVISIONING or BOOTSTRAPPED")

        snapshot = self.registry.recover(project_id)
        spec = snapshot.active_spec
        if spec is None or spec.status != ProjectSpecStatus.APPROVED:
            raise BootstrapValidationError("active APPROVED ProjectSpec is required")

        if project.lifecycle_state == ProjectLifecycleState.APPROVED:
            project = self.registry.transition_lifecycle(
                project_id,
                ProjectLifecycleState.PROVISIONING,
                "project factory bootstrap started",
                "project_factory",
                at,
            )

        target = RepositoryTarget.from_spec(spec)
        context = RepositoryOperationContext(
            project_id=project_id,
            project_spec_id=spec.project_spec_id,
            idempotency_key=f"project-factory:{spec.project_spec_id}:bootstrap",
        )
        adapter = self.adapters.get(target.provider)
        if adapter is None:
            self._block_for_repository(project_id, target, at, "repository provider adapter is unavailable")

        try:
            repository = (
                adapter.prepare(target, context=context)
                if getattr(adapter, "supports_operation_context", False)
                else adapter.prepare(target)
            )
        except RepositoryGovernanceBlockedError as exc:
            if exc.human_action_id is not None:
                raise BootstrapBlockedError(str(exc), exc.human_action_id) from exc
            self._block_for_repository(project_id, target, at, str(exc))
        except RepositoryUnavailableError as exc:
            if target.provisioning != "AUTOMATABLE":
                self._block_for_repository(project_id, target, at, str(exc))
            raise

        files = generate_bootstrap_files(spec, target)
        validate_bootstrap(spec, target, files)
        try:
            if getattr(adapter, "supports_operation_context", False):
                adapter.apply_files(repository, files, context=context)
            else:
                adapter.apply_files(repository, files)
        except RepositoryGovernanceBlockedError as exc:
            if exc.human_action_id is not None:
                raise BootstrapBlockedError(str(exc), exc.human_action_id) from exc
            self._block_for_repository(project_id, target, at, str(exc))

        expected = {item.path for item in files}
        actual = set(
            adapter.list_files(repository, context=context)
            if getattr(adapter, "supports_operation_context", False)
            else adapter.list_files(repository)
        )
        missing = sorted(expected.difference(actual))
        if missing:
            raise BootstrapValidationError(f"repository is missing generated files: {', '.join(missing)}")

        current = self.registry.get(project_id)
        if current is None:
            raise KeyError(project_id)
        updated = current.model_copy(update={"current_roadmap_phase": "Phase 0", "updated_at": at})
        self.registry.store.save_project(updated)
        if current.lifecycle_state != ProjectLifecycleState.BOOTSTRAPPED:
            self.registry.transition_lifecycle(
                project_id,
                ProjectLifecycleState.BOOTSTRAPPED,
                "repository bootstrap validated",
                "project_factory",
                at,
            )

        return BootstrapResult(
            project_id=project_id,
            project_spec_id=spec.project_spec_id,
            repository=repository,
            files=tuple(sorted(actual)),
        )

    def _block_for_repository(
        self,
        project_id: str,
        target: RepositoryTarget,
        at: datetime,
        reason: str,
    ) -> None:
        action_id = None
        if self.human_intervention is not None:
            action = HumanActionRequest(
                human_action_id=f"HA_{uuid4().hex}",
                project_id=project_id,
                action_type="REPOSITORY_PROVISIONING",
                title="Repository action required",
                summary=reason,
                required_action=(
                    f"Prepare or authorize the {target.provider} repository '{target.name}' "
                    "and make the configured repository adapter available."
                ),
                blocking=True,
                created_at=at,
                resume_condition="repository can be resolved through the configured adapter",
                verification_method="repository adapter availability check",
            )
            saved = self.human_intervention.open(action)
            action_id = saved.human_action_id
        raise BootstrapBlockedError(reason, action_id)
