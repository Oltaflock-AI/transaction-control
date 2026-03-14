from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from tc.core.security import require_role
from tc.db.models.membership import Membership
from tc.db.session import get_db
from tc.services.audit_service import list_audit_events_for_org

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_role("admin"))],
)

DB = Annotated[Session, Depends(get_db)]


@router.get("")
def list_org_audit(
    db: DB,
    user=Depends(require_role("admin")),
    entity_type: str | None = Query(None, description="Filter by entity type, e.g. 'task'"),
    action: str | None = Query(None, description="Filter by action, e.g. 'task.marked_overdue'"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Org-wide audit feed — all events across all deals for the user's org."""
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user.id, Membership.role == "admin")
        .first()
    )

    events, total = list_audit_events_for_org(
        db,
        org_id=membership.org_id,
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
