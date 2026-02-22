from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tc.core.security import AdminUser
from tc.db.session import get_db
from tc.services.deadline_service import check_deadlines

router = APIRouter(prefix="/admin", tags=["admin"])

DB = Annotated[Session, Depends(get_db)]


@router.post("/check-deadlines")
def run_check_deadlines(_user: AdminUser, db: DB):
    """Run the deadline checker on demand. Admin only."""
    return check_deadlines(db)
