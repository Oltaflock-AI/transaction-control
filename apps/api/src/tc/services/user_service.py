from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from tc.core.security import hash_password
from tc.db.models.membership import Membership
from tc.db.models.user import User


class UserAlreadyExistsError(ValueError):
    """Raised when trying to create a user that already exists."""


def create_user_in_org(
    db: Session,
    *,
    org_id: uuid.UUID,
    email: str,
    full_name: str,
    password: str,
    role: str,
) -> User:
    """Create a new user and add them to the organization with a specific role."""
    user = db.query(User).filter(User.email == email).first()

    if user:
        # Check if already in org
        membership = (
            db.query(Membership)
            .filter(Membership.org_id == org_id, Membership.user_id == user.id)
            .first()
        )
        if not membership:
            membership = Membership(org_id=org_id, user_id=user.id, role=role)
            db.add(membership)
            db.commit()
            db.refresh(user)
            return user
        else:
            raise UserAlreadyExistsError(f"User with email {email} is already in the organization.")

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    membership = Membership(
        org_id=org_id,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


def list_users_in_org(db: Session, org_id: uuid.UUID) -> list[tuple[User, str]]:
    """Return all users in an org, along with their roles."""
    results = (
        db.query(User, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .filter(Membership.org_id == org_id)
        .order_by(User.full_name)
        .all()
    )
    return results
