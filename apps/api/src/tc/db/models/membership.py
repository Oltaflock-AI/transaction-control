from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tc.db.base import Base

if TYPE_CHECKING:
    from tc.db.models.org import Org
    from tc.db.models.user import User


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("org_id", "user_id"),)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(50), default="member")

    org: Mapped[Org] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")
