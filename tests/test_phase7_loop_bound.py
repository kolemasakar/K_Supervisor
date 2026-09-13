from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType
from workflows import WorkflowExecutionStatus
from tests.phase7_support import build_workflow_stack


def test_loop_is_bounded_by_node_visits(tmp_path):
    _, _, _, engine = build_workflow_stack(tmp_path)
    definition = WorkflowDefinition(
        workflow_id="wf.loop",
        start_node_id="loop",
        max_steps=10,
        nodes=(
            WorkflowNode(node_id="loop", node_type=WorkflowNodeType.CONDITION,
                         condition_key="__input__.flag", true_node_id="loop",
                         false_node_id="done", max_visits=2),
            WorkflowNode(node_id="done", node_type=WorkflowNodeType.END),
        ),
    )
    result = engine.start("P1", "loop", definition, {"flag": True})
    assert result.status == WorkflowExecutionStatus.FAILED
    assert result.error == "node max_visits exceeded: loop"
