from __future__ import annotations

from typing import Protocol

from .contracts import PolicyDecision


class PolicyAuditSink(Protocol):
    def append(self, decision: PolicyDecision) -> None: ...


class MemoryPolicyAuditSink:
    def __init__(self):
        self.decisions: list[PolicyDecision] = []

    def append(self, decision: PolicyDecision) -> None:
        self.decisions.append(decision)


class NullPolicyAuditSink:
    def append(self, decision: PolicyDecision) -> None:
        return None
