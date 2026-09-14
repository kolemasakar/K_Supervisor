from models.capability import CapabilityRequirement
from models.workflow import WorkflowDefinition, WorkflowNode, WorkflowNodeType


def build_example_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="example.research_report",
        workflow_version="1.0.0",
        start_node_id="research",
        nodes=(
            WorkflowNode(
                node_id="research",
                node_type=WorkflowNodeType.CAPABILITY,
                requirement=CapabilityRequirement(
                    capability_id="research.reference",
                    version_constraint="^1.0.0",
                    operation="research",
                ),
                output_key="research_output",
                next_node_id="report",
            ),
            WorkflowNode(
                node_id="report",
                node_type=WorkflowNodeType.CAPABILITY,
                requirement=CapabilityRequirement(
                    capability_id="report.reference",
                    version_constraint="^1.0.0",
                    operation="report",
                ),
                input_key="research_output",
                output_key="report_output",
                next_node_id="done",
            ),
            WorkflowNode(node_id="done", node_type=WorkflowNodeType.END),
        ),
    )
