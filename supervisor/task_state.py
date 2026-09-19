from enum import StrEnum

from models.task import Task


class TaskStatus(StrEnum):
    NEW = "NEW"
    ROUTING = "ROUTING"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


_ALLOWED = {
    TaskStatus.NEW: {TaskStatus.ROUTING, TaskStatus.CANCELLED},
    TaskStatus.ROUTING: {TaskStatus.RUNNING, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.RETRYING, TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.RETRYING: {TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.SUCCEEDED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.BLOCKED: set(),
    TaskStatus.CANCELLED: set(),
}


def transition_task(task: Task, to_status: TaskStatus, at) -> Task:
    current = TaskStatus(task.status)
    if to_status not in _ALLOWED[current]:
        raise ValueError(f"invalid task transition: {current} -> {to_status}")
    return task.model_copy(update={"status": to_status.value, "updated_at": at})
