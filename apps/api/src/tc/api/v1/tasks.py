from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from tc.core.security import CurrentUser
from tc.db.session import get_db
from tc.services.task_service import (
    assign_task,
    create_task,
    get_task,
    list_tasks_by_user,
    update_task_status,
)
from tc.services.transaction_service import get_transaction, user_belongs_to_org

router = APIRouter(tags=["tasks"])

DB = Annotated[Session, Depends(get_db)]


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    due_at: datetime | None = None


class TaskStatusUpdate(BaseModel):
    status: str


class TaskAssign(BaseModel):
    assignee_id: uuid.UUID


def _task_to_dict(task):
    return {
        "id": str(task.id),
        "transaction_id": str(task.transaction_id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "assignee_id": str(task.assignee_id) if task.assignee_id else None,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def _check_task_org_access(db: Session, user, task_id: uuid.UUID):
    """Look up a task and verify the user belongs to the transaction's org."""
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    txn = get_transaction(db, task.transaction_id)
    if txn is None or not user_belongs_to_org(db, user.id, txn.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organisation",
        )
    return task


@router.post(
    "/transactions/{transaction_id}/tasks",
    status_code=status.HTTP_201_CREATED,
)
def create_task_endpoint(transaction_id: uuid.UUID, body: TaskCreate, user: CurrentUser, db: DB):
    """Create a task on a transaction."""
    txn = get_transaction(db, transaction_id)
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    if not user_belongs_to_org(db, user.id, txn.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organisation",
        )
    if body.assignee_id is not None and not user_belongs_to_org(db, body.assignee_id, txn.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assignee must be a member of the organisation",
        )

    task = create_task(
        db,
        transaction_id=transaction_id,
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
        due_at=body.due_at,
    )
    return _task_to_dict(task)


@router.get("/tasks/mine")
def my_tasks(user: CurrentUser, db: DB):
    """List all tasks assigned to the current user across all orgs."""
    tasks = list_tasks_by_user(db, user.id)
    return [_task_to_dict(t) for t in tasks]


@router.patch("/tasks/{task_id}/status")
def update_status(task_id: uuid.UUID, body: TaskStatusUpdate, user: CurrentUser, db: DB):
    """Update the status of a task."""
    _check_task_org_access(db, user, task_id)

    try:
        task = update_task_status(db, task_id=task_id, new_status=body.status)
    except ValueError as exc:
        msg = str(exc)
        if "Invalid task status" in msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc

    return _task_to_dict(task)


@router.patch("/tasks/{task_id}/assign")
def assign(task_id: uuid.UUID, body: TaskAssign, user: CurrentUser, db: DB):
    """Assign a task to a user."""
    task = _check_task_org_access(db, user, task_id)
    txn = get_transaction(db, task.transaction_id)
    if txn is not None and not user_belongs_to_org(db, body.assignee_id, txn.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assignee must be a member of the organisation",
        )

    try:
        task = assign_task(db, task_id=task_id, assignee_id=body.assignee_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _task_to_dict(task)


@router.get("/transactions/{transaction_id}/health")
def health(transaction_id: uuid.UUID, user: CurrentUser, db: DB):
    """Return the health score (GREEN/YELLOW/RED) for a transaction."""
    from tc.services.health_service import compute_health_score

    txn = get_transaction(db, transaction_id)
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    if not user_belongs_to_org(db, user.id, txn.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organisation",
        )
    return compute_health_score(db, transaction_id)
