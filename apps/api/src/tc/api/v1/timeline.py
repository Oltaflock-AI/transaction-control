import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tc.core.security import CurrentUser, require_user
from tc.db.models.timeline import TimelineItem
from tc.db.session import get_db
from tc.services import timeline_service, transaction_service

DB = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/timeline", tags=["timeline"], dependencies=[Depends(require_user)])


@router.get("/transactions/{transaction_id}")
def list_timeline_items(transaction_id: uuid.UUID, user: CurrentUser, db: DB):
    """
    fetch specific transaction timeline items.
    """
    # Org membership check
    if not transaction_service.user_has_access_to_transaction(db, user.id, transaction_id):
        raise HTTPException(status_code=403, detail="Not a member of this organisation")

    return timeline_service.get_timeline_items(db, transaction_id)


@router.patch("/{item_id}/complete")
def complete_timeline_item(item_id: uuid.UUID, user: CurrentUser, db: DB):
    """
    mark a timeline item as complete.
    """
    item = db.query(TimelineItem).filter(TimelineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Timeline item not found")

    # Org membership check
    if not transaction_service.user_has_access_to_transaction(db, user.id, item.transaction_id):
        raise HTTPException(status_code=403, detail="Not a member of this organisation")

    return timeline_service.mark_item_complete(db, item_id)
