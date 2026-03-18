from __future__ import annotations

import uuid

from tc.db.models.audit import AuditEvent


def test_list_org_audit(db, client, auth_header, seed_user):
    user, org = seed_user

    event1 = AuditEvent(
        org_id=org.id,
        action="task.created",
        entity_type="task",
        entity_id=uuid.uuid4(),
        actor_id=user.id,
        detail="Task 1 created"
    )
    event2 = AuditEvent(
        org_id=org.id,
        action="task.marked_overdue",
        entity_type="task",
        entity_id=uuid.uuid4(),
        actor_id=None,
        detail="Task 2 overdue"
    )
    db.add_all([event1, event2])
    db.commit()

    r = client.get(f"/api/v1/audit?org_id={str(org.id)}", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    actions = [item["action"] for item in data["items"]]
    assert "task.created" in actions
    assert "task.marked_overdue" in actions


def test_list_org_audit_filtering(db, client, auth_header, seed_user):
    user, org = seed_user

    event1 = AuditEvent(
        org_id=org.id,
        action="transaction.created",
        entity_type="transaction",
        entity_id=uuid.uuid4(),
        detail="Txn created"
    )
    event2 = AuditEvent(
        org_id=org.id,
        action="task.marked_overdue",
        entity_type="task",
        entity_id=uuid.uuid4(),
        detail="Task overdue"
    )
    db.add_all([event1, event2])
    db.commit()

    r = client.get(f"/api/v1/audit?org_id={str(org.id)}&entity_type=task", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "task.marked_overdue"

    r2 = client.get(f"/api/v1/audit?org_id={str(org.id)}&action=transaction.created", headers=auth_header)
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["entity_type"] == "transaction"


def test_list_org_audit_requires_admin(db, client, seed_user):
    from tc.core.security import create_access_token
    from tc.db.models.user import User
    from tc.db.models.membership import Membership

    user, org = seed_user

    # Create non-admin member
    member = User(
        id=uuid.uuid4(),
        email="member@test.local",
        full_name="Test Member",
        hashed_password="hashed_password",
    )
    db.add(member)
    db.flush()

    membership = Membership(id=uuid.uuid4(), org_id=org.id, user_id=member.id, role="member")
    db.add(membership)
    db.commit()

    token = create_access_token(subject=str(member.id))
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get(f"/api/v1/audit?org_id={str(org.id)}", headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "Role 'admin' required"
