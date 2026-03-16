from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from tc.db.models.task import Task
from tc.domain.enums import TaskStatus
from tc.services.audit_service import create_audit_event


class TaskNotFoundError(ValueError):
    """Raised when a task lookup by id fails."""


class TransactionNotFoundError(ValueError):
    """Raised when a transaction is missing (e.g. deleted) during an operation."""


def create_task(
    db: Session,
    *,
    transaction_id: uuid.UUID,
    title: str,
    description: str | None = None,
    assignee_id: uuid.UUID | None = None,
    due_at: datetime | None = None,
    dedupe_key: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    commit: bool = True,
) -> Task:
    """
    Create a Task associated with the specified transaction and record a corresponding audit event.
    
    Parameters:
        transaction_id (uuid.UUID): ID of the transaction to attach the task to.
        title (str): Short title for the task.
        description (str | None): Optional longer description of the task.
        assignee_id (uuid.UUID | None): Optional user ID to assign the task to.
        due_at (datetime | None): Optional due date/time for the task.
        dedupe_key (str | None): Optional key used to deduplicate tasks.
        category (str | None): Optional category label for the task.
        severity (str | None): Optional severity label for the task.
        commit (bool): If True, commit the current DB session and refresh the returned task.
    
    Returns:
        Task: The created Task instance.
    
    Raises:
        ValueError: If no transaction exists with the given `transaction_id`.
    """
    from tc.db.models.transaction import Transaction

    task = Task(
        transaction_id=transaction_id,
        title=title,
        description=description,
        assignee_id=assignee_id,
        due_at=due_at,
        status=TaskStatus.todo,
        dedupe_key=dedupe_key,
        category=category,
        severity=severity,
    )
    db.add(task)
    db.flush()

    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if txn is None:
        raise ValueError(f"Transaction {transaction_id} not found")
    create_audit_event(
        db,
        org_id=txn.org_id,
        action="task.created",
        entity_type="task",
        entity_id=task.id,
        detail=f"Task '{title}' created",
    )
    if commit:
        db.commit()
        db.refresh(task)
    return task


def update_task_status(
    db: Session,
    *,
    task_id: uuid.UUID,
    new_status: str,
) -> Task:
    """
    Update the status of an existing task and record an audit event for the change.
    
    Parameters:
        task_id (uuid.UUID): ID of the task to update.
        new_status (str): New status value; must be one of the members of `TaskStatus`.
    
    Returns:
        task (Task): The updated Task instance.
    
    Raises:
        ValueError: If the task or its transaction cannot be found, or if `new_status` is not a valid `TaskStatus`.
    """
    from tc.db.models.transaction import Transaction

    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    try:
        validated_status = TaskStatus(new_status)
    except ValueError as exc:
        raise ValueError(f"Invalid task status: {new_status}") from exc

    old_status = task.status
    task.status = validated_status
    db.flush()

    txn = db.query(Transaction).filter(Transaction.id == task.transaction_id).first()
    if txn is None:
        raise ValueError(f"Transaction {task.transaction_id} not found")
    create_audit_event(
        db,
        org_id=txn.org_id,
        action="task.status_changed",
        entity_type="task",
        entity_id=task.id,
        detail=f"Status changed from '{old_status}' to '{new_status}'",
    )
    db.commit()
    db.refresh(task)
    return task


def assign_task(
    db: Session,
    *,
    task_id: uuid.UUID,
    assignee_id: uuid.UUID,
) -> Task:
    """
    Assign a task to a user and record an audit event.
    
    Updates the task's assignee, creates an audit event scoped to the task's transaction organization, commits the change, and returns the refreshed Task.
    
    Returns:
        task (Task): The updated Task instance.
    
    Raises:
        TaskNotFoundError: If no Task exists with the given `task_id`.
        TransactionNotFoundError: If the Task's associated transaction cannot be found.
    """
    from tc.db.models.transaction import Transaction

    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise TaskNotFoundError(f"Task {task_id} not found")

    task.assignee_id = assignee_id
    db.flush()

    txn = db.query(Transaction).filter(Transaction.id == task.transaction_id).first()
    if txn is None:
        raise TransactionNotFoundError(f"Transaction {task.transaction_id} not found")
    create_audit_event(
        db,
        org_id=txn.org_id,
        action="task.assigned",
        entity_type="task",
        entity_id=task.id,
        detail=f"Task assigned to user {assignee_id}",
    )
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: uuid.UUID) -> Task | None:
    """
    Retrieve the task with the given ID.
    
    Returns:
        `Task` if found, `None` otherwise.
    """
    return db.query(Task).filter(Task.id == task_id).first()


def list_tasks_by_transaction(db: Session, transaction_id: uuid.UUID) -> list[Task]:
    """
    List tasks for a transaction, ordered by due date.
    
    Returns:
        list[Task]: A list of Task instances associated with the given transaction, ordered by Task.due_at (earliest first).
    """
    return db.query(Task).filter(Task.transaction_id == transaction_id).order_by(Task.due_at).all()


def list_tasks_by_user(db: Session, user_id: uuid.UUID) -> list[Task]:
    """
    List all tasks assigned to a user within the organizations the user belongs to.
    
    Returns:
        list[Task]: Tasks assigned to `user_id` whose transactions belong to the user's organizations, ordered by `due_at`.
    """
    from tc.db.models.membership import Membership
    from tc.db.models.transaction import Transaction

    user_org_ids = db.query(Membership.org_id).filter(Membership.user_id == user_id).subquery()
    return (
        db.query(Task)
        .join(Transaction, Task.transaction_id == Transaction.id)
        .filter(Task.assignee_id == user_id, Transaction.org_id.in_(user_org_ids))
        .order_by(Task.due_at)
        .all()
    )
