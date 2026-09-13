import pytest
from pydantic import ValidationError

from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType


def test_workflow_rejects_missing_transition_target():
    with pytest.raises(ValidationError):
        WorkflowDefinition(
            workflow_id="wf.invalid",
            start_node_id="check",
            nodes=(
                WorkflowNode(node_id="check", node_type=WorkflowNodeType.CONDITION,
                             condition_key="__input__.flag", true_node_id="missing",
                             false_node_id="done"),
                WorkflowNode(node_id="done", node_type=WorkflowNodeType.END),
            ),
        )
