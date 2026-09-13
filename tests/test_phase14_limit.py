from tests.phase12_support import build_reference_stack
from workflows.contracts import WorkflowExecutionStatus
from workflows.reference_loop import ReferenceResearchReviewWorkflow


def test_phase14_limit_never_false_approves(tmp_path):
    store, _, _, _, _, _, kernel = build_reference_stack(tmp_path)
    flow = ReferenceResearchReviewWorkflow(kernel, store, max_iterations=2)
    started = flow.start(
        "P12",
        "Bounded review",
        {"query": "Check", "sources": ["short"], "revision_sources": ["still short"]},
    )
    result = flow.approve_profile("P12", started.workflow_run_id, approved_by="OWNER")
    assert result.status == WorkflowExecutionStatus.FAILED
    assert result.context["reference_status"] == "MAX_ITERATIONS_REACHED"
    assert "final" not in result.context
    assert len(result.context["review_history"]) == 2
