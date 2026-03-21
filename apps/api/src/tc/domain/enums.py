from enum import StrEnum


class TaskStatus(StrEnum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    overdue = "overdue"
