from tests.phase12_support import build_reference_stack
from workflows.contracts import WorkflowExecutionStatus
from workflows.reference_loop import ReferenceResearchReviewWorkflow


def test_phase14_starts_waiting_for_profile_approval(tmp_path):
    store, _, _, _, _, _, kernel = build_reference_stack(tmp_path)
    flow = ReferenceResearchReviewWorkflow(kernel, store)
    result = flow.start("P12", "Reference review", {"query": "Q", "sources": ["source"]})
    assert result.status == WorkflowExecutionStatus.WAITING_FOR_APPROVAL
    assert store.list_agent_runs("P12") == ()
