from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from tc.db.models.task import Task
from tc.db.models.timeline import TimelineItem
from tc.domain.enums import TaskStatus

TEMPLATE_TASKS: list[tuple[str, int]] = [
    ("Review contract", 3),
    ("Order inspection", 7),
    ("Appraisal review", 14),
    ("Title search", 21),
    ("Final walkthrough", 28),
]


def generate_default_timeline(db: Session, transaction_id: uuid.UUID) -> list[Task]:
    """Create a set of starter tasks and matching timeline items for a new transaction."""
    now = datetime.now(UTC)
    tasks: list[Task] = []

    for title, offset_days in TEMPLATE_TASKS:
        due = now + timedelta(days=offset_days)

        task = Task(
            transaction_id=transaction_id,
            title=title,
            status=TaskStatus.todo,
            due_at=due,
        )
        db.add(task)
        tasks.append(task)

        item = TimelineItem(
            transaction_id=transaction_id,
            label=title,
            due_at=due,
        )
        db.add(item)

    db.commit()
    return tasks
