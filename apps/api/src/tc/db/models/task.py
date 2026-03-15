from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tc.db.base import Base
from tc.domain.enums import TaskStatus

if TYPE_CHECKING:
    from tc.db.models.transaction import Transaction


class Task(Base):
    __tablename__ = "tasks"

    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.todo)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), default=None, index=True
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    offset_days: Mapped[int | None] = mapped_column(Integer, default=None)
    category: Mapped[str | None] = mapped_column(String(100), default=None)
    severity: Mapped[str | None] = mapped_column(String(20), default=None)
    dedupe_key: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, default=None
    )

    transaction: Mapped[Transaction] = relationship(back_populates="tasks")
