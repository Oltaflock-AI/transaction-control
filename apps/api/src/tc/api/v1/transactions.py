from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from tc.core.security import CurrentUser
from tc.db.session import get_db
from tc.services.audit_service import list_audit_events_for_transaction
from tc.services.transaction_service import (
    create_transaction,
    get_transaction,
    list_user_transactions,
    user_belongs_to_org,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])

DB = Annotated[Session, Depends(get_db)]


# -- Schemas ------------------------------------------------------------------


class TransactionCreate(BaseModel):
    org_id: uuid.UUID
    title: str
    description: str | None = None
    property_address: str | None = None
    close_date: date | None = None


# -- Helpers ------------------------------------------------------------------


def _txn_to_dict(t, *, include_tasks: bool = False):
    """
    Convert a transaction-like object into a serializable dictionary for API responses.
    
    Parameters:
        t: Transaction-like object with attributes `id`, `org_id`, `title`, `description`,
           `status`, optional `health_score`, `property_address`, `close_date`, `created_at`,
           and iterable `tasks` when tasks are present. UUIDs are stringified.
        include_tasks (bool): If True, include the transaction's tasks under the `tasks` key.
    
    Returns:
        dict: A dictionary with keys:
          - id (str): Transaction UUID as a string.
          - org_id (str): Organization UUID as a string.
          - title (str)
          - description (str | None)
          - status (str)
          - health_score (str): Uses the object's `health_score` if present, otherwise "GREEN".
          - property_address (str | None)
          - close_date (str | None): ISO-formatted date or None.
          - created_at (str | None): ISO-formatted datetime or None.
          - tasks (list[dict], optional): Present only if `include_tasks` is True. Each task dict contains:
              - id (str)
              - title (str)
              - offset_days (int)
              - description (str | None)
              - category (str | None)
              - status (str)
              - due_at (str | None): ISO-formatted date or None.
    """
    out = {
        "id": str(t.id),
        "org_id": str(t.org_id),
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "health_score": getattr(t, "health_score", "GREEN"),
        "property_address": t.property_address,
        "close_date": t.close_date.isoformat() if t.close_date else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }
    if include_tasks:
        out["tasks"] = [
            {
                "id": str(task.id),
                "title": task.title,
                "offset_days": task.offset_days,
                "description": task.description,
                "category": task.category,
                "status": task.status,
                "due_at": task.due_at.isoformat() if task.due_at else None,
            }
            for task in t.tasks
        ]
    return out


# -- Endpoints ----------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def create(body: TransactionCreate, user: CurrentUser, db: DB):
    if not user_belongs_to_org(db, user.id, body.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organisation",
        )

    txn = create_transaction(
        db,
        org_id=body.org_id,
        title=body.title,
        description=body.description,
        property_address=body.property_address,
        close_date=body.close_date,
    )

    from tc.workers.tasks import generate_timeline

    generate_timeline.delay(str(txn.id))

    return _txn_to_dict(txn)


@router.get("/{transaction_id}")
def get_by_id(transaction_id: uuid.UUID, user: CurrentUser, db: DB):
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
    return _txn_to_dict(txn, include_tasks=True)


@router.get("/{transaction_id}/tasks")
def get_tasks(transaction_id: uuid.UUID, user: CurrentUser, db: DB):
    """List tasks belonging to a transaction."""
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
    return [
        {
            "id": str(task.id),
            "transaction_id": str(task.transaction_id),
            "title": task.title,
            "status": task.status,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "assignee_id": str(task.assignee_id) if task.assignee_id else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
        for task in txn.tasks
    ]


@router.get("")
def list_all(user: CurrentUser, db: DB):
    txns = list_user_transactions(db, user.id)
    return [_txn_to_dict(t) for t in txns]


@router.get("/{transaction_id}/audit")
def get_audit(transaction_id: uuid.UUID, user: CurrentUser, db: DB):
    """
    Retrieve the audit events for a transaction and its tasks.
    
    Parameters:
        transaction_id (uuid.UUID): ID of the transaction to fetch audit events for.
    
    Returns:
        List[dict]: A list of audit event objects with keys:
            - id (str): Event UUID as a string.
            - action (str): Action performed.
            - entity_type (str): Type of the entity affected.
            - entity_id (str | None): ID of the affected entity, or None.
            - actor_id (str | None): ID of the actor who performed the action, or None.
            - detail (str | None): Additional event details.
            - created_at (str | None): ISO-8601 timestamp of when the event was created, or None.
    
    Raises:
        HTTPException: 404 if the transaction does not exist.
        HTTPException: 403 if the current user is not a member of the transaction's organization.
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
    events = list_audit_events_for_transaction(db, transaction_id)
    return [
        {
            "id": str(e.id),
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": str(e.entity_id) if e.entity_id else None,
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "detail": e.detail,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/{transaction_id}/events")
def get_events(
    transaction_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    event_type: str | None = None,
):
    """
    Return event logs for the specified transaction, optionally filtered by event type.
    
    Parameters:
        transaction_id (uuid.UUID): ID of the transaction to fetch logs for.
        event_type (str | None): If provided, only include logs with this event type.
    
    Returns:
        list[dict]: A list of event log objects with keys:
            - id (str)
            - transaction_id (str)
            - event_type (str)
            - entity_type (str)
            - entity_id (str | None)
            - detail (str)
            - created_at (str | None): ISO 8601 timestamp or None
    
    Raises:
        HTTPException: 404 if the transaction is not found.
        HTTPException: 403 if the current user is not a member of the transaction's organisation.
    """
    from tc.services.event_log_service import list_event_logs_for_transaction

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
    logs = list_event_logs_for_transaction(db, transaction_id, event_type=event_type)
    return [
        {
            "id": str(log.id),
            "transaction_id": str(log.transaction_id),
            "event_type": log.event_type,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "detail": log.detail,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
