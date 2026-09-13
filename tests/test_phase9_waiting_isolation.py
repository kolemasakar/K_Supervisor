from datetime import timedelta

from models.enums import ProjectOperationalState
from scheduler import ProjectSchedulePolicy, ProjectScheduler, SchedulerJob, SchedulerLimits
from tests.phase9_support import NOW, open_projects


def test_waiting_project_does_not_block_active_project(tmp_path):
    store, projects = open_projects(
        tmp_path,
        {
            "P1": ProjectOperationalState.WAITING_FOR_OWNER,
            "P2": ProjectOperationalState.ACTIVE,
        },
    )
    scheduler = ProjectScheduler(projects, SchedulerLimits(global_max_concurrency=2))
    scheduler.register_project("P1", ProjectSchedulePolicy())
    scheduler.register_project("P2", ProjectSchedulePolicy())

    waiting = scheduler.submit(SchedulerJob("W1", "P1", lambda: "P1"))
    active = scheduler.submit(SchedulerJob("W2", "P2", lambda: "P2"))
    assert active.result(2) == "P2"
    assert not waiting.done()

    projects.transition_operational("P1", ProjectOperationalState.ACTIVE, NOW + timedelta(minutes=1))
    scheduler.notify_state_changed()
    assert waiting.result(2) == "P1"
    scheduler.shutdown()
    store.close()
