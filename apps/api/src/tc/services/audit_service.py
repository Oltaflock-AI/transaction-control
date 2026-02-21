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


def list_audit_events_for_transaction(
    db: Session, transaction_id: uuid.UUID
) -> list[AuditEvent]:
    """Return audit events whose entity is the transaction or any of its tasks."""
    from tc.db.models.task import Task

    task_ids = [
        row[0]
        for row in db.query(Task.id).filter(Task.transaction_id == transaction_id).all()
    ]

    entity_ids = [transaction_id, *task_ids]
    return (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_id.in_(entity_ids))
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
