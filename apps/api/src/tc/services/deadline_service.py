from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from tc.db.models.event_log import EventLog
from tc.db.models.task import Task
from tc.domain.enums import TaskStatus
from tc.services.audit_service import create_audit_event

logger = logging.getLogger(__name__)


def check_deadlines(db: Session) -> dict:
    """Mark past-due tasks as overdue and emit event_log + audit_events entries.

    Returns a summary dict with check time and count.
    """
    now = datetime.now(UTC)

    overdue_tasks: list[Task] = (
        db.query(Task)
        .options(joinedload(Task.transaction))
        .filter(
            Task.due_at.isnot(None),
            Task.due_at < now,
            Task.status.notin_([TaskStatus.done, TaskStatus.overdue]),
        )
        .all()
    )

    if not overdue_tasks:
        logger.info("check_deadlines: no newly overdue tasks")
        return {"checked_at": now.isoformat(), "overdue_marked": 0}

    for task in overdue_tasks:
        old_status = task.status
        task.status = TaskStatus.overdue

        payload = {
            "task_id": str(task.id),
            "task_title": task.title,
            "transaction_id": str(task.transaction_id),
            "old_status": old_status,
            "new_status": TaskStatus.overdue,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "marked_overdue_at": now.isoformat(),
        }
        detail = json.dumps(payload)

        db.add(
            EventLog(
                transaction_id=task.transaction_id,
                event_type="task.overdue",
                entity_type="task",
                entity_id=task.id,
                detail=detail,
            )
        )

        create_audit_event(
            db,
            org_id=task.transaction.org_id,
            action="task.marked_overdue",
            entity_type="task",
            entity_id=task.id,
            actor_id=None,
            detail=detail,
        )

    db.commit()

    count = len(overdue_tasks)
    logger.info("check_deadlines: marked %d task(s) overdue", count)
    return {"checked_at": now.isoformat(), "overdue_marked": count}
