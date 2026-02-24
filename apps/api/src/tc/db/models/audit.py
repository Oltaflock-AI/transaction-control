from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from tc.db.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id"), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), default=None, index=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(default=None)
    detail: Mapped[str | None] = mapped_column(Text, default=None)
