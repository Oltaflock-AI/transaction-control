from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from tc.db.models.task import Task
from tc.domain.enums import TaskStatus


def compute_health_score(db: Session, transaction_id: uuid.UUID) -> dict:
    """
    Compute a GREEN / YELLOW / RED health score for a transaction.

    - RED:    any task is overdue
    - YELLOW: any task is due within 48 hours and still todo/in_progress
    - GREEN:  everything is fine
    """
    now = datetime.now(UTC)
    due_soon_threshold = now + timedelta(hours=48)

    tasks = db.query(Task).filter(Task.transaction_id == transaction_id).all()

    overdue_count = 0
    due_soon_count = 0
    reasons: list[str] = []

    for task in tasks:
        if task.status == TaskStatus.overdue:
            overdue_count += 1

        if (
            task.due_at is not None
            and task.due_at > now
            and task.due_at <= due_soon_threshold
            and task.status in (TaskStatus.todo, TaskStatus.in_progress)
        ):
            due_soon_count += 1

    if overdue_count > 0:
        reasons.append(f"{overdue_count} task(s) overdue")
    if due_soon_count > 0:
        reasons.append(f"{due_soon_count} task(s) due in next 48h")

    if overdue_count > 0:
        score = "RED"
    elif due_soon_count > 0:
        score = "YELLOW"
    else:
        score = "GREEN"
        if not reasons:
            reasons.append("All tasks on track")

    return {"score": score, "reasons": reasons}
