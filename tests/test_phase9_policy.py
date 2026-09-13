from scheduler import ProjectSchedulePolicy
from tests.phase6_support import make_spec


def test_scheduler_policy_can_be_derived_from_project_spec():
    spec = make_spec().model_copy(
        update={
            "parallel_execution": {"priority": 7, "max_concurrency": 3},
            "risk": {"budget_limit": 12.5},
        }
    )
    policy = ProjectSchedulePolicy.from_spec(spec)
    assert policy.priority == 7
    assert policy.max_concurrency == 3
    assert policy.budget_limit == 12.5
