from tests.phase12_support import build_reference_stack
from workflows.reference_loop import ReferenceResearchReviewWorkflow


def test_phase14_profile_edits_are_preserved(tmp_path):
    store, _, _, _, _, _, kernel = build_reference_stack(tmp_path)
    flow = ReferenceResearchReviewWorkflow(kernel, store)
    started = flow.start(
        "P12",
        "Profile edits",
        {"query": "Evaluate", "sources": ["A detailed source statement long enough for review acceptance."]},
    )
    result = flow.approve_profile(
        "P12",
        started.workflow_run_id,
        approved_by="OWNER",
        edits={"domain": "science", "evaluation_criteria": ["accuracy", "evidence"]},
    )
    profile = result.context["profile"]
    assert profile["domain"] == "science"
    assert profile["evaluation_criteria"] == ["accuracy", "evidence"]
    assert profile["status"] == "APPROVED"
    assert result.context["__structured_approvals__"]["critic_profile"]["edited"] is True
