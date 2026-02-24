import uuid
from datetime import UTC, datetime, timedelta

from tc.db.models.audit import AuditEvent
from tc.db.models.event_log import EventLog
from tc.db.models.task import Task
from tc.db.models.transaction import Transaction
from tc.domain.enums import TaskStatus
from tc.services.deadline_service import check_deadlines


def _create_task(db, org, *, status=TaskStatus.todo, due_offset_hours=-24):
    """Helper: create a transaction + single task with a due_at relative to now."""
    txn = Transaction(id=uuid.uuid4(), org_id=org.id, title="Deadline test txn")
    db.add(txn)
    db.flush()

    due_at = datetime.now(UTC) + timedelta(hours=due_offset_hours)
    task = Task(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        title="Overdue candidate",
        status=status,
        due_at=due_at,
    )
    db.add(task)
    db.commit()
    return txn, task


class TestMarkOverdue:
    def test_marks_past_due_task_overdue(self, db, seed_user):
        _, org = seed_user
        _txn, task = _create_task(db, org, due_offset_hours=-24)

        result = check_deadlines(db)

        db.refresh(task)
        assert task.status == TaskStatus.overdue
        assert result["overdue_marked"] == 1

    def test_ignores_future_due_date(self, db, seed_user):
        _, org = seed_user
        _txn, task = _create_task(db, org, due_offset_hours=+48)

        result = check_deadlines(db)

        db.refresh(task)
        assert task.status == TaskStatus.todo
        assert result["overdue_marked"] == 0

    def test_ignores_done_tasks(self, db, seed_user):
        _, org = seed_user
        _txn, task = _create_task(db, org, status=TaskStatus.done, due_offset_hours=-24)

        result = check_deadlines(db)

        db.refresh(task)
        assert task.status == TaskStatus.done
        assert result["overdue_marked"] == 0


class TestIdempotency:
    def test_does_not_remarque_already_overdue(self, db, seed_user):
        _, org = seed_user
        _txn, task = _create_task(db, org, due_offset_hours=-24)

        check_deadlines(db)
        db.refresh(task)
        assert task.status == TaskStatus.overdue

        audit_count_after_first = db.query(AuditEvent).count()
        event_count_after_first = db.query(EventLog).count()

        check_deadlines(db)

        assert db.query(AuditEvent).count() == audit_count_after_first
        assert db.query(EventLog).count() == event_count_after_first


class TestEmitsLogs:
    def test_creates_event_log_entry(self, db, seed_user):
        _, org = seed_user
        txn, task = _create_task(db, org, due_offset_hours=-24)

        check_deadlines(db)

        logs = db.query(EventLog).filter(EventLog.transaction_id == txn.id).all()
        assert len(logs) == 1
        assert logs[0].event_type == "task.overdue"
        assert logs[0].entity_type == "task"
        assert logs[0].entity_id == task.id
        assert "task_title" in logs[0].detail

    def test_creates_audit_event_entry(self, db, seed_user):
        _, org = seed_user
        _txn, task = _create_task(db, org, due_offset_hours=-24)

        check_deadlines(db)

        audits = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.entity_id == task.id,
                AuditEvent.action == "task.marked_overdue",
            )
            .all()
        )
        assert len(audits) == 1
        assert audits[0].entity_type == "task"
        assert audits[0].actor_id is None
        assert audits[0].org_id == org.id
        assert "transaction_id" in audits[0].detail


class TestAuditEndpoint:
    def test_audit_returns_overdue_entries(self, db, client, auth_header, seed_user):
        _, org = seed_user
        txn, _task = _create_task(db, org, due_offset_hours=-24)

        check_deadlines(db)

        r = client.get(f"/api/v1/transactions/{txn.id}/audit", headers=auth_header)
        assert r.status_code == 200
        events = r.json()
        assert len(events) >= 1
        assert events[0]["action"] == "task.marked_overdue"
        assert events[0]["actor_id"] is None

    def test_audit_empty_before_overdue(self, db, client, auth_header, seed_user):
        _, org = seed_user
        txn, _task = _create_task(db, org, due_offset_hours=+48)

        r = client.get(f"/api/v1/transactions/{txn.id}/audit", headers=auth_header)
        assert r.status_code == 200
        assert r.json() == []
