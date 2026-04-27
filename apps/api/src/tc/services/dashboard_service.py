import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from tc.db.models.task import Task
from tc.db.models.transaction import Transaction
from tc.domain.enums import TaskStatus


def get_agent_dashboard(db: Session, user_id: uuid.UUID, org_id: uuid.UUID):
    now = datetime.now(UTC)
    soon = now + timedelta(hours=48)

    # Total active transactions they are assigned work in
    total_txns = (
        db.query(func.count(func.distinct(Task.transaction_id)))
        .join(Transaction)
        .filter(
            Task.assignee_id == user_id,
            Transaction.org_id == org_id,
            Transaction.status != "closed",
        )
        .scalar()
        or 0
    )

    tasks_overdue = (
        db.query(func.count(Task.id))
        .join(Transaction)
        .filter(
            Task.assignee_id == user_id,
            Transaction.org_id == org_id,
            Task.status == TaskStatus.overdue,
        )
        .scalar()
        or 0
    )

    tasks_due_soon = (
        db.query(func.count(Task.id))
        .join(Transaction)
        .filter(
            Task.assignee_id == user_id,
            Transaction.org_id == org_id,
            Task.status.notin_([TaskStatus.done, TaskStatus.overdue]),
            Task.due_at <= soon,
        )
        .scalar()
        or 0
    )

    risk_txns_ids = db.query(Task.transaction_id).filter(Task.assignee_id == user_id).subquery()

    deals_at_risk = (
        db.query(Transaction)
        .filter(
            Transaction.org_id == org_id,
            Transaction.id.in_(risk_txns_ids),
            Transaction.health_score.in_(["RED", "YELLOW"]),
            Transaction.status != "closed",
        )
        .all()
    )

    return total_txns, tasks_overdue, tasks_due_soon, deals_at_risk


def get_admin_dashboard(db: Session, org_id: uuid.UUID):
    now = datetime.now(UTC)
    soon = now + timedelta(hours=48)

    total_txns = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.org_id == org_id, Transaction.status != "closed")
        .scalar()
        or 0
    )

    tasks_overdue = (
        db.query(func.count(Task.id))
        .join(Transaction)
        .filter(Transaction.org_id == org_id, Task.status == TaskStatus.overdue)
        .scalar()
        or 0
    )

    tasks_due_soon = (
        db.query(func.count(Task.id))
        .join(Transaction)
        .filter(
            Transaction.org_id == org_id,
            Task.status.notin_([TaskStatus.done, TaskStatus.overdue]),
            Task.due_at <= soon,
        )
        .scalar()
        or 0
    )

    deals_at_risk = (
        db.query(Transaction)
        .filter(
            Transaction.org_id == org_id,
            Transaction.health_score.in_(["RED", "YELLOW"]),
            Transaction.status != "closed",
        )
        .all()
    )

    return total_txns, tasks_overdue, tasks_due_soon, deals_at_risk
