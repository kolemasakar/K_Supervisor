from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock
from time import sleep

from models.enums import HumanActionStatus, ProjectLifecycleState, ProjectOperationalState
from models.intervention import HumanActionRequest
from models.project import Project
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry
from scheduler import ProjectSchedulePolicy, ProjectScheduler, SchedulerJob, SchedulerLimits
from supervisor.human_intervention import HumanInterventionBroker

NOW = datetime(2026, 9, 16, 19, 0, tzinfo=timezone.utc)


def _project(project_id: str) -> Project:
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=ProjectLifecycleState.BUILDING,
        operational_state=ProjectOperationalState.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    )


def test_owner_wait_isolated_while_other_project_progresses_across_restart(tmp_path):
    path = tmp_path / "state.db"
    store = SQLitePersistenceStore(path)
    store.initialize()
    projects = ProjectRegistry(store)
    projects.register(_project("P8_OWNER_WAIT"))
    projects.register(_project("P8_ACTIVE"))
    human = HumanInterventionBroker(store, projects)
    action = human.open(
        HumanActionRequest(
            human_action_id="HUMAN_P8_OWNER",
            project_id="P8_OWNER_WAIT",
            action_type="OWNER_DECISION",
            title="Owner decision",
            summary="Owner decision required before this project resumes.",
            required_action="Confirm continuation.",
            blocking=True,
            created_at=NOW + timedelta(minutes=1),
            resume_condition="owner_confirmed",
            verification_method="OWNER_CONFIRMATION",
        )
    )
    assert action.status == HumanActionStatus.WAITING_FOR_OWNER
    assert (
        projects.get("P8_OWNER_WAIT").operational_state
        == ProjectOperationalState.WAITING_FOR_OWNER
    )
    store.close()

    completed: list[str] = []
    guard = Lock()

    def record(project_id: str) -> str:
        with guard:
            completed.append(project_id)
        return project_id

    reopened = SQLitePersistenceStore(path)
    reopened.initialize()
    recovered_projects = ProjectRegistry(reopened)
    owner_snapshot = recovered_projects.recover("P8_OWNER_WAIT")
    active_snapshot = recovered_projects.recover("P8_ACTIVE")
    assert owner_snapshot.project.operational_state == ProjectOperationalState.WAITING_FOR_OWNER
    assert owner_snapshot.human_actions[0].status == HumanActionStatus.WAITING_FOR_OWNER
    assert active_snapshot.project.operational_state == ProjectOperationalState.ACTIVE
    assert active_snapshot.human_actions == ()

    scheduler = ProjectScheduler(
        recovered_projects,
        SchedulerLimits(global_max_concurrency=2),
    )
    policy = ProjectSchedulePolicy(max_concurrency=1)
    scheduler.register_project("P8_OWNER_WAIT", policy)
    scheduler.register_project("P8_ACTIVE", policy)
    blocked = scheduler.submit(
        SchedulerJob(
            work_id="blocked-owner-work",
            project_id="P8_OWNER_WAIT",
            execute=lambda: record("P8_OWNER_WAIT"),
        )
    )
    active = scheduler.submit(
        SchedulerJob(
            work_id="active-work",
            project_id="P8_ACTIVE",
            execute=lambda: record("P8_ACTIVE"),
        )
    )

    assert active.result(timeout=2) == "P8_ACTIVE"
    sleep(0.1)
    assert not blocked.done()
    assert completed == ["P8_ACTIVE"]

    recovered_human = HumanInterventionBroker(reopened, recovered_projects)
    resolved = recovered_human.verify(
        "HUMAN_P8_OWNER", True, NOW + timedelta(minutes=2)
    )
    assert resolved.status == HumanActionStatus.VERIFIED
    scheduler.notify_state_changed("P8_OWNER_WAIT")
    assert blocked.result(timeout=2) == "P8_OWNER_WAIT"
    assert set(completed) == {"P8_ACTIVE", "P8_OWNER_WAIT"}
    scheduler.shutdown()
    reopened.close()

    with SQLitePersistenceStore(path) as final_store:
        final_projects = ProjectRegistry(final_store)
        owner_final = final_projects.recover("P8_OWNER_WAIT")
        active_final = final_projects.recover("P8_ACTIVE")
        assert owner_final.project.operational_state == ProjectOperationalState.ACTIVE
        assert owner_final.human_actions[0].status == HumanActionStatus.VERIFIED
        assert active_final.project.operational_state == ProjectOperationalState.ACTIVE
        assert active_final.human_actions == ()
