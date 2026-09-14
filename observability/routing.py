from datetime import datetime
from models.observability_records import RoutingRecord
from .audit import record_audit


def record_routing(store, record: RoutingRecord, *, occurred_at: datetime) -> RoutingRecord:
    store.append_routing_record(record)
    record_audit(
        store,
        project_id=record.project_id,
        category="ROUTING",
        event_type=f"ROUTING_{record.outcome}",
        occurred_at=occurred_at,
        resource_type="Task",
        resource_id=record.task_id,
        correlation_id=record.workflow_run_id,
        details={
            "capability_id": record.capability_id,
            "candidate_count": len(record.candidate_agent_ids),
            "selected_agent_id": record.selected_agent_id,
            "selected_capability_version": record.selected_capability_version,
        },
    )
    return record
