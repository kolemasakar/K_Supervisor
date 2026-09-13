from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType
from workflows import WorkflowExecutionStatus
from tests.phase7_support import build_workflow_stack


def test_condition_branch(tmp_path):
    _, _, _, engine = build_workflow_stack(tmp_path)
    definition = WorkflowDefinition(
        workflow_id="wf.condition",
        start_node_id="check",
        nodes=(
            WorkflowNode(node_id="check", node_type=WorkflowNodeType.CONDITION,
                         condition_key="__input__.flag", true_node_id="yes", false_node_id="no"),
            WorkflowNode(node_id="yes", node_type=WorkflowNodeType.END),
            WorkflowNode(node_id="no", node_type=WorkflowNodeType.END),
        ),
    )
    result = engine.start("P1", "condition", definition, {"flag": True})
    assert result.status == WorkflowExecutionStatus.SUCCEEDED
    assert result.current_node_id == "yes"
