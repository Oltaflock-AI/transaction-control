from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from tc.db.models.task import Task
from tc.domain.enums import TaskSeverity, TaskStatus

# Severity weights used when computing the health score.
SEVERITY_WEIGHTS: dict[str, float] = {
    TaskSeverity.critical: 3.0,
    TaskSeverity.high: 2.0,
    TaskSeverity.medium: 1.0,
    TaskSeverity.low: 0.5,
}


def _weight(severity: str | None) -> float:
    """
    Map a task severity to its numeric weight, using medium as the default when none is provided.
    
    Parameters:
        severity (str | None): The task severity name or `None` to use the medium default.
    
    Returns:
        float: Numeric weight corresponding to the given severity.
    """
    return SEVERITY_WEIGHTS.get(severity or TaskSeverity.medium, 1.0)


def compute_health_score(db: Session, transaction_id: uuid.UUID) -> dict:
    """
    Compute a transaction health score based on overdue and imminently due tasks.
    
    Evaluates all tasks for the given transaction and classifies them as overdue or due soon (within 48 hours), accumulates severity-weighted scores, and determines a health level:
    - "RED" if any overdue task is critical or the total overdue weighted score is at least 3.0.
    - "YELLOW" if the overdue weighted score is at least 1.0 or there are any due-soon tasks.
    - "GREEN" otherwise (adds "All tasks on track" when no other reasons exist).
    
    Returns:
        dict: A mapping with keys:
            - "score": One of "GREEN", "YELLOW", or "RED".
            - "reasons": List of brief reason strings describing overdue or due-soon task counts and weighted scores.
    """
    now = datetime.now(UTC)
    due_soon_threshold = now + timedelta(hours=48)

    tasks = db.query(Task).filter(Task.transaction_id == transaction_id).all()

    overdue_count = 0
    due_soon_count = 0
    overdue_weighted = 0.0
    due_soon_weighted = 0.0
    has_critical_overdue = False
    reasons: list[str] = []

    for task in tasks:
        is_overdue = task.status == TaskStatus.overdue or (
            task.due_at is not None
            and task.due_at <= now
            and task.status in (TaskStatus.todo, TaskStatus.in_progress)
        )
        if is_overdue:
            overdue_count += 1
            overdue_weighted += _weight(task.severity)
            if (task.severity or TaskSeverity.medium) == TaskSeverity.critical:
                has_critical_overdue = True
            continue

        if (
            task.due_at is not None
            and task.due_at > now
            and task.due_at <= due_soon_threshold
            and task.status in (TaskStatus.todo, TaskStatus.in_progress)
        ):
            due_soon_count += 1
            due_soon_weighted += _weight(task.severity)

    if overdue_count > 0:
        reasons.append(f"{overdue_count} task(s) overdue (weighted score {overdue_weighted:.1f})")
    if due_soon_count > 0:
        reasons.append(
            f"{due_soon_count} task(s) due in next 48h (weighted score {due_soon_weighted:.1f})"
        )

    if has_critical_overdue or overdue_weighted >= 3.0:
        score = "RED"
    elif overdue_weighted >= 1.0 or due_soon_count > 0:
        score = "YELLOW"
    else:
        score = "GREEN"
        if not reasons:
            reasons.append("All tasks on track")

    return {"score": score, "reasons": reasons}
