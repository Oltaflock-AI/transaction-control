from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tc.db.base import Base

if TYPE_CHECKING:
    from tc.db.models.membership import Membership


class Org(Base):
    __tablename__ = "orgs"

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    memberships: Mapped[list[Membership]] = relationship(back_populates="org")
