from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from tc.core.security import CurrentUser
from tc.db.models.membership import Membership
from tc.db.session import get_db
from tc.domain.enums import UserRole
from tc.services.user_service import UserAlreadyExistsError, create_user_in_org, list_users_in_org

router = APIRouter(prefix="/users", tags=["users"])

DB = Annotated[Session, Depends(get_db)]


class UserCreateRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole


@router.get("")
def list_org_users(user: CurrentUser, db: DB):
    """List users in the current user's org. For simplicity, takes first org of the user."""
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of any organization")

    users_roles = list_users_in_org(db, membership.org_id)

    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": role,
            "is_active": u.is_active,
        }
        for u, role in users_roles
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_org_user(body: UserCreateRequest, user: CurrentUser, db: DB):
    """Create a new user in the current user's org."""
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of any organization")

    if membership.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can create users")

    if body.role not in (UserRole.buyerAgent, UserRole.sellerAgent):
        raise HTTPException(
            status_code=400,
            detail="Only buyerAgent and sellerAgent roles can be assigned dynamically.",
        )

    try:
        new_user = create_user_in_org(
            db,
            org_id=membership.org_id,
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            role=body.role,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None

    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": body.role,
    }
