from factory import build_draft_project_spec
from tests.phase6_support import NOW


def test_onboarding_handoff_is_draft():
    spec = build_draft_project_spec(
        "P6",
        {
            "name": "Demo",
            "purpose": "Demo purpose",
            "problem_statement": "Demo problem",
            "project_type": "AI",
            "success_criteria": ["validated"],
            "first_working_criteria": ["runs"],
            "repository": {"repository_provider": "FILESYSTEM", "repository_name": "demo"},
        },
        NOW,
    )
    assert spec.status.value == "DRAFT"
