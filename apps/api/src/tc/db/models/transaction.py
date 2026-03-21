from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tc.db.base import Base

if TYPE_CHECKING:
    from tc.db.models.task import Task
    from tc.db.models.timeline import TimelineItem


class TransactionStatus(StrEnum):
    draft = "draft"
    active = "active"
    closed = "closed"
    cancelled = "cancelled"


class Transaction(Base):
    __tablename__ = "transactions"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(20), default=TransactionStatus.draft)
    property_address: Mapped[str | None] = mapped_column(String(500), default=None)
    close_date: Mapped[date | None] = mapped_column(Date, default=None)

    tasks: Mapped[list[Task]] = relationship(back_populates="transaction")
    timeline_items: Mapped[list[TimelineItem]] = relationship(back_populates="transaction")
