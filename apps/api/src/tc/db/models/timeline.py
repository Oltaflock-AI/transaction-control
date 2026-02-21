from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tc.db.base import Base

if TYPE_CHECKING:
    from tc.db.models.transaction import Transaction


class TimelineItem(Base):
    __tablename__ = "timeline_items"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id"), index=True
    )
    label: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    transaction: Mapped[Transaction] = relationship(back_populates="timeline_items")
