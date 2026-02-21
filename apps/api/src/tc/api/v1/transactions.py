from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tc.core.security import CurrentUser
from tc.db.models.membership import Membership
from tc.db.models.transaction import Transaction
from tc.db.session import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/")
def list_transactions(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Return transactions belonging to organisations the caller is a member of."""
    org_ids = [
        m.org_id
        for m in db.query(Membership.org_id).filter(Membership.user_id == user.id).all()
    ]
    txns = db.query(Transaction).filter(Transaction.org_id.in_(org_ids)).all()
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "status": t.status,
            "org_id": str(t.org_id),
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txns
    ]
