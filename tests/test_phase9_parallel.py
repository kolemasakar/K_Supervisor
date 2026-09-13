from threading import Event

from scheduler import ProjectSchedulePolicy, ProjectScheduler, SchedulerJob, SchedulerLimits
from tests.phase9_support import open_projects


def test_two_projects_make_progress_concurrently(tmp_path):
    store, projects = open_projects(tmp_path)
    scheduler = ProjectScheduler(projects, SchedulerLimits(global_max_concurrency=2))
    scheduler.register_project("P1", ProjectSchedulePolicy(max_concurrency=1))
    scheduler.register_project("P2", ProjectSchedulePolicy(max_concurrency=1))
    release = Event()
    first = Event()
    second = Event()

    def work(started, value):
        started.set()
        assert release.wait(2)
        return value

    f1 = scheduler.submit(SchedulerJob("W1", "P1", lambda: work(first, "P1")))
    f2 = scheduler.submit(SchedulerJob("W2", "P2", lambda: work(second, "P2")))
    assert first.wait(1)
    assert second.wait(1)
    assert scheduler.snapshot().running_global == 2
    release.set()
    assert {f1.result(2), f2.result(2)} == {"P1", "P2"}
    scheduler.shutdown()
    store.close()
