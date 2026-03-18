from __future__ import annotations

import uuid

from tc.db.models.transaction import Transaction
from tc.db.models.event_log import EventLog


def test_list_events_for_transaction(db, client, auth_header, seed_user):
    user, org = seed_user

    txn = Transaction(
        id=uuid.uuid4(),
        org_id=org.id,
        title="123 Test St",
        status="active",
        health_score="GREEN"
    )
    db.add(txn)
    
    event1 = EventLog(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        event_type="task.overdue",
        entity_type="task",
        entity_id=uuid.uuid4(),
        detail="{}",
    )
    event2 = EventLog(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        event_type="task.due_soon",
        entity_type="task",
        entity_id=uuid.uuid4(),
        detail="{}",
    )
    db.add_all([event1, event2])
    db.commit()

    r = client.get(f"/api/v1/transactions/{txn.id}/events", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    event_types = [log["event_type"] for log in data]
    assert "task.overdue" in event_types
    assert "task.due_soon" in event_types


def test_list_events_for_transaction_filtered(db, client, auth_header, seed_user):
    user, org = seed_user

    txn = Transaction(
        id=uuid.uuid4(),
        org_id=org.id,
        title="123 Test St",
        status="active",
        health_score="GREEN"
    )
    db.add(txn)
    
    event1 = EventLog(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        event_type="task.overdue",
        entity_type="task",
        entity_id=uuid.uuid4(),
        detail="{}",
    )
    db.add(event1)
    db.commit()

    r = client.get(f"/api/v1/transactions/{txn.id}/events?event_type=task.overdue", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "task.overdue"

    r2 = client.get(f"/api/v1/transactions/{txn.id}/events?event_type=task.due_soon", headers=auth_header)
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2) == 0


def test_list_events_unauthorized(db, client, seed_user):
    user, org = seed_user

    # Create org2
    from tc.db.models.org import Org
    org2 = Org(id=uuid.uuid4(), name="Other Org", slug="other-org")
    db.add(org2)
    
    txn2 = Transaction(
        id=uuid.uuid4(),
        org_id=org2.id,
        title="456 Other St",
        status="active",
        health_score="GREEN"
    )
    db.add(txn2)
    db.commit()

    from tc.core.security import create_access_token
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get(f"/api/v1/transactions/{txn2.id}/events", headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "Not a member of this organisation"
