from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from pydantic import ValidationError

from factory.onboarding import build_draft_project_spec
from models.control import ServiceCommandRecord, ServiceCommandStatus
from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project, ProjectSpec
from persistence.base import PersistenceConflictError, PersistenceStore
from registry.project_registry import ProjectRegistry
from supervisor.kernel import ProjectNotRunnableError
from supervisor.routing import NoProviderError
from workflows.engine import WorkflowRuntimeError

from .contracts import (
    API_VERSION,
    APPROVALS_DECIDE_SCOPE,
    APPROVALS_READ_SCOPE,
    EXECUTIONS_CANCEL_SCOPE,
    EXECUTIONS_READ_SCOPE,
    EXECUTIONS_START_SCOPE,
    HUMAN_ACTIONS_READ_SCOPE,
    HUMAN_ACTIONS_VERIFY_SCOPE,
    PROJECT_REGISTER_SCOPE,
    PROJECT_SPECS_ACTIVATE_SCOPE,
    PROJECT_SPECS_APPROVE_SCOPE,
    PROJECT_SPECS_READ_SCOPE,
    PROJECT_SPECS_SUBMIT_SCOPE,
    RECOVERY_READ_SCOPE,
    RELEASES_CONFIRM_SCOPE,
    RELEASES_READ_SCOPE,
    ApiResponse,
    ApprovalRevokeRequest,
    ProjectRegistrationRequest,
    ProjectSpecSubmissionRequest,
    ServicePrincipal,
    TaskStartRequest,
    WorkflowStartRequest,
)


class OperatorApiError(RuntimeError):
    def __init__(self, code: str, status_code: int, message: str, category: str | None = None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.category = category or code


class OperatorControlApi:
    """Additive Phase-2 owner/operator routes over authoritative domain services."""

    BASE_PATH = "/api/v1"
    MAX_IDEMPOTENCY_KEY_LENGTH = 256

    def __init__(
        self,
        projects: ProjectRegistry,
        store: PersistenceStore,
        *,
        kernel=None,
        workflows=None,
        human=None,
        approvals=None,
        releases=None,
    ):
        self.projects = projects
        self.store = store
        self.kernel = kernel
        self.workflows = workflows
        self.human = human
        self.approvals = approvals
        self.releases = releases
        self._active_commands: set[str] = set()
        self._active_lock = RLock()

    def dispatch_if_supported(
        self,
        method: str,
        path: str,
        *,
        principal: ServicePrincipal | None,
        body: Any,
        idempotency_key: str | None,
    ) -> ApiResponse | None:
        normalized = path.rstrip("/") or "/"
        method = method.upper()

        if normalized == f"{self.BASE_PATH}/projects" and method == "POST":
            return self._register_project(principal, body, idempotency_key)

        prefix = f"{self.BASE_PATH}/projects/"
        if not normalized.startswith(prefix):
            return None
        remainder = normalized[len(prefix):]
        parts = remainder.split("/")
        if not parts or not parts[0]:
            return None
        project_id = parts[0]

        if len(parts) == 2 and parts[1] == "specs":
            if method == "GET":
                return self._list_specs(project_id, principal)
            if method == "POST":
                return self._submit_spec(project_id, principal, body, idempotency_key)
            return None
        if len(parts) == 4 and parts[1] == "specs":
            spec_id, action = parts[2], parts[3]
            if method != "POST":
                return None
            if action == "approve":
                return self._approve_spec(project_id, spec_id, principal, idempotency_key)
            if action == "reject":
                return self._reject_spec(project_id, spec_id, principal, idempotency_key)
            if action == "activate":
                return self._activate_spec(project_id, spec_id, principal, idempotency_key)
            return None

        if len(parts) == 2 and parts[1] == "human-actions":
            if method == "GET":
                return self._list_human_actions(project_id, principal)
            return None
        if len(parts) == 4 and parts[1] == "human-actions" and method == "POST":
            action_id, operation = parts[2], parts[3]
            if operation == "verify":
                return self._verify_human_action(project_id, action_id, principal, idempotency_key)
            if operation == "cancel":
                return self._cancel_human_action(project_id, action_id, principal, idempotency_key)
            return None

        if len(parts) == 2 and parts[1] == "approvals":
            if method == "GET":
                return self._list_approvals(project_id, principal)
            return None
        if len(parts) == 4 and parts[1] == "approvals" and method == "POST":
            approval_id, operation = parts[2], parts[3]
            if operation == "approve":
                return self._decide_approval(project_id, approval_id, "approve", principal, None, idempotency_key)
            if operation == "reject":
                return self._decide_approval(project_id, approval_id, "reject", principal, None, idempotency_key)
            if operation == "revoke":
                return self._decide_approval(project_id, approval_id, "revoke", principal, body, idempotency_key)
            return None

        if len(parts) == 2 and parts[1] == "tasks":
            if method == "GET":
                return self._list_tasks(project_id, principal)
            if method == "POST":
                return self._start_task(project_id, principal, body, idempotency_key)
            return None
        if len(parts) == 3 and parts[1] == "tasks" and method == "GET":
            return self._get_task(project_id, parts[2], principal)
        if len(parts) == 4 and parts[1] == "tasks" and parts[3] == "cancel" and method == "POST":
            return self._cancel_task(project_id, parts[2], principal, idempotency_key)

        if len(parts) == 2 and parts[1] == "workflows":
            if method == "GET":
                return self._list_workflows(project_id, principal)
            if method == "POST":
                return self._start_workflow(project_id, principal, body, idempotency_key)
            return None
        if len(parts) == 3 and parts[1] == "workflows" and method == "GET":
            return self._get_workflow(project_id, parts[2], principal)
        if len(parts) == 4 and parts[1] == "workflows" and parts[3] == "cancel" and method == "POST":
            return self._cancel_workflow(project_id, parts[2], principal, idempotency_key)

        if len(parts) == 2 and parts[1] == "releases" and method == "GET":
            return self._list_releases(project_id, principal)
        if len(parts) == 3 and parts[1] == "releases" and method == "GET":
            return self._get_release(project_id, parts[2], principal)
        if (
            len(parts) == 6
            and parts[1] == "releases"
            and parts[3] == "targets"
            and parts[5] == "confirm-publication"
            and method == "POST"
        ):
            return self._confirm_publication(
                project_id,
                parts[2],
                parts[4],
                principal,
                idempotency_key,
            )

        if len(parts) == 2 and parts[1] == "recovery-status" and method == "GET":
            return self._recovery_status(project_id, principal)

        return None

    # Project / ProjectSpec -------------------------------------------------

    def _register_project(self, principal, body, idempotency_key):
        self._require_scope(principal, PROJECT_REGISTER_SCOPE)
        request = self._validate(ProjectRegistrationRequest, body)
        key = self._require_key(idempotency_key)
        payload = request.model_dump(mode="json")
        command_id = self._command_id(request.project_id, "project-register", key)
        spec_id = self._derived_id("PSPEC", command_id)
        refs = {"project_id": request.project_id, "project_spec_id": spec_id}

        def mutate(at):
            if self.projects.get(request.project_id) is not None:
                raise OperatorApiError("IDEMPOTENCY_CONFLICT", 409, "project already exists")
            try:
                spec = build_draft_project_spec(
                    request.project_id,
                    request.onboarding,
                    at,
                    project_spec_id=spec_id,
                    spec_version=request.spec_version,
                )
            except (ValidationError, ValueError) as exc:
                raise OperatorApiError("INVALID_REQUEST", 400, "invalid onboarding data") from exc
            project = Project(
                project_id=request.project_id,
                name=spec.name,
                lifecycle_state=ProjectLifecycleState.IDEA,
                operational_state=ProjectOperationalState.ACTIVE,
                created_at=at,
                updated_at=at,
            )
            self.projects.register(project, spec)
            return project

        return self._local_command(
            request.project_id,
            "project-register",
            key,
            payload,
            refs,
            mutate,
            lambda project, replay: self._success(
                {
                    "project": self._project_payload(project),
                    "project_spec": self._spec_payload(self.store.get_project_spec(spec_id)),
                },
                meta={"idempotent_replay": replay},
            ),
        )

    def _list_specs(self, project_id, principal):
        self._require_scope(principal, PROJECT_SPECS_READ_SCOPE)
        self._require_project(project_id)
        return self._success(
            {"project_specs": [self._spec_payload(item) for item in self.store.list_project_specs(project_id)]}
        )

    def _submit_spec(self, project_id, principal, body, idempotency_key):
        self._require_scope(principal, PROJECT_SPECS_SUBMIT_SCOPE)
        self._require_project(project_id)
        request = self._validate(ProjectSpecSubmissionRequest, body)
        key = self._require_key(idempotency_key)
        payload = request.model_dump(mode="json")
        command_id = self._command_id(project_id, "project-spec-submit", key)
        spec_id = self._derived_id("PSPEC", command_id)
        refs = {"project_spec_id": spec_id}

        def mutate(at):
            if any(item.spec_version == request.spec_version for item in self.store.list_project_specs(project_id)):
                raise OperatorApiError("IDEMPOTENCY_CONFLICT", 409, "ProjectSpec version already exists")
            if request.supersedes_spec_id is not None:
                previous = self.store.get_project_spec(request.supersedes_spec_id)
                if previous is None or previous.project_id != project_id:
                    raise OperatorApiError("NOT_FOUND", 404, "superseded ProjectSpec not found")
            try:
                spec = build_draft_project_spec(
                    project_id,
                    request.onboarding,
                    at,
                    project_spec_id=spec_id,
                    spec_version=request.spec_version,
                ).model_copy(update={"supersedes_spec_id": request.supersedes_spec_id})
            except (ValidationError, ValueError) as exc:
                raise OperatorApiError("INVALID_REQUEST", 400, "invalid ProjectSpec submission") from exc
            self.projects.add_spec(spec)
            return spec

        return self._local_command(
            project_id,
            "project-spec-submit",
            key,
            payload,
            refs,
            mutate,
            lambda spec, replay: self._success(
                {"project_spec": self._spec_payload(spec)},
                meta={"idempotent_replay": replay},
            ),
        )

    def _approve_spec(self, project_id, spec_id, principal, idempotency_key):
        self._require_scope(principal, PROJECT_SPECS_APPROVE_SCOPE)
        self._require_project(project_id)
        key = self._require_key(idempotency_key)
        return self._local_command(
            project_id,
            "project-spec-approve",
            key,
            {"project_spec_id": spec_id},
            {"project_spec_id": spec_id},
            lambda at: self._translate_transition(
                lambda: self.projects.approve_spec(project_id, spec_id, at),
                "ProjectSpec approval conflict",
            ),
            lambda spec, replay: self._success(
                {"project_spec": self._spec_payload(spec)},
                meta={"idempotent_replay": replay},
            ),
        )

    def _reject_spec(self, project_id, spec_id, principal, idempotency_key):
        self._require_scope(principal, PROJECT_SPECS_APPROVE_SCOPE)
        self._require_project(project_id)
        key = self._require_key(idempotency_key)
        return self._local_command(
            project_id,
            "project-spec-reject",
            key,
            {"project_spec_id": spec_id},
            {"project_spec_id": spec_id},
            lambda at: self._translate_transition(
                lambda: self.projects.reject_spec(project_id, spec_id, at),
                "ProjectSpec rejection conflict",
            ),
            lambda spec, replay: self._success(
                {"project_spec": self._spec_payload(spec)},
                meta={"idempotent_replay": replay},
            ),
        )

    def _activate_spec(self, project_id, spec_id, principal, idempotency_key):
        self._require_scope(principal, PROJECT_SPECS_ACTIVATE_SCOPE)
        self._require_project(project_id)
        key = self._require_key(idempotency_key)

        def mutate(at):
            spec = self.store.get_project_spec(spec_id)
            if spec is None or spec.project_id != project_id:
                raise OperatorApiError("NOT_FOUND", 404, "ProjectSpec not found")
            try:
                return self.projects.activate_spec(project_id, spec, at)
            except ValueError as exc:
                raise OperatorApiError("INVALID_TRANSITION", 409, "ProjectSpec cannot be activated") from exc

        return self._local_command(
            project_id,
            "project-spec-activate",
            key,
            {"project_spec_id": spec_id},
            {"project_id": project_id, "project_spec_id": spec_id},
            mutate,
            lambda project, replay: self._success(
                {"project": self._project_payload(project)},
                meta={"idempotent_replay": replay},
            ),
        )

    # Human actions / approvals --------------------------------------------

    def _list_human_actions(self, project_id, principal):
        self._require_scope(principal, HUMAN_ACTIONS_READ_SCOPE)
        self._require_project(project_id)
        return self._success(
            {"human_actions": [self._human_action_payload(item) for item in self.store.list_human_actions(project_id)]}
        )

    def _verify_human_action(self, project_id, action_id, principal, idempotency_key):
        self._require_scope(principal, HUMAN_ACTIONS_VERIFY_SCOPE)
        self._require_dependency(self.human, "human intervention")
        self._require_project(project_id)
        key = self._require_key(idempotency_key)

        def mutate(at):
            action = self.store.get_human_action(action_id)
            if action is None or action.project_id != project_id:
                raise OperatorApiError("NOT_FOUND", 404, "human action not found")
            try:
                return self.human.verify(action_id, True, at)
            except ValueError as exc:
                raise OperatorApiError("OWNER_ACTION_INVALID", 409, "human action cannot be verified") from exc

        return self._local_command(
            project_id,
            "human-action-verify",
            key,
            {"human_action_id": action_id},
            {"human_action_id": action_id},
            mutate,
            lambda action, replay: self._success(
                {"human_action": self._human_action_payload(action)},
                meta={"idempotent_replay": replay},
            ),
        )

    def _cancel_human_action(self, project_id, action_id, principal, idempotency_key):
        self._require_scope(principal, HUMAN_ACTIONS_VERIFY_SCOPE)
        self._require_dependency(self.human, "human intervention")
        self._require_project(project_id)
        key = self._require_key(idempotency_key)

        def mutate(at):
            action = self.store.get_human_action(action_id)
            if action is None or action.project_id != project_id:
                raise OperatorApiError("NOT_FOUND", 404, "human action not found")
            try:
                return self.human.cancel(action_id, at)
            except ValueError as exc:
                raise OperatorApiError("OWNER_ACTION_INVALID", 409, "human action cannot be cancelled") from exc

        return self._local_command(
            project_id,
            "human-action-cancel",
            key,
            {"human_action_id": action_id},
            {"human_action_id": action_id},
            mutate,
            lambda action, replay: self._success(
                {"human_action": self._human_action_payload(action)},
                meta={"idempotent_replay": replay},
            ),
        )

    def _list_approvals(self, project_id, principal):
        self._require_scope(principal, APPROVALS_READ_SCOPE)
        self._require_project(project_id)
        return self._success(
            {"approvals": [self._approval_payload(item) for item in self.store.list_approvals(project_id)]}
        )

    def _decide_approval(self, project_id, approval_id, operation, principal, body, idempotency_key):
        self._require_scope(principal, APPROVALS_DECIDE_SCOPE)
        self._require_dependency(self.approvals, "policy approval")
        self._require_project(project_id)
        key = self._require_key(idempotency_key)
        request = self._validate(ApprovalRevokeRequest, body) if operation == "revoke" else None
        payload = {"approval_id": approval_id, "operation": operation}
        if request is not None:
            payload["reason"] = request.reason

        def mutate(at):
            record = self.store.get_approval(approval_id)
            if record is None or record.project_id != project_id:
                raise OperatorApiError("NOT_FOUND", 404, "approval not found")
            try:
                if operation == "approve":
                    return self.approvals.approve(approval_id, at)
                if operation == "reject":
                    return self.approvals.reject(approval_id, at)
                return self.approvals.revoke(approval_id, at, reason=request.reason)
            except ValueError as exc:
                raise OperatorApiError("APPROVAL_STATE_CONFLICT", 409, "approval state conflict") from exc

        return self._local_command(
            project_id,
            f"approval-{operation}",
            key,
            payload,
            {"approval_id": approval_id},
            mutate,
            lambda record, replay: self._success(
                {"approval": self._approval_payload(record)},
                meta={"idempotent_replay": replay},
            ),
        )

    # Execution -------------------------------------------------------------

    def _list_tasks(self, project_id, principal):
        self._require_scope(principal, EXECUTIONS_READ_SCOPE)
        self._require_project(project_id)
        return self._success({"tasks": [self._task_payload(item) for item in self.store.list_tasks(project_id)]})

    def _get_task(self, project_id, task_id, principal):
        self._require_scope(principal, EXECUTIONS_READ_SCOPE)
        self._require_project(project_id)
        task = self.store.get_task(task_id)
        if task is None or task.project_id != project_id:
            raise OperatorApiError("NOT_FOUND", 404, "task not found")
        return self._success({"task": self._task_payload(task)})

    def _start_task(self, project_id, principal, body, idempotency_key):
        self._require_scope(principal, EXECUTIONS_START_SCOPE)
        self._require_dependency(self.kernel, "supervisor kernel")
        self._require_project(project_id)
        request = self._validate(TaskStartRequest, body)
        key = self._require_key(idempotency_key)
        payload = request.model_dump(mode="json")
        command_id = self._command_id(project_id, "task-start", key)
        task_id = self._derived_id("TASK_SERVICE", command_id)
        workflow_run_id = self._derived_id("WF_SERVICE", command_id)
        refs = {"task_id": task_id, "workflow_run_id": workflow_run_id}
        existing, signature = self._begin_long_command(
            project_id, "task-start", key, payload, refs
        )
        if existing is not None:
            replay = self._reconcile_task_command(existing)
            if replay is not None:
                return replay
            self._mark_active(command_id)

        try:
            try:
                self.kernel.run_task(
                    project_id,
                    request.title,
                    request.requirement,
                    request.input,
                    context=request.context,
                    policy=request.policy,
                    limits=request.limits,
                    task_id=task_id,
                    workflow_run_id=workflow_run_id,
                    metadata={"service_command_id": command_id},
                )
            except ProjectNotRunnableError as exc:
                self._fail_command(command_id, "PROJECT_NOT_RUNNABLE", 409, "PROJECT_STATE")
                raise OperatorApiError("PROJECT_NOT_RUNNABLE", 409, "project is not runnable") from exc
            except NoProviderError as exc:
                self._fail_command(command_id, "DEPENDENCY_UNAVAILABLE", 503, "DEPENDENCY")
                raise OperatorApiError("DEPENDENCY_UNAVAILABLE", 503, "execution provider unavailable") from exc
            except (ValidationError, ValueError) as exc:
                self._fail_command(command_id, "INVALID_REQUEST", 400, "VALIDATION")
                raise OperatorApiError("INVALID_REQUEST", 400, "invalid task execution request") from exc
            except Exception as exc:
                self._fail_command(command_id, "INTERNAL_ERROR", 500, "INTERNAL")
                raise OperatorApiError("INTERNAL_ERROR", 500, "internal service error") from exc

            self._succeed_command(command_id)
            task = self.store.get_task(task_id)
            return self._success(
                {"task": self._task_payload(task)},
                meta={"idempotent_replay": False},
            )
        finally:
            self._clear_active(command_id)

    def _cancel_task(self, project_id, task_id, principal, idempotency_key):
        self._require_scope(principal, EXECUTIONS_CANCEL_SCOPE)
        self._require_dependency(self.kernel, "supervisor kernel")
        self._require_project(project_id)
        key = self._require_key(idempotency_key)

        def mutate(at):
            del at
            try:
                return self.kernel.cancel_task(project_id, task_id)
            except KeyError as exc:
                raise OperatorApiError("NOT_FOUND", 404, "task not found") from exc
            except ValueError as exc:
                raise OperatorApiError("EXECUTION_NOT_CANCELLABLE", 409, "task is not cancellable") from exc

        return self._local_command(
            project_id,
            "task-cancel",
            key,
            {"task_id": task_id},
            {"task_id": task_id},
            mutate,
            lambda task, replay: self._success(
                {"task": self._task_payload(task)},
                meta={"idempotent_replay": replay},
            ),
        )

    def _list_workflows(self, project_id, principal):
        self._require_scope(principal, EXECUTIONS_READ_SCOPE)
        self._require_project(project_id)
        return self._success(
            {"workflows": [self._workflow_payload(item) for item in self.store.list_workflow_runs(project_id)]}
        )

    def _get_workflow(self, project_id, workflow_run_id, principal):
        self._require_scope(principal, EXECUTIONS_READ_SCOPE)
        self._require_project(project_id)
        run = self._find_workflow(project_id, workflow_run_id)
        return self._success({"workflow": self._workflow_payload(run)})

    def _start_workflow(self, project_id, principal, body, idempotency_key):
        self._require_scope(principal, EXECUTIONS_START_SCOPE)
        self._require_dependency(self.workflows, "workflow engine")
        self._require_project(project_id)
        request = self._validate(WorkflowStartRequest, body)
        key = self._require_key(idempotency_key)
        payload = request.model_dump(mode="json")
        command_id = self._command_id(project_id, "workflow-start", key)
        task_id = self._derived_id("TASK_WF_SERVICE", command_id)
        workflow_run_id = self._derived_id("WF_SERVICE", command_id)
        refs = {"task_id": task_id, "workflow_run_id": workflow_run_id}
        existing, signature = self._begin_long_command(
            project_id, "workflow-start", key, payload, refs
        )
        del signature
        if existing is not None:
            replay = self._reconcile_workflow_command(existing)
            if replay is not None:
                return replay
            self._mark_active(command_id)

        try:
            try:
                self.workflows.start(
                    project_id,
                    request.title,
                    request.definition,
                    request.input,
                    approvals=request.approvals,
                    task_id=task_id,
                    workflow_run_id=workflow_run_id,
                )
            except ProjectNotRunnableError as exc:
                self._fail_command(command_id, "PROJECT_NOT_RUNNABLE", 409, "PROJECT_STATE")
                raise OperatorApiError("PROJECT_NOT_RUNNABLE", 409, "project is not runnable") from exc
            except (ValidationError, WorkflowRuntimeError, ValueError) as exc:
                self._fail_command(command_id, "INVALID_REQUEST", 400, "VALIDATION")
                raise OperatorApiError("INVALID_REQUEST", 400, "invalid workflow execution request") from exc
            except Exception as exc:
                self._fail_command(command_id, "INTERNAL_ERROR", 500, "INTERNAL")
                raise OperatorApiError("INTERNAL_ERROR", 500, "internal service error") from exc

            self._succeed_command(command_id)
            run = self._find_workflow(project_id, workflow_run_id)
            return self._success(
                {"workflow": self._workflow_payload(run)},
                meta={"idempotent_replay": False},
            )
        finally:
            self._clear_active(command_id)

    def _cancel_workflow(self, project_id, workflow_run_id, principal, idempotency_key):
        self._require_scope(principal, EXECUTIONS_CANCEL_SCOPE)
        self._require_dependency(self.workflows, "workflow engine")
        self._require_project(project_id)
        key = self._require_key(idempotency_key)

        def mutate(at):
            del at
            try:
                self.workflows.cancel(project_id, workflow_run_id)
            except KeyError as exc:
                raise OperatorApiError("NOT_FOUND", 404, "workflow not found") from exc
            except ValueError as exc:
                raise OperatorApiError("EXECUTION_NOT_CANCELLABLE", 409, "workflow is not cancellable") from exc
            return self._find_workflow(project_id, workflow_run_id)

        return self._local_command(
            project_id,
            "workflow-cancel",
            key,
            {"workflow_run_id": workflow_run_id},
            {"workflow_run_id": workflow_run_id},
            mutate,
            lambda run, replay: self._success(
                {"workflow": self._workflow_payload(run)},
                meta={"idempotent_replay": replay},
            ),
        )

    # Release / recovery ----------------------------------------------------

    def _list_releases(self, project_id, principal):
        self._require_scope(principal, RELEASES_READ_SCOPE)
        self._require_project(project_id)
        return self._success(
            {"releases": [self._release_payload(item) for item in self.store.list_releases(project_id)]}
        )

    def _get_release(self, project_id, release_id, principal):
        self._require_scope(principal, RELEASES_READ_SCOPE)
        self._require_project(project_id)
        release = self.store.get_release(release_id)
        if release is None or release.project_id != project_id:
            raise OperatorApiError("NOT_FOUND", 404, "release not found")
        return self._success({"release": self._release_payload(release)})

    def _confirm_publication(self, project_id, release_id, target_type, principal, idempotency_key):
        self._require_scope(principal, RELEASES_CONFIRM_SCOPE)
        self._require_dependency(self.releases, "release manager")
        self._require_project(project_id)
        key = self._require_key(idempotency_key)

        def mutate(at):
            release = self.store.get_release(release_id)
            if release is None or release.project_id != project_id:
                raise OperatorApiError("NOT_FOUND", 404, "release not found")
            targets = [
                item for item in self.store.list_release_targets(project_id)
                if item.release_id == release_id and item.target_type.upper() == target_type.upper()
            ]
            if not targets:
                raise OperatorApiError("NOT_FOUND", 404, "release target not found")
            try:
                self.releases.confirm_publication(release_id, target_type, at)
            except ValueError as exc:
                raise OperatorApiError("RELEASE_STATE_CONFLICT", 409, "release target cannot be confirmed") from exc
            return self.store.get_release(release_id)

        return self._local_command(
            project_id,
            "release-confirm-publication",
            key,
            {"release_id": release_id, "target_type": target_type.upper()},
            {"release_id": release_id, "target_type": target_type.upper()},
            mutate,
            lambda release, replay: self._success(
                {"release": self._release_payload(release)},
                meta={"idempotent_replay": replay},
            ),
        )

    def _recovery_status(self, project_id, principal):
        self._require_scope(principal, RECOVERY_READ_SCOPE)
        snapshot = self.projects.recover(project_id)
        active_spec = snapshot.active_spec
        task_counts: dict[str, int] = {}
        for task in snapshot.tasks:
            task_counts[task.status] = task_counts.get(task.status, 0) + 1
        workflow_counts: dict[str, int] = {}
        for run in snapshot.workflow_runs:
            workflow_counts[run.status] = workflow_counts.get(run.status, 0) + 1
        return self._success(
            {
                "recovery_status": {
                    "project": self._project_payload(snapshot.project),
                    "active_project_spec": None if active_spec is None else self._spec_summary(active_spec),
                    "counts": {
                        "project_specs": len(snapshot.specs),
                        "tasks": len(snapshot.tasks),
                        "workflows": len(snapshot.workflow_runs),
                        "human_actions": len(snapshot.human_actions),
                        "approvals": len(snapshot.approvals),
                        "releases": len(snapshot.releases),
                        "release_targets": len(snapshot.release_targets),
                        "service_commands": len(snapshot.service_commands),
                    },
                    "task_statuses": task_counts,
                    "workflow_statuses": workflow_counts,
                }
            }
        )

    # Command/idempotency ---------------------------------------------------

    def _local_command(
        self,
        project_id: str,
        operation: str,
        key: str,
        request_payload: dict[str, Any],
        result_refs: dict[str, Any],
        mutate: Callable[[datetime], Any],
        render: Callable[[Any, bool], ApiResponse],
    ) -> ApiResponse:
        signature = self._signature(request_payload)
        command_id = self._command_id(project_id, operation, key)
        existing = self.store.get_service_command(command_id)
        if existing is not None:
            self._assert_command_signature(existing, signature)
            if existing.status == ServiceCommandStatus.FAILED:
                self._raise_recorded_failure(existing)
            if existing.status == ServiceCommandStatus.PENDING:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "service command is in progress")
            return render(self._resolve_command_result(existing), True)

        now = datetime.now(timezone.utc)
        pending = ServiceCommandRecord(
            command_id=command_id,
            project_id=project_id,
            api_version=API_VERSION,
            operation=operation,
            idempotency_key=key,
            signature=signature,
            result_refs=result_refs,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.store.transaction():
                concurrent = self.store.get_service_command(command_id)
                if concurrent is not None:
                    self._assert_command_signature(concurrent, signature)
                    if concurrent.status == ServiceCommandStatus.FAILED:
                        self._raise_recorded_failure(concurrent)
                    if concurrent.status == ServiceCommandStatus.PENDING:
                        raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "service command is in progress")
                    return render(self._resolve_command_result(concurrent), True)
                self.store.claim_service_command(pending)
                result = mutate(now)
                completed = pending.model_copy(
                    update={
                        "status": ServiceCommandStatus.SUCCEEDED,
                        "result_kind": self._result_kind(result),
                        "updated_at": now,
                        "completed_at": now,
                    }
                )
                self.store.save_service_command(completed)
        except OperatorApiError as exc:
            self._persist_failed_claim(pending, exc)
            raise
        except PersistenceConflictError as exc:
            raise OperatorApiError("IDEMPOTENCY_CONFLICT", 409, "idempotency key conflict") from exc
        except Exception as exc:
            error = OperatorApiError("INTERNAL_ERROR", 500, "internal service error", "INTERNAL")
            self._persist_failed_claim(pending, error)
            raise error from exc

        return render(result, False)

    def _begin_long_command(self, project_id, operation, key, request_payload, result_refs):
        signature = self._signature(request_payload)
        command_id = self._command_id(project_id, operation, key)
        existing = self.store.get_service_command(command_id)
        if existing is not None:
            self._assert_command_signature(existing, signature)
            if existing.status == ServiceCommandStatus.FAILED:
                self._raise_recorded_failure(existing)
            return existing, signature
        now = datetime.now(timezone.utc)
        pending = ServiceCommandRecord(
            command_id=command_id,
            project_id=project_id,
            api_version=API_VERSION,
            operation=operation,
            idempotency_key=key,
            signature=signature,
            result_refs=result_refs,
            created_at=now,
            updated_at=now,
        )
        try:
            self.store.claim_service_command(pending)
        except PersistenceConflictError:
            existing = self.store.get_service_command(command_id)
            if existing is None:
                raise OperatorApiError("IDEMPOTENCY_CONFLICT", 409, "idempotency key conflict")
            self._assert_command_signature(existing, signature)
            if existing.status == ServiceCommandStatus.FAILED:
                self._raise_recorded_failure(existing)
            return existing, signature
        self._mark_active(command_id)
        return None, signature

    def _reconcile_task_command(self, command):
        if self._is_active(command.command_id):
            raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "task command is in progress")
        task_id = command.result_refs.get("task_id")
        task = self.store.get_task(task_id) if isinstance(task_id, str) else None
        if task is None:
            return None
        if task.status in {"SUCCEEDED", "FAILED", "BLOCKED", "CANCELLED"}:
            self._succeed_command(command.command_id)
            return self._success(
                {"task": self._task_payload(task)},
                meta={"idempotent_replay": True},
            )

        try:
            self.kernel.cancel_task(command.project_id, task.task_id)
        except (KeyError, ValueError):
            pass
        self._fail_command(
            command.command_id,
            "EXECUTION_INTERRUPTED",
            409,
            "RECOVERY",
        )
        raise OperatorApiError(
            "EXECUTION_INTERRUPTED",
            409,
            "previous task execution was interrupted and reconciled",
            "RECOVERY",
        )

    def _reconcile_workflow_command(self, command):
        if self._is_active(command.command_id):
            raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "workflow command is in progress")
        workflow_run_id = command.result_refs.get("workflow_run_id")
        if not isinstance(workflow_run_id, str):
            return None
        try:
            run = self._find_workflow(command.project_id, workflow_run_id)
        except OperatorApiError:
            task_id = command.result_refs.get("task_id")
            task = self.store.get_task(task_id) if isinstance(task_id, str) else None
            if task is None:
                return None
            if task.project_id != command.project_id:
                self._fail_command(
                    command.command_id,
                    "EXECUTION_INTERRUPTED",
                    409,
                    "RECOVERY",
                )
                raise OperatorApiError(
                    "EXECUTION_INTERRUPTED",
                    409,
                    "previous workflow execution was interrupted and reconciled",
                    "RECOVERY",
                )
            if task.status not in {"SUCCEEDED", "FAILED", "BLOCKED", "CANCELLED"}:
                try:
                    self.kernel.cancel_task(command.project_id, task.task_id)
                except (KeyError, ValueError):
                    pass
            self._fail_command(
                command.command_id,
                "EXECUTION_INTERRUPTED",
                409,
                "RECOVERY",
            )
            raise OperatorApiError(
                "EXECUTION_INTERRUPTED",
                409,
                "previous workflow execution was interrupted and reconciled",
                "RECOVERY",
            )
        if run.status != "RUNNING":
            self._succeed_command(command.command_id)
            return self._success(
                {"workflow": self._workflow_payload(run)},
                meta={"idempotent_replay": True},
            )

        try:
            self.workflows.cancel(command.project_id, workflow_run_id)
        except (KeyError, ValueError):
            pass
        self._fail_command(
            command.command_id,
            "EXECUTION_INTERRUPTED",
            409,
            "RECOVERY",
        )
        raise OperatorApiError(
            "EXECUTION_INTERRUPTED",
            409,
            "previous workflow execution was interrupted and reconciled",
            "RECOVERY",
        )

    def _mark_active(self, command_id: str) -> None:
        with self._active_lock:
            self._active_commands.add(command_id)

    def _clear_active(self, command_id: str) -> None:
        with self._active_lock:
            self._active_commands.discard(command_id)

    def _is_active(self, command_id: str) -> bool:
        with self._active_lock:
            return command_id in self._active_commands

    def _succeed_command(self, command_id):
        record = self.store.get_service_command(command_id)
        if record is None:
            raise RuntimeError("service command disappeared")
        if record.status == ServiceCommandStatus.SUCCEEDED:
            return
        now = datetime.now(timezone.utc)
        self.store.save_service_command(
            record.model_copy(
                update={
                    "status": ServiceCommandStatus.SUCCEEDED,
                    "updated_at": now,
                    "completed_at": now,
                    "error_code": None,
                    "error_category": None,
                    "error_status_code": None,
                }
            )
        )

    def _fail_command(self, command_id, code, status_code, category):
        record = self.store.get_service_command(command_id)
        if record is None or record.status != ServiceCommandStatus.PENDING:
            return
        now = datetime.now(timezone.utc)
        self.store.save_service_command(
            record.model_copy(
                update={
                    "status": ServiceCommandStatus.FAILED,
                    "error_code": code,
                    "error_category": category,
                    "error_status_code": status_code,
                    "updated_at": now,
                    "completed_at": now,
                }
            )
        )

    def _persist_failed_claim(self, pending, error):
        if self.store.get_service_command(pending.command_id) is not None:
            return
        now = datetime.now(timezone.utc)
        failed = pending.model_copy(
            update={
                "status": ServiceCommandStatus.FAILED,
                "error_code": error.code,
                "error_category": error.category,
                "error_status_code": error.status_code,
                "updated_at": now,
                "completed_at": now,
            }
        )
        try:
            self.store.claim_service_command(failed)
        except PersistenceConflictError:
            pass

    def _resolve_command_result(self, command):
        refs = command.result_refs
        if command.operation == "project-register":
            project = self.projects.get(command.project_id)
            if project is None:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "registered project is unavailable")
            return project
        if command.operation in {"project-spec-submit", "project-spec-approve", "project-spec-reject"}:
            spec_id = refs.get("project_spec_id")
            spec = self.store.get_project_spec(spec_id) if isinstance(spec_id, str) else None
            if spec is None or spec.project_id != command.project_id:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "ProjectSpec result is unavailable")
            return spec
        if command.operation == "project-spec-activate":
            project = self.projects.get(command.project_id)
            if project is None:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "project result is unavailable")
            return project
        if command.operation.startswith("human-action-"):
            action_id = refs.get("human_action_id")
            action = self.store.get_human_action(action_id) if isinstance(action_id, str) else None
            if action is None or action.project_id != command.project_id:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "human action result is unavailable")
            return action
        if command.operation.startswith("approval-"):
            approval_id = refs.get("approval_id")
            record = self.store.get_approval(approval_id) if isinstance(approval_id, str) else None
            if record is None or record.project_id != command.project_id:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "approval result is unavailable")
            return record
        if command.operation == "task-cancel":
            task_id = refs.get("task_id")
            task = self.store.get_task(task_id) if isinstance(task_id, str) else None
            if task is None or task.project_id != command.project_id:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "task result is unavailable")
            return task
        if command.operation == "workflow-cancel":
            return self._find_workflow(command.project_id, refs.get("workflow_run_id"))
        if command.operation == "release-confirm-publication":
            release_id = refs.get("release_id")
            release = self.store.get_release(release_id) if isinstance(release_id, str) else None
            if release is None or release.project_id != command.project_id:
                raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "release result is unavailable")
            return release
        raise OperatorApiError("COMMAND_IN_PROGRESS", 409, "service command result is unavailable")

    # Projection / validation helpers --------------------------------------

    def _require_project(self, project_id):
        project = self.projects.get(project_id)
        if project is None:
            raise OperatorApiError("NOT_FOUND", 404, "project not found")
        return project

    def _find_workflow(self, project_id, workflow_run_id):
        for run in self.store.list_workflow_runs(project_id):
            if run.workflow_run_id == workflow_run_id:
                return run
        raise OperatorApiError("NOT_FOUND", 404, "workflow not found")

    @staticmethod
    def _project_payload(project):
        return project.model_dump(mode="json")

    @staticmethod
    def _spec_payload(spec):
        if spec is None:
            return None
        return spec.model_dump(mode="json")

    @staticmethod
    def _spec_summary(spec):
        return {
            "project_spec_id": spec.project_spec_id,
            "spec_version": spec.spec_version,
            "status": spec.status.value,
            "approved_at": None if spec.approved_at is None else spec.approved_at.isoformat(),
        }

    @staticmethod
    def _human_action_payload(action):
        return {
            "human_action_id": action.human_action_id,
            "project_id": action.project_id,
            "status": action.status.value,
            "action_type": action.action_type,
            "title": action.title,
            "summary": action.summary,
            "required_action": action.required_action,
            "blocking": action.blocking,
            "created_at": action.created_at.isoformat(),
            "due_at": None if action.due_at is None else action.due_at.isoformat(),
            "resolved_at": None if action.resolved_at is None else action.resolved_at.isoformat(),
            "resume_condition": action.resume_condition,
            "verification_method": action.verification_method,
        }

    @staticmethod
    def _approval_payload(record):
        return {
            "approval_id": record.approval_id,
            "project_id": record.project_id,
            "human_action_id": record.human_action_id,
            "scope_hash": record.scope_hash,
            "status": record.status.value,
            "requested_permissions": record.requested_permissions.model_dump(mode="json"),
            "created_at": record.created_at.isoformat(),
            "decided_at": None if record.decided_at is None else record.decided_at.isoformat(),
            "expires_at": None if record.expires_at is None else record.expires_at.isoformat(),
            "revoked_at": None if record.revoked_at is None else record.revoked_at.isoformat(),
            "revocation_reason": record.revocation_reason,
            "metadata": dict(record.metadata),
        }

    @staticmethod
    def _task_payload(task):
        if task is None:
            return None
        metadata = {
            key: task.metadata[key]
            for key in (
                "capability_id",
                "version_constraint",
                "operation",
                "workflow_id",
                "parent_task_id",
                "parent_workflow_run_id",
                "workflow_node_id",
                "current_run_id",
                "last_run_id",
                "service_command_id",
            )
            if key in task.metadata
        }
        return {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "title": task.title,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "metadata": metadata,
        }

    @staticmethod
    def _workflow_payload(run):
        metadata = {
            key: run.metadata[key]
            for key in (
                "workflow_version",
                "definition_hash",
                "current_node_id",
                "steps",
                "human_action_id",
            )
            if key in run.metadata
        }
        return {
            "workflow_run_id": run.workflow_run_id,
            "project_id": run.project_id,
            "task_id": run.task_id,
            "workflow_id": run.workflow_id,
            "status": run.status,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
            "metadata": metadata,
        }

    def _release_payload(self, release):
        targets = [
            item.model_dump(mode="json")
            for item in self.store.list_release_targets(release.project_id)
            if item.release_id == release.release_id
        ]
        validation = [
            item.model_dump(mode="json")
            for item in self.store.list_release_validation_records(release.project_id)
            if item.release_id == release.release_id
        ]
        return {
            **release.model_dump(mode="json"),
            "release_targets": targets,
            "validation": validation,
        }

    @staticmethod
    def _validate(model, body):
        try:
            return model.model_validate(body)
        except ValidationError as exc:
            raise OperatorApiError("INVALID_REQUEST", 400, "invalid request body") from exc

    @staticmethod
    def _require_scope(principal, scope):
        if principal is None:
            raise OperatorApiError("AUTH_REQUIRED", 401, "authentication required")
        if scope not in principal.scopes:
            raise OperatorApiError("ACCESS_DENIED", 403, "required scope is missing")

    @staticmethod
    def _require_dependency(value, name):
        if value is None:
            raise OperatorApiError("DEPENDENCY_UNAVAILABLE", 503, f"{name} is unavailable")

    def _require_key(self, value):
        if value is None or not value.strip():
            raise OperatorApiError("IDEMPOTENCY_REQUIRED", 400, "Idempotency-Key is required for mutations")
        key = value.strip()
        if len(key) > self.MAX_IDEMPOTENCY_KEY_LENGTH:
            raise OperatorApiError("INVALID_REQUEST", 400, "Idempotency-Key is too long")
        return key

    @staticmethod
    def _signature(payload):
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _command_id(project_id, operation, key):
        raw = f"{API_VERSION}\0{project_id}\0{operation}\0{key}".encode("utf-8")
        return "SERVICE_COMMAND_" + hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _derived_id(prefix, command_id):
        return f"{prefix}_{command_id.rsplit('_', 1)[-1][:32]}"

    @staticmethod
    def _assert_command_signature(record, signature):
        if record.signature != signature:
            raise OperatorApiError(
                "IDEMPOTENCY_CONFLICT",
                409,
                "idempotency key was already used with a different request",
            )

    @staticmethod
    def _raise_recorded_failure(record):
        raise OperatorApiError(
            record.error_code or "INTERNAL_ERROR",
            record.error_status_code or 500,
            "recorded service command failed",
            record.error_category,
        )

    @staticmethod
    def _result_kind(result):
        return type(result).__name__

    @staticmethod
    def _translate_transition(callable_, message):
        try:
            return callable_()
        except KeyError as exc:
            raise OperatorApiError("NOT_FOUND", 404, "ProjectSpec not found") from exc
        except ValueError as exc:
            raise OperatorApiError("INVALID_TRANSITION", 409, message) from exc

    @staticmethod
    def _success(data, *, meta=None):
        body = {"api_version": API_VERSION, "data": data}
        if meta is not None:
            body["meta"] = meta
        return ApiResponse(status_code=200, body=body)
