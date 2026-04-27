from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tc.core.security import CurrentUser
from tc.db.models.membership import Membership
from tc.db.models.transaction import Transaction
from tc.db.session import get_db
from tc.domain.enums import UserRole
from tc.services.dashboard_service import get_admin_dashboard, get_agent_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DB = Annotated[Session, Depends(get_db)]


def _serialize_risk(t: Transaction) -> dict:
    return {
        "id": str(t.id),
        "org_id": str(t.org_id),
        "title": t.title,
        "status": t.status,
        "property_address": t.property_address,
        "health_score": t.health_score,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


@router.get("/stats")
def get_dashboard_stats(user: CurrentUser, db: DB):
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of any organization")

    if membership.role == UserRole.admin:
        total_txns, tasks_overdue, tasks_due_soon, deals_at_risk = get_admin_dashboard(
            db, membership.org_id
        )
    else:
        total_txns, tasks_overdue, tasks_due_soon, deals_at_risk = get_agent_dashboard(
            db, user.id, membership.org_id
        )

    return {
        "total_transactions": total_txns,
        "tasks_overdue": tasks_overdue,
        "tasks_due_soon": tasks_due_soon,
        "deals_at_risk": [_serialize_risk(t) for t in deals_at_risk],
    }
