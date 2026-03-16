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
    """
    List audit events for an organization with optional filters and pagination.
    
    Parameters:
        org_id (uuid.UUID): UUID of the organization to list audit events for.
        entity_type (str | None): If provided, restrict results to this entity type.
        action (str | None): If provided, restrict results to this action name.
        page (int): Page number for pagination (1-based).
        page_size (int): Number of items per page.
    
    Returns:
        dict: A page object containing:
            - page (int): The requested page number.
            - page_size (int): The requested page size.
            - total (int): Total number of matching events.
            - items (list): List of event dictionaries, each with:
                - id (str)
                - action (str)
                - entity_type (str)
                - entity_id (str | None)
                - actor_id (str | None)
                - detail (str)
                - created_at (str | None): ISO 8601 formatted timestamp or None.
    
    Raises:
        HTTPException: 403 if the requesting user is not an admin of the organization.
    """
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
