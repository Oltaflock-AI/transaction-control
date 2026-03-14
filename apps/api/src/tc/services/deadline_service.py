from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from tc.db.models.event_log import EventLog
from tc.db.models.task import Task
from tc.domain.enums import TaskStatus
from tc.domain.rules import evaluate_rules
from tc.services.audit_service import create_audit_event

logger = logging.getLogger(__name__)


def check_deadlines(db: Session) -> dict:
    """
    1. Mark past-due tasks as overdue.
    2. Detect tasks due within the next 48 hours (Due Soon).
    3. Emit event_log + audit_events entries.
    """
    now = datetime.now(UTC)
    due_soon_threshold = now + timedelta(hours=48)

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

        evaluate_rules(db, trigger="task.overdue", source_task=task)

    due_soon_tasks: list[Task] = (
        db.query(Task)
        .options(joinedload(Task.transaction))
        .filter(
            Task.due_at.isnot(None),
            Task.due_at > now,
            Task.due_at <= due_soon_threshold,
            Task.status.in_([TaskStatus.todo, TaskStatus.in_progress]),
        )
        .all()
    )

    due_soon_count = 0
    for task in due_soon_tasks:
        already_logged = (
            db.query(EventLog)
            .filter(EventLog.entity_id == task.id, EventLog.event_type == "task.due_soon")
            .first()
        )

        if not already_logged:
            payload = {
                "task_id": str(task.id),
                "task_title": task.title,
                "due_at": task.due_at.isoformat(),
                "hours_remaining": round(
                    (task.due_at.replace(tzinfo=UTC) - now).total_seconds() / 3600, 1
                ),
            }
            db.add(
                EventLog(
                    transaction_id=task.transaction_id,
                    event_type="task.due_soon",
                    entity_type="task",
                    entity_id=task.id,
                    detail=json.dumps(payload),
                )
            )

            evaluate_rules(db, trigger="task.due_soon", source_task=task)

            due_soon_count += 1

    db.commit()

    logger.info(
        "check_deadlines: marked %d overdue, detected %d new due-soon",
        len(overdue_tasks),
        due_soon_count,
    )

    return {
        "checked_at": now.isoformat(),
        "overdue_marked": len(overdue_tasks),
        "due_soon_logged": due_soon_count,
    }
