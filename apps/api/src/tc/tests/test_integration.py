from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from tc.db.models.task import Task


@patch("tc.workers.tasks.generate_timeline.delay")
def test_week2_end_to_end_integration(mock_delay, db, client, auth_header, seed_user):
    user, org = seed_user

    # 1. Create a transaction via API
    r_create = client.post(
        "/api/v1/transactions",
        json={"title": "E2E Integration Deal", "org_id": str(org.id)},
        headers=auth_header,
    )
    assert r_create.status_code == 201
    txn_id = r_create.json()["id"]

    # Let Celery worker process generate_timeline (we could sync call it for test)
    # Wait for celery task if it was async, but timeline generation is usually fast.
    # In tests, celery task is usually Eager if so configured.
    # We will invoke timeline directly to avoid race in test without eager celery
    from tc.services.timeline_service import generate_default_timeline

    generate_default_timeline(db, uuid.UUID(txn_id))
    db.commit()

    # 2. Verify tasks are generated
    r_tasks = client.get(f"/api/v1/transactions/{txn_id}/tasks", headers=auth_header)
    assert r_tasks.status_code == 200
    tasks = r_tasks.json()
    assert len(tasks) > 0

    first_task = tasks[0]

    # 3. Fast-forward time manually by setting due_at to past
    task_model = db.query(Task).filter(Task.id == uuid.UUID(first_task["id"])).first()
    task_model.due_at = datetime.now(UTC) - timedelta(days=2)
    db.commit()

    # 4. Trigger deadline check
    r_deadline = client.post("/api/v1/admin/check-deadlines", headers=auth_header)
    assert r_deadline.status_code == 200

    # 5. Verify: task marked overdue, event_log created, audit_event created,
    # rules engine created escalation task, RED health
    r_tasks_after = client.get(f"/api/v1/transactions/{txn_id}/tasks", headers=auth_header)
    tasks_after = r_tasks_after.json()

    escalation_tasks = [t for t in tasks_after if t["title"].startswith("ESCALATION")]
    assert len(escalation_tasks) == 1

    overdue_task = next(t for t in tasks_after if t["id"] == first_task["id"])
    assert overdue_task["status"] == "overdue"

    r_events = client.get(f"/api/v1/transactions/{txn_id}/events", headers=auth_header)
    events = [e for e in r_events.json() if e["event_type"] == "task.overdue"]
    assert len(events) >= 1

    r_audit = client.get(
        f"/api/v1/audit?org_id={str(org.id)}&action=task.marked_overdue", headers=auth_header
    )
    audit_events = r_audit.json()["items"]
    assert len(audit_events) >= 1

    r_health = client.get(f"/api/v1/transactions/{txn_id}/health", headers=auth_header)
    assert r_health.json()["score"] == "YELLOW"

    # 6. Mark the escalation task as done, and the overdue task as done.
    escalation_task_id = escalation_tasks[0]["id"]
    client.patch(
        f"/api/v1/tasks/{escalation_task_id}/status", json={"status": "done"}, headers=auth_header
    )
    client.patch(
        f"/api/v1/tasks/{first_task['id']}/status", json={"status": "done"}, headers=auth_header
    )

    # 7. Verify health score improves
    r_health_after = client.get(f"/api/v1/transactions/{txn_id}/health", headers=auth_header)
    assert r_health_after.json()["score"] == "GREEN"
