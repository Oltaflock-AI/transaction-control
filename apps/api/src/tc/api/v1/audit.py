from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tc.core.security import AdminUser, require_role
from tc.db.models.membership import Membership
from tc.db.session import get_db
from tc.services.audit_service import list_audit_events_for_org

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_role("admin"))],
)

DB = Annotated[Session, Depends(get_db)]

MAX_PAGE_SIZE = 100


@router.get("")
def list_org_audit(
    org_id: uuid.UUID,
    db: DB,
    user: AdminUser,
    entity_type: str | None = None,
    action: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """Org-wide audit feed — all events across all deals for the user's org."""
    if page < 1:
        raise HTTPException(status_code=400, detail=f"page must be >= 1, got {page}")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"page_size must be between 1 and {MAX_PAGE_SIZE}, got {page_size}",
        )

    membership = (
        db.query(Membership)
        .filter(
            Membership.user_id == user.id,
            Membership.role == "admin",
            Membership.org_id == org_id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Not an admin of this organisation")

    events, total = list_audit_events_for_org(
        db,
        org_id=org_id,
        entity_type=entity_type,
        action=action,
        page=page,
        page_size=page_size,
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [
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
        ],
    }
