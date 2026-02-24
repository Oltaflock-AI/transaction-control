from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from tc.db.models.membership import Membership
from tc.db.models.transaction import Transaction, TransactionStatus


def create_transaction(
    db: Session,
    *,
    org_id: uuid.UUID,
    title: str,
    description: str | None = None,
    property_address: str | None = None,
    close_date: date | None = None,
) -> Transaction:
    txn = Transaction(
        org_id=org_id,
        title=title,
        description=description,
        property_address=property_address,
        close_date=close_date,
        status=TransactionStatus.draft,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def get_transaction(db: Session, transaction_id: uuid.UUID) -> Transaction | None:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def list_user_transactions(db: Session, user_id: uuid.UUID) -> list[Transaction]:
    org_ids = [
        m.org_id for m in db.query(Membership.org_id).filter(Membership.user_id == user_id).all()
    ]
    if not org_ids:
        return []
    return db.query(Transaction).filter(Transaction.org_id.in_(org_ids)).all()


def user_belongs_to_org(db: Session, user_id: uuid.UUID, org_id: uuid.UUID) -> bool:
    return (
        db.query(Membership)
        .filter(Membership.user_id == user_id, Membership.org_id == org_id)
        .first()
        is not None
    )
