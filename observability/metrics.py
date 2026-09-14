from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from models.enums import DeliveryStatus, ExecutionStatus, HumanActionStatus
from models.metrics import AgentMetrics, ProjectMetrics


class MetricsCollector:
    def __init__(self, store):
        self.store = store

    def snapshot(self, project_id: str, generated_at: datetime) -> ProjectMetrics:
        tasks = self.store.list_tasks(project_id)
        runs = self.store.list_agent_runs(project_id)
        actions = self.store.list_human_actions(project_id)
        deliveries = self.store.list_notification_delivery_attempts(project_id)
        by_agent = defaultdict(list)
        for run in runs:
            by_agent[run.agent_id].append(run)
        agent_metrics = tuple(self._agent(agent_id, items) for agent_id, items in sorted(by_agent.items()))
        open_states = {
            HumanActionStatus.OPEN,
            HumanActionStatus.NOTIFIED,
            HumanActionStatus.WAITING_FOR_OWNER,
            HumanActionStatus.VERIFYING,
        }
        return ProjectMetrics(
            project_id=project_id,
            generated_at=generated_at,
            lifecycle_transitions=len(self.store.list_lifecycle_transitions(project_id)),
            operational_transitions=len(self.store.list_operational_transitions(project_id)),
            tasks_total=len(tasks),
            tasks_succeeded=sum(item.status == "SUCCEEDED" for item in tasks),
            tasks_failed=sum(item.status == "FAILED" for item in tasks),
            tasks_blocked=sum(item.status == "BLOCKED" for item in tasks),
            agent_runs_total=len(runs),
            routing_records=len(self.store.list_routing_records(project_id)),
            human_actions_total=len(actions),
            human_actions_open=sum(item.status in open_states for item in actions),
            notifications_total=len(self.store.list_notifications(project_id)),
            deliveries_sent=sum(item.status == DeliveryStatus.SENT for item in deliveries),
            deliveries_failed=sum(item.status == DeliveryStatus.FAILED for item in deliveries),
            releases_total=len(self.store.list_releases(project_id)),
            release_validations=len(self.store.list_release_validation_records(project_id)),
            audit_events_total=len(self.store.list_audit_events(project_id)),
            agents=agent_metrics,
        )

    @staticmethod
    def _agent(agent_id: str, runs) -> AgentMetrics:
        total = len(runs)
        succeeded = sum(item.status == ExecutionStatus.SUCCEEDED for item in runs)
        return AgentMetrics(
            agent_id=agent_id,
            runs_total=total,
            succeeded=succeeded,
            failed=sum(item.status == ExecutionStatus.FAILED for item in runs),
            blocked=sum(item.status == ExecutionStatus.BLOCKED for item in runs),
            timed_out=sum(item.status == ExecutionStatus.TIMED_OUT for item in runs),
            cancelled=sum(item.status == ExecutionStatus.CANCELLED for item in runs),
            success_rate=(succeeded / total) if total else 0.0,
        )
