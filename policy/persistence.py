from __future__ import annotations

from persistence.base import PersistenceStore

from .contracts import PolicyDecision


class PersistencePolicyAuditSink:
    def __init__(self, store: PersistenceStore):
        self.store = store

    def append(self, decision: PolicyDecision) -> None:
        self.store.append_policy_decision(decision)
