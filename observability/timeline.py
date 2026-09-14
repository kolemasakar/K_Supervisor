from models.audit import AuditEvent


class AuditTimeline:
    def __init__(self, store):
        self.store = store

    def events(self, project_id: str) -> tuple[AuditEvent, ...]:
        items = list(self.store.list_audit_events(project_id))
        items.extend(self._interventions(project_id))
        items.extend(self._notifications(project_id))
        items.extend(self._routing(project_id))
        items.extend(self._release_validations(project_id))
        items.extend(self._releases(project_id))
        return tuple(sorted(items, key=lambda item: (item.occurred_at, item.audit_event_id)))

    def _interventions(self, project_id):
        return [
            AuditEvent(
                audit_event_id=f"VIEW_HUMAN_{item.human_action_id}_{item.status.value}",
                project_id=project_id,
                category="INTERVENTION",
                event_type=f"HUMAN_ACTION_{item.status.value}",
                occurred_at=item.resolved_at or item.created_at,
                resource_type="HumanActionRequest",
                resource_id=item.human_action_id,
                details={"blocking": item.blocking, "action_type": item.action_type},
            )
            for item in self.store.list_human_actions(project_id)
        ]

    def _notifications(self, project_id):
        result = []
        for item in self.store.list_notifications(project_id):
            result.append(AuditEvent(
                audit_event_id=f"VIEW_NOTIFICATION_{item.notification_id}",
                project_id=project_id,
                category="NOTIFICATION",
                event_type="NOTIFICATION_CREATED",
                occurred_at=item.created_at,
                resource_type="NotificationEvent",
                resource_id=item.notification_id,
                severity=item.severity,
                details={"event_type": item.event_type, "channel": item.channel.value},
            ))
        for item in self.store.list_notification_delivery_attempts(project_id):
            result.append(AuditEvent(
                audit_event_id=f"VIEW_DELIVERY_{item.delivery_attempt_id}_{item.status.value}",
                project_id=project_id,
                category="NOTIFICATION",
                event_type=f"NOTIFICATION_DELIVERY_{item.status.value}",
                occurred_at=item.completed_at or item.created_at,
                resource_type="NotificationDeliveryAttempt",
                resource_id=item.delivery_attempt_id,
                correlation_id=item.notification_id,
                severity="WARNING" if item.status.value == "FAILED" else "INFO",
                details={"attempt_number": item.attempt_number, "channel": item.channel.value},
            ))
        return result

    def _routing(self, project_id):
        return [
            AuditEvent(
                audit_event_id=f"VIEW_ROUTE_{item.routing_record_id}",
                project_id=project_id,
                category="ROUTING",
                event_type=f"ROUTING_{item.outcome}",
                occurred_at=item.created_at,
                resource_type="Task",
                resource_id=item.task_id,
                correlation_id=item.workflow_run_id,
                details={"capability_id": item.capability_id, "selected_agent_id": item.selected_agent_id},
            )
            for item in self.store.list_routing_records(project_id)
        ]

    def _release_validations(self, project_id):
        return [
            AuditEvent(
                audit_event_id=f"VIEW_RELEASE_VALIDATION_{item.validation_record_id}",
                project_id=project_id,
                category="RELEASE",
                event_type="RELEASE_VALIDATION",
                occurred_at=item.created_at,
                resource_type="ReleaseTarget",
                resource_id=item.release_target_id,
                correlation_id=item.release_id,
                severity="INFO" if item.ready else "WARNING",
                details={"ready": item.ready, "failed_check_ids": list(item.failed_check_ids)},
            )
            for item in self.store.list_release_validation_records(project_id)
        ]

    def _releases(self, project_id):
        return [
            AuditEvent(
                audit_event_id=f"VIEW_RELEASE_{item.release_id}_{item.status.value}",
                project_id=project_id,
                category="RELEASE",
                event_type=f"RELEASE_{item.status.value}",
                occurred_at=item.updated_at,
                resource_type="Release",
                resource_id=item.release_id,
                details={"version": item.version, "targets": list(item.targets)},
            )
            for item in self.store.list_releases(project_id)
        ]
