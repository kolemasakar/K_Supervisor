from threading import Event

import pytest

from scheduler import (
    ProjectBudgetExceeded,
    ProjectSchedulePolicy,
    ProjectScheduler,
    SchedulerJob,
    SchedulerLimits,
)
from tests.phase9_support import open_projects


def test_shared_resource_and_provider_limits_serialize_work(tmp_path):
    store, projects = open_projects(tmp_path)
    scheduler = ProjectScheduler(
        projects,
        SchedulerLimits(global_max_concurrency=2, provider_concurrency={"MODEL": 1}),
    )
    scheduler.register_project("P1", ProjectSchedulePolicy(max_concurrency=2))
    scheduler.register_project("P2", ProjectSchedulePolicy(max_concurrency=2))
    release = Event()
    first_started = Event()
    second_started = Event()

    def first():
        first_started.set()
        assert release.wait(2)
        return "first"

    f1 = scheduler.submit(
        SchedulerJob("W1", "P1", first, provider_key="MODEL", shared_resources=("GPU",))
    )
    assert first_started.wait(1)
    f2 = scheduler.submit(
        SchedulerJob(
            "W2",
            "P2",
            lambda: (second_started.set(), "second")[1],
            provider_key="MODEL",
            shared_resources=("GPU",),
        )
    )
    assert not second_started.wait(0.2)
    release.set()
    assert f1.result(2) == "first"
    assert f2.result(2) == "second"
    scheduler.shutdown()
    store.close()


def test_project_budget_is_enforced_at_admission(tmp_path):
    store, projects = open_projects(tmp_path)
    scheduler = ProjectScheduler(projects)
    scheduler.register_project("P1", ProjectSchedulePolicy(budget_limit=5.0))
    scheduler.register_project("P2", ProjectSchedulePolicy())
    assert scheduler.submit(SchedulerJob("W1", "P1", lambda: "ok", estimated_cost=3.0)).result(2) == "ok"
    with pytest.raises(ProjectBudgetExceeded):
        scheduler.submit(SchedulerJob("W2", "P1", lambda: "no", estimated_cost=2.1))
    assert scheduler.snapshot().budget_used["P1"] == 3.0
    scheduler.shutdown()
    store.close()
