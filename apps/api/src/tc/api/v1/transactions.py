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
    out = {
        "id": str(t.id),
        "org_id": str(t.org_id),
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "property_address": t.property_address,
        "close_date": t.close_date.isoformat() if t.close_date else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }
    if include_tasks:
        out["tasks"] = [
            {
                "id": str(task.id),
                "title": task.title,
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
    """Audit trail for a transaction and its tasks."""
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
