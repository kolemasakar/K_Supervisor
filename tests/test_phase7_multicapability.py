from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType
from workflows import WorkflowExecutionStatus

from tests.phase7_support import build_workflow_stack, requirement


def test_workflow_composes_two_capabilities_without_agent_coupling(tmp_path):
    store, _, _, engine = build_workflow_stack(tmp_path)
    definition = WorkflowDefinition(
        workflow_id="workflow.multi",
        start_node_id="first",
        nodes=(
            WorkflowNode(
                node_id="first",
                node_type=WorkflowNodeType.CAPABILITY,
                requirement=requirement("analysis.first"),
                input_key="__input__",
                output_key="first_output",
                next_node_id="second",
            ),
            WorkflowNode(
                node_id="second",
                node_type=WorkflowNodeType.CAPABILITY,
                requirement=requirement("report.second"),
                input_key="first_output",
                output_key="second_output",
                next_node_id="done",
            ),
            WorkflowNode(node_id="done", node_type=WorkflowNodeType.END),
        ),
    )

    result = engine.start("P1", "multi", definition, {"seed": 2})

    assert result.status == WorkflowExecutionStatus.SUCCEEDED
    assert result.context["first_output"] == {"value": 3}
    assert result.context["second_output"] == {"final": 6}
    runs = store.list_agent_runs("P1")
    assert [run.agent_id for run in runs] == ["agent.first", "agent.second"]
    assert {run.capability_id for run in runs} == {"analysis.first", "report.second"}
