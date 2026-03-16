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
    """
    Retrieve event logs for a given transaction, optionally filtered by event type.
    
    Results are ordered by `created_at` in descending order (newest first).
    
    Parameters:
        event_type (str | None): Event type to filter by; if `None`, no event-type filtering is applied.
    
    Returns:
        list[EventLog]: EventLog objects matching the transaction (and `event_type` if provided), ordered newest first.
    """
    query = db.query(EventLog).filter(EventLog.transaction_id == transaction_id)

    if event_type:
        query = query.filter(EventLog.event_type == event_type)

    return query.order_by(EventLog.created_at.desc()).all()
