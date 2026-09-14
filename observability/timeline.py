from models.audit import AuditEvent


class AuditTimeline:
    def __init__(self, store):
        self.store = store

    def events(self, project_id: str) -> tuple[AuditEvent, ...]:
        items = self.store.list_audit_events(project_id)
        return tuple(sorted(items, key=lambda item: (item.occurred_at, item.audit_event_id)))
