from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Condition, Thread
from time import monotonic
from typing import Any

from models.enums import ProjectOperationalState
from registry.project_registry import ProjectRegistry

from .contracts import ProjectSchedulePolicy, SchedulerJob, SchedulerLimits, SchedulerSnapshot
from .errors import DuplicateWorkError, ProjectBudgetExceeded, SchedulerClosedError


@dataclass
class _PendingWork:
    sequence: int
    job: SchedulerJob
    future: Future[Any]


class ProjectScheduler:
    def __init__(self, projects: ProjectRegistry, limits: SchedulerLimits | None = None):
        self.projects = projects
        self.limits = limits or SchedulerLimits()
        self._policies: dict[str, ProjectSchedulePolicy] = {}
        self._project_states: dict[str, ProjectOperationalState] = {}
        self._pending: list[_PendingWork] = []
        self._work_ids: set[str] = set()
        self._running_by_project: dict[str, int] = {}
        self._provider_running: dict[str, int] = {}
        self._held_resources: set[str] = set()
        self._budget_used: dict[str, float] = {}
        self._running_global = 0
        self._sequence = 0
        self._closed = False
        self._condition = Condition()
        self._executor = ThreadPoolExecutor(max_workers=self.limits.global_max_concurrency)
        self._dispatcher = Thread(target=self._dispatch_loop, name="project-scheduler", daemon=True)
        self._dispatcher.start()

    def register_project(
        self,
        project_id: str,
        policy: ProjectSchedulePolicy | None = None,
    ) -> ProjectSchedulePolicy:
        project = self.projects.get(project_id)
        if project is None:
            raise KeyError(project_id)
        if policy is None:
            recovered = self.projects.recover(project_id)
            policy = (
                ProjectSchedulePolicy.from_spec(recovered.active_spec)
                if recovered.active_spec is not None
                else ProjectSchedulePolicy()
            )
        with self._condition:
            self._policies[project_id] = policy
            self._project_states[project_id] = project.operational_state
            self._budget_used.setdefault(project_id, 0.0)
            self._condition.notify_all()
        return policy

    def submit(self, job: SchedulerJob) -> Future[Any]:
        if self.projects.get(job.project_id) is None:
            raise KeyError(job.project_id)
        with self._condition:
            if self._closed:
                raise SchedulerClosedError("scheduler is closed")
            if job.work_id in self._work_ids:
                raise DuplicateWorkError(f"work_id already submitted: {job.work_id}")
            policy = self._policies.get(job.project_id)
            if policy is None:
                raise KeyError(f"project is not registered with scheduler: {job.project_id}")
            used = self._budget_used.get(job.project_id, 0.0)
            projected = used + float(job.estimated_cost)
            if policy.budget_limit is not None and projected > policy.budget_limit:
                raise ProjectBudgetExceeded(
                    f"project budget exceeded: {job.project_id} ({projected} > {policy.budget_limit})"
                )
            self._budget_used[job.project_id] = projected
            self._work_ids.add(job.work_id)
            self._sequence += 1
            future: Future[Any] = Future()
            self._pending.append(_PendingWork(self._sequence, job, future))
            self._condition.notify_all()
            return future

    def notify_state_changed(self, project_id: str | None = None) -> None:
        with self._condition:
            project_ids = (
                (project_id,)
                if project_id is not None
                else tuple(self._policies)
            )
        states: dict[str, ProjectOperationalState] = {}
        for current_id in project_ids:
            project = self.projects.get(current_id)
            if project is None:
                raise KeyError(current_id)
            states[current_id] = project.operational_state
        with self._condition:
            self._project_states.update(states)
            self._condition.notify_all()

    def snapshot(self) -> SchedulerSnapshot:
        with self._condition:
            return SchedulerSnapshot(
                pending=len(self._pending),
                running_global=self._running_global,
                running_by_project=dict(self._running_by_project),
                provider_running=dict(self._provider_running),
                held_resources=tuple(sorted(self._held_resources)),
                budget_used=dict(self._budget_used),
            )

    def wait_for_idle(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else monotonic() + timeout
        with self._condition:
            while self._pending or self._running_global:
                if deadline is None:
                    self._condition.wait()
                    continue
                remaining = deadline - monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(remaining)
            return True

    def shutdown(self, *, wait: bool = True, cancel_pending: bool = True) -> None:
        with self._condition:
            self._closed = True
            if cancel_pending:
                for item in self._pending:
                    if item.future.cancel():
                        self._budget_used[item.job.project_id] -= item.job.estimated_cost
                self._pending.clear()
            self._condition.notify_all()
        self._dispatcher.join(timeout=None if wait else 0)
        self._executor.shutdown(wait=wait, cancel_futures=cancel_pending)

    def _dispatch_loop(self) -> None:
        while True:
            with self._condition:
                if self._closed:
                    return
                dispatched = False
                while self._running_global < self.limits.global_max_concurrency:
                    item = self._select_next_locked()
                    if item is None:
                        break
                    self._pending.remove(item)
                    self._acquire_locked(item.job)
                    self._executor.submit(self._run, item)
                    dispatched = True
                if not dispatched:
                    self._condition.wait(timeout=0.05)

    def _select_next_locked(self) -> _PendingWork | None:
        eligible: list[_PendingWork] = []
        cancelled: list[_PendingWork] = []
        for item in self._pending:
            if item.future.cancelled():
                cancelled.append(item)
                continue
            job = item.job
            policy = self._policies[job.project_id]
            if self._project_states.get(job.project_id) != ProjectOperationalState.ACTIVE:
                continue
            if self._running_by_project.get(job.project_id, 0) >= policy.max_concurrency:
                continue
            if job.provider_key is not None:
                limit = self.limits.provider_concurrency.get(job.provider_key)
                if limit is not None and self._provider_running.get(job.provider_key, 0) >= limit:
                    continue
            if any(resource in self._held_resources for resource in job.shared_resources):
                continue
            eligible.append(item)

        for item in cancelled:
            self._pending.remove(item)
            self._budget_used[item.job.project_id] -= item.job.estimated_cost

        if not eligible:
            return None
        return max(
            eligible,
            key=lambda item: (
                self._policies[item.job.project_id].priority,
                item.job.priority,
                -item.sequence,
            ),
        )

    def _acquire_locked(self, job: SchedulerJob) -> None:
        self._running_global += 1
        self._running_by_project[job.project_id] = self._running_by_project.get(job.project_id, 0) + 1
        if job.provider_key is not None:
            self._provider_running[job.provider_key] = self._provider_running.get(job.provider_key, 0) + 1
        self._held_resources.update(job.shared_resources)

    def _release_locked(self, job: SchedulerJob) -> None:
        self._running_global -= 1
        self._running_by_project[job.project_id] -= 1
        if self._running_by_project[job.project_id] == 0:
            self._running_by_project.pop(job.project_id)
        if job.provider_key is not None:
            self._provider_running[job.provider_key] -= 1
            if self._provider_running[job.provider_key] == 0:
                self._provider_running.pop(job.provider_key)
        for resource in job.shared_resources:
            self._held_resources.discard(resource)

    def _run(self, item: _PendingWork) -> None:
        job = item.job
        future = item.future
        try:
            if not future.set_running_or_notify_cancel():
                with self._condition:
                    self._budget_used[job.project_id] -= job.estimated_cost
                return
            try:
                future.set_result(job.execute())
            except BaseException as exc:
                future.set_exception(exc)
        finally:
            with self._condition:
                self._release_locked(job)
                self._condition.notify_all()
