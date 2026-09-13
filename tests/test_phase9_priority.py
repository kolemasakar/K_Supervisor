from threading import Event

from scheduler import ProjectSchedulePolicy, ProjectScheduler, SchedulerJob, SchedulerLimits
from tests.phase9_support import open_projects


def test_higher_project_priority_runs_first_when_slot_opens(tmp_path):
    store, projects = open_projects(tmp_path)
    scheduler = ProjectScheduler(projects, SchedulerLimits(global_max_concurrency=1))
    scheduler.register_project("P1", ProjectSchedulePolicy(priority=1))
    scheduler.register_project("P2", ProjectSchedulePolicy(priority=10))
    release = Event()
    started = Event()
    order = []

    blocker = scheduler.submit(
        SchedulerJob("BLOCK", "P1", lambda: (started.set(), release.wait(2), "block")[2])
    )
    assert started.wait(1)
    low = scheduler.submit(SchedulerJob("LOW", "P1", lambda: order.append("low")))
    high = scheduler.submit(SchedulerJob("HIGH", "P2", lambda: order.append("high")))
    release.set()
    assert blocker.result(2) == "block"
    high.result(2)
    low.result(2)
    assert order == ["high", "low"]
    scheduler.shutdown()
    store.close()
