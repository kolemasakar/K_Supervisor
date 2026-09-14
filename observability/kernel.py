from datetime import datetime, timezone
from models.observability_records import RoutingRecord
from .routing import record_routing


class ObservableSupervisorKernel:
    def __init__(self, kernel):
        self.kernel = kernel

    def __getattr__(self, name):
        return getattr(self.kernel, name)

    def run_task(self, project_id, title, requirement, input_data, **kwargs):
        providers = self.kernel.agents.find_providers(requirement)
        result = self.kernel.run_task(project_id, title, requirement, input_data, **kwargs)
        at = datetime.now(timezone.utc)
        record = RoutingRecord(
            routing_record_id=f"ROUTE_{result.task_id}",
            project_id=project_id,
            task_id=result.task_id,
            workflow_run_id=result.workflow_run_id,
            capability_id=requirement.capability_id,
            version_constraint=requirement.version_constraint,
            operation=requirement.operation,
            candidate_agent_ids=tuple(item.agent.agent_id for item in providers),
            selected_agent_id=result.agent_id,
            selected_capability_version=result.capability_version,
            outcome="SELECTED",
            created_at=at,
        )
        record_routing(self.kernel.store, record, occurred_at=at)
        return result
