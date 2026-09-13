from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType
from workflows import WorkflowExecutionStatus
from tests.phase7_support import build_workflow_stack


def test_approval_gate_waits_and_resumes(tmp_path):
    _, _, _, engine = build_workflow_stack(tmp_path)
    definition = WorkflowDefinition(
        workflow_id="wf.approval",
        start_node_id="gate",
        nodes=(
            WorkflowNode(node_id="gate", node_type=WorkflowNodeType.APPROVAL,
                         approval_key="owner", approval_prompt="Approve continuation",
                         approved_node_id="approved", rejected_node_id="rejected"),
            WorkflowNode(node_id="approved", node_type=WorkflowNodeType.END),
            WorkflowNode(node_id="rejected", node_type=WorkflowNodeType.END),
        ),
    )
    waiting = engine.start("P1", "approval", definition, {})
    assert waiting.status == WorkflowExecutionStatus.WAITING_FOR_APPROVAL

    resumed = engine.resume("P1", waiting.workflow_run_id, definition, approvals={"owner": True})
    assert resumed.status == WorkflowExecutionStatus.SUCCEEDED
    assert resumed.current_node_id == "approved"
