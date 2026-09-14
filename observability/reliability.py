from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReliabilityReport:
    project_id: str
    passed: bool
    errors: tuple[str, ...]


class ReliabilityValidator:
    def __init__(self, store):
        self.store = store

    def check(self, project_id: str) -> ReliabilityReport:
        errors: list[str] = []
        project = self.store.get_project(project_id)
        if project is None:
            return ReliabilityReport(project_id, False, ("project is missing",))

        tasks = {item.task_id: item for item in self.store.list_tasks(project_id)}
        workflows = {item.workflow_run_id: item for item in self.store.list_workflow_runs(project_id)}
        notifications = {item.notification_id for item in self.store.list_notifications(project_id)}
        releases = {item.release_id for item in self.store.list_releases(project_id)}
        targets = {item.release_target_id: item for item in self.store.list_release_targets(project_id)}

        for run in self.store.list_agent_runs(project_id):
            if run.task_id not in tasks:
                errors.append(f"orphan agent run task: {run.run_id}")
            if run.workflow_run_id not in workflows:
                errors.append(f"orphan agent run workflow: {run.run_id}")

        for record in self.store.list_routing_records(project_id):
            if record.task_id not in tasks:
                errors.append(f"orphan routing task: {record.routing_record_id}")
            if record.workflow_run_id not in workflows:
                errors.append(f"orphan routing workflow: {record.routing_record_id}")
            if record.outcome == "SELECTED" and record.selected_agent_id not in record.candidate_agent_ids:
                errors.append(f"selected agent not in candidates: {record.routing_record_id}")

        for attempt in self.store.list_notification_delivery_attempts(project_id):
            if attempt.notification_id not in notifications:
                errors.append(f"orphan notification delivery: {attempt.delivery_attempt_id}")

        for target in targets.values():
            if target.release_id not in releases:
                errors.append(f"orphan release target: {target.release_target_id}")

        for record in self.store.list_release_validation_records(project_id):
            if record.release_id not in releases:
                errors.append(f"orphan release validation release: {record.validation_record_id}")
            if record.release_target_id not in targets:
                errors.append(f"orphan release validation target: {record.validation_record_id}")

        return ReliabilityReport(project_id, not errors, tuple(errors))
