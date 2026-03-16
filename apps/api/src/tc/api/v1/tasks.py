from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from tc.core.security import CurrentUser
from tc.db.session import get_db
from tc.services.task_service import (
    TaskNotFoundError,
    TransactionNotFoundError,
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

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, v: datetime | None) -> datetime | None:
        if v is not None:
            if v.tzinfo is None:
                return v.astimezone(timezone.utc)
        return v


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
    return task


from tc.db.models.user import User

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
    if body.assignee_id is not None:
        assignee = db.get(User, body.assignee_id)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found",
            )
        if not user_belongs_to_org(db, body.assignee_id, txn.org_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of the organisation",
            )

    try:
        task = create_task(
            db,
            transaction_id=transaction_id,
            title=body.title,
            description=body.description,
            assignee_id=body.assignee_id,
            due_at=body.due_at,
        )
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        ) from exc
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

        # Recompute health score and save it to the transaction
        from tc.services.health_service import compute_health_score

        health = compute_health_score(db, task.transaction_id)

        txn = get_transaction(db, task.transaction_id)
        if txn:
            txn.health_score = health["score"]
            db.commit()
            db.refresh(txn)

    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _task_to_dict(task)


@router.patch("/tasks/{task_id}/assign")
def assign(task_id: uuid.UUID, body: TaskAssign, user: CurrentUser, db: DB):
    """Assign a task to a user."""
    task = _check_task_org_access(db, user, task_id)
    txn = get_transaction(db, task.transaction_id)
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction no longer exists; please retry",
        )
    assignee = db.get(User, body.assignee_id)
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found",
        )
    if not user_belongs_to_org(db, body.assignee_id, txn.org_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a member of the organisation",
        )

    try:
        task = assign_task(db, task_id=task_id, assignee_id=body.assignee_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction no longer exists; please retry",
        ) from exc

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
