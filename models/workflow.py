from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from .base import ContractModel
from .capability import CapabilityRequirement


class WorkflowNodeType(StrEnum):
    CAPABILITY = "CAPABILITY"
    CONDITION = "CONDITION"
    APPROVAL = "APPROVAL"
    END = "END"


class WorkflowNode(ContractModel):
    node_id: str
    node_type: WorkflowNodeType
    next_node_id: str | None = None

    requirement: CapabilityRequirement | None = None
    input_key: str = "__input__"
    output_key: str | None = None

    condition_key: str | None = None
    true_node_id: str | None = None
    false_node_id: str | None = None

    approval_key: str | None = None
    approval_prompt: str | None = None
    approved_node_id: str | None = None
    rejected_node_id: str | None = None

    max_visits: int = Field(default=1, ge=1, le=1000)

    @model_validator(mode="after")
    def validate_shape(self):
        if self.node_type == WorkflowNodeType.CAPABILITY:
            if self.requirement is None or self.next_node_id is None:
                raise ValueError("CAPABILITY node requires requirement and next_node_id")
        elif self.node_type == WorkflowNodeType.CONDITION:
            if not self.condition_key or not self.true_node_id or not self.false_node_id:
                raise ValueError("CONDITION node requires condition_key and both branches")
        elif self.node_type == WorkflowNodeType.APPROVAL:
            if (
                not self.approval_key
                or not self.approval_prompt
                or not self.approved_node_id
                or not self.rejected_node_id
            ):
                raise ValueError("APPROVAL node requires key, prompt, and both branches")
        elif self.node_type == WorkflowNodeType.END:
            if any(
                value is not None
                for value in (
                    self.next_node_id,
                    self.requirement,
                    self.condition_key,
                    self.true_node_id,
                    self.false_node_id,
                    self.approval_key,
                    self.approved_node_id,
                    self.rejected_node_id,
                )
            ):
                raise ValueError("END node must not have outgoing behavior")
        return self

    def targets(self) -> tuple[str, ...]:
        if self.node_type == WorkflowNodeType.CAPABILITY:
            return (self.next_node_id,) if self.next_node_id else ()
        if self.node_type == WorkflowNodeType.CONDITION:
            return tuple(x for x in (self.true_node_id, self.false_node_id) if x)
        if self.node_type == WorkflowNodeType.APPROVAL:
            return tuple(x for x in (self.approved_node_id, self.rejected_node_id) if x)
        return ()


class WorkflowDefinition(ContractModel):
    workflow_id: str
    workflow_version: str = "1.0.0"
    start_node_id: str
    nodes: tuple[WorkflowNode, ...]
    max_steps: int = Field(default=100, ge=1, le=10000)

    @model_validator(mode="after")
    def validate_graph(self):
        if not self.nodes:
            raise ValueError("workflow requires at least one node")
        by_id = {node.node_id: node for node in self.nodes}
        if len(by_id) != len(self.nodes):
            raise ValueError("workflow node_id values must be unique")
        if self.start_node_id not in by_id:
            raise ValueError("start_node_id does not exist")
        if not any(node.node_type == WorkflowNodeType.END for node in self.nodes):
            raise ValueError("workflow requires at least one END node")
        for node in self.nodes:
            for target in node.targets():
                if target not in by_id:
                    raise ValueError(f"workflow target does not exist: {target}")

        reachable: set[str] = set()
        pending = [self.start_node_id]
        while pending:
            node_id = pending.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            pending.extend(by_id[node_id].targets())
        if reachable != set(by_id):
            missing = sorted(set(by_id) - reachable)
            raise ValueError(f"workflow contains unreachable nodes: {missing}")
        if not any(by_id[node_id].node_type == WorkflowNodeType.END for node_id in reachable):
            raise ValueError("workflow has no reachable END node")
        return self

    def node(self, node_id: str) -> WorkflowNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(node_id)
