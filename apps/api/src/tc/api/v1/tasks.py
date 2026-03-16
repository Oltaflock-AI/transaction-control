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


class TaskStatusUpdate(BaseModel):
    status: str


class TaskAssign(BaseModel):
    assignee_id: uuid.UUID


def _task_to_dict(task):
    """
    Serialize a task ORM object into a JSON-serializable dictionary suitable for API responses.
    
    Parameters:
        task: ORM task object with attributes `id`, `transaction_id`, `title`, `description`, `status`,
              `assignee_id`, `due_at`, and `created_at`.
    
    Returns:
        dict: A dictionary with keys:
            - `id`: string UUID of the task.
            - `transaction_id`: string UUID of the related transaction.
            - `title`: task title.
            - `description`: task description or None.
            - `status`: task status.
            - `assignee_id`: string UUID of the assignee or None.
            - `due_at`: ISO 8601 string of the due date/time or None.
            - `created_at`: ISO 8601 string of the creation date/time or None.
    """
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
    """
    Lookup a task by ID and ensure the given user is a member of the task's transaction organisation.
    
    Parameters:
        db (Session): Database session.
        user: CurrentUser-like object representing the requesting user.
        task_id (uuid.UUID): ID of the task to check.
    
    Returns:
        The task ORM object when access is valid.
    
    Raises:
        HTTPException: 404 if the task does not exist.
        HTTPException: 403 if the user is not a member of the transaction's organisation.
    """
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
    """
    Create a new task for the given transaction.
    
    Returns:
        dict: Serialized task object created for the transaction.
    
    Raises:
        HTTPException: 404 if the transaction does not exist.
        HTTPException: 403 if the current user is not a member of the transaction's organisation.
        HTTPException: 403 if an assignee_id is provided but the assignee is not a member of the organisation.
    """
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
    """
    List tasks assigned to the current user across all organizations.
    
    Returns:
        list[dict]: Serialized task dictionaries with keys `id`, `transaction_id`, `title`, `description`, `status`, `assignee_id`, `due_at`, and `created_at`.
    """
    tasks = list_tasks_by_user(db, user.id)
    return [_task_to_dict(t) for t in tasks]


@router.patch("/tasks/{task_id}/status")
def update_status(task_id: uuid.UUID, body: TaskStatusUpdate, user: CurrentUser, db: DB):
    """
    Update a task's status.
    
    Returns:
        dict: The updated task represented as a dictionary with keys
            `id`, `transaction_id`, `title`, `description`, `status`,
            `assignee_id`, `due_at`, and `created_at`.
    
    Raises:
        HTTPException: 400 if the provided status value is invalid.
        HTTPException: 404 if the task or related resource cannot be found.
    """
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

    except ValueError as exc:
        msg = str(exc)
        if "Invalid task status" in msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc

    return _task_to_dict(task)


@router.patch("/tasks/{task_id}/assign")
def assign(task_id: uuid.UUID, body: TaskAssign, user: CurrentUser, db: DB):
    """
    Assign the specified task to the provided assignee.
    
    Parameters:
        task_id (uuid.UUID): ID of the task to assign.
        body (TaskAssign): Payload containing `assignee_id`.
    
    Returns:
        dict: Serialized representation of the updated task.
    
    Raises:
        HTTPException: 404 if the task cannot be found.
        HTTPException: 403 if the assignee is not a member of the transaction's organisation.
        HTTPException: 409 if the transaction no longer exists (conflict).
        HTTPException: 500 if the related transaction cannot be loaded.
    """
    task = _check_task_org_access(db, user, task_id)
    txn = get_transaction(db, task.transaction_id)
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction no longer exists; please retry",
        )
    if not user_belongs_to_org(db, body.assignee_id, txn.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
    """
    Get the health score (GREEN, YELLOW, or RED) for a transaction.
    
    Raises:
        HTTPException: 404 if the transaction does not exist.
        HTTPException: 403 if the requesting user is not a member of the transaction's organisation.
    
    Returns:
        str: 'GREEN', 'YELLOW', or 'RED' indicating the transaction's health.
    """
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
