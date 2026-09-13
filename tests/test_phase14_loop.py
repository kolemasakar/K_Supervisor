from tests.phase12_support import build_reference_stack
from workflows.contracts import WorkflowExecutionStatus
from workflows.reference_loop import ReferenceResearchReviewWorkflow


def test_phase14_revision_then_pass(tmp_path):
    store, _, _, _, _, _, kernel = build_reference_stack(tmp_path)
    flow = ReferenceResearchReviewWorkflow(kernel, store, max_iterations=3)
    started = flow.start(
        "P12",
        "Reference review",
        {
            "query": "Evaluate evidence",
            "sources": ["short"],
            "revision_sources": ["A sufficiently detailed authoritative evidence statement for the revised iteration."],
        },
    )
    result = flow.approve_profile("P12", started.workflow_run_id, approved_by="OWNER")
    assert result.status == WorkflowExecutionStatus.SUCCEEDED
    assert [item["verdict"] for item in result.context["review_history"]] == ["REVISE", "PASS"]
    assert result.context["final"]["final_report"]
    assert result.context["final"]["review_protocol"]
