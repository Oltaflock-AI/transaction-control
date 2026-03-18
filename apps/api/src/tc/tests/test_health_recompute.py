from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from tc.db.models.task import Task
from tc.db.models.transaction import Transaction


def test_health_recompute_on_task_status_change(db, client, auth_header, seed_user):
    user, org = seed_user
    
    txn = Transaction(
        id=uuid.uuid4(),
        org_id=org.id,
        title="Health Recompute Txn",
        status="active",
        health_score="GREEN"
    )
    db.add(txn)
    
    # Task already overdue
    task1 = Task(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        title="Overdue Task",
        status="todo",
        due_at=datetime.now(UTC) - timedelta(days=1),
        severity="critical",
    )
    db.add(task1)
    db.commit()

    # Trigger deadlines to mark task1 overdue and set RED health
    client.post("/api/v1/admin/check-deadlines", headers=auth_header)
    
    r = client.get(f"/api/v1/transactions/{txn.id}/health", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["score"] == "RED"

    # Now manually change task1 status to done. Health should recompute to GREEN.
    patch_rsp = client.patch(
        f"/api/v1/tasks/{task1.id}/status",
        json={"status": "done"},
        headers=auth_header,
    )
    assert patch_rsp.status_code == 200
    
    # Verify health score is updated on transaction
    r_txn = client.get(f"/api/v1/transactions/{txn.id}", headers=auth_header)
    assert r_txn.status_code == 200
    assert r_txn.json()["health_score"] == "GREEN"

    # Verify health endpoint returns GREEN
    r_health = client.get(f"/api/v1/transactions/{txn.id}/health", headers=auth_header)
    assert r_health.json()["score"] == "GREEN"
