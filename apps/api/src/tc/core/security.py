from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from tc.core.config import settings
from tc.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def create_access_token(subject: str, extra: dict | None = None) -> str:
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALG],
        options={"verify_exp": True},
    )


_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def require_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """FastAPI dependency — resolves the current authenticated user from the JWT."""
    from tc.db.models.user import User

    try:
        payload = decode_access_token(token)
        raw_sub: str | None = payload.get("sub")
        if raw_sub is None:
            raise _credentials_exc
        user_id = _uuid.UUID(raw_sub)
    except (JWTError, ValueError):
        raise _credentials_exc from None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise _credentials_exc
    return user


def require_role(role: str):
    """Factory that returns a FastAPI dependency requiring a specific membership role."""

    async def _check(
        user: Annotated[object, Depends(require_user)],
        db: Annotated[Session, Depends(get_db)],
    ):
        from tc.db.models.membership import Membership

        has_role = (
            db.query(Membership)
            .filter(Membership.user_id == user.id, Membership.role == role)
            .first()
        )
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user

    return _check


CurrentUser = Annotated[object, Depends(require_user)]
AdminUser = Annotated[object, Depends(require_role("admin"))]
