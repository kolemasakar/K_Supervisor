from threading import Event

from scheduler import ProjectSchedulePolicy, ProjectScheduler, SchedulerJob, SchedulerLimits
from tests.phase9_support import open_projects


def test_per_project_concurrency_limit_is_enforced(tmp_path):
    store, projects = open_projects(tmp_path)
    scheduler = ProjectScheduler(projects, SchedulerLimits(global_max_concurrency=2))
    scheduler.register_project("P1", ProjectSchedulePolicy(max_concurrency=1))
    scheduler.register_project("P2", ProjectSchedulePolicy(max_concurrency=1))
    release = Event()
    first_started = Event()
    second_started = Event()

    def first():
        first_started.set()
        assert release.wait(2)
        return 1

    first_future = scheduler.submit(SchedulerJob("P1-A", "P1", first))
    assert first_started.wait(1)
    second_future = scheduler.submit(
        SchedulerJob("P1-B", "P1", lambda: (second_started.set(), 2)[1])
    )
    assert not second_started.wait(0.2)
    assert scheduler.snapshot().running_by_project == {"P1": 1}
    release.set()
    assert first_future.result(2) == 1
    assert second_future.result(2) == 2
    scheduler.shutdown()
    store.close()
