from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from tc.db.models.audit import AuditEvent


def create_audit_event(
    db: Session,
    *,
    org_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    detail: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        org_id=org_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(event)
    db.flush()
    return event


def list_audit_events_for_transaction(db: Session, transaction_id: uuid.UUID) -> list[AuditEvent]:
    """
    List audit events for a transaction and any tasks belonging to that transaction.
    
    Returns:
        A list of AuditEvent objects whose `entity_id` is the transaction ID or any task ID for that transaction, ordered by `created_at` descending.
    """
    from tc.db.models.task import Task

    task_ids = [
        row[0] for row in db.query(Task.id).filter(Task.transaction_id == transaction_id).all()
    ]

    entity_ids = [transaction_id, *task_ids]
    return (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_id.in_(entity_ids))
        .order_by(AuditEvent.created_at.desc())
        .all()
    )


def list_audit_events_for_org(
    db: Session,
    org_id: uuid.UUID,
    *,
    entity_type: str | None = None,
    action: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditEvent], int]:
    """
    Retrieve a paginated list of audit events for an organization with optional filtering.
    
    The results are ordered by `created_at` descending, with `id` used as a tiebreaker.
    
    Parameters:
        db (Session): Database session (omitted from generator docs but kept for call clarity).
        org_id (uuid.UUID): Organization identifier to scope the events.
        entity_type (str | None): If provided, only include events for this entity type.
        action (str | None): If provided, only include events with this action.
        page (int): 1-based page number to retrieve.
        page_size (int): Number of events per page.
    
    Returns:
        tuple[list[AuditEvent], int]: A tuple where the first element is the list of `AuditEvent`
        objects for the requested page and filters, and the second element is the total number
        of events that match the filters.
    """
    query = db.query(AuditEvent).filter(AuditEvent.org_id == org_id)

    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if action:
        query = query.filter(AuditEvent.action == action)

    total = query.count()

    events = (
        query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return events, total
