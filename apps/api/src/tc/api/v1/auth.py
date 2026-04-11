from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from tc.core.config import settings
from tc.core.security import create_access_token
from tc.db.models.user import User
from tc.db.models.membership import Membership
from tc.db.session import get_db
from tc.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

DB = Annotated[Session, Depends(get_db)]


class LoginRequest(BaseModel):
    email: str
    password: str


class DevTokenRequest(BaseModel):
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DB):
    user = authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    role = membership.role if membership else "member"
    
    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": role,
            "is_active": user.is_active,
        }
    )


@router.post("/dev-token", response_model=TokenResponse)
def dev_token(body: DevTokenRequest, db: DB):
    """Issue a JWT without a password — only available in local/test environments."""
    if settings.APP_ENV not in ("local", "test"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user = db.query(User).filter(User.email == body.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    role = membership.role if membership else "member"

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": role,
            "is_active": user.is_active,
        }
    )
