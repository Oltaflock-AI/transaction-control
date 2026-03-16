from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from tc.db.models.event_log import EventLog


def list_event_logs_for_transaction(
    db: Session,
    transaction_id: uuid.UUID,
    *,
    event_type: str | None = None,
) -> list[EventLog]:
    """Return event logs for a transaction with optional event_type filter."""
    query = db.query(EventLog).filter(EventLog.transaction_id == transaction_id)

    if event_type:
        query = query.filter(EventLog.event_type == event_type)

    return query.order_by(EventLog.created_at.desc(), EventLog.id.desc()).all()
