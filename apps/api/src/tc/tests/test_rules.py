from __future__ import annotations

import uuid
from datetime import UTC, datetime

from tc.db.models.task import Task
from tc.db.models.transaction import Transaction
from tc.domain.rules import evaluate_rules, build_dedupe_key


def test_evaluate_rules_due_soon(db, seed_user):
    user, org = seed_user
    txn = Transaction(
        id=uuid.uuid4(), org_id=org.id, title="123 Test St", status="active", health_score="GREEN"
    )
    db.add(txn)

    task = Task(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        title="Schedule Inspection",
        status="todo",
        due_at=datetime.now(UTC),
    )
    db.add(task)
    db.commit()

    created_tasks = evaluate_rules(db, trigger="task.due_soon", source_task=task)

    assert len(created_tasks) == 1
    new_task = created_tasks[0]
    assert new_task.title == "Reminder: Confirm 'Schedule Inspection' is scheduled"
    assert new_task.category == "reminder"
    assert new_task.severity == "medium"
    assert new_task.dedupe_key == build_dedupe_key("due_soon_reminder", "task.due_soon", task.id)
    assert new_task.assignee_id is None


def test_evaluate_rules_overdue_escalation_assigns_coordinator(db, seed_user):
    user, org = seed_user
    txn = Transaction(
        id=uuid.uuid4(), org_id=org.id, title="123 Test St", status="active", health_score="GREEN"
    )
    db.add(txn)

    task = Task(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        title="Finalize Contract",
        status="overdue",
        due_at=datetime.now(UTC),
    )
    db.add(task)
    db.commit()

    created_tasks = evaluate_rules(db, trigger="task.overdue", source_task=task)

    assert len(created_tasks) == 1
    new_task = created_tasks[0]
    assert new_task.title == "ESCALATION: 'Finalize Contract' is overdue"
    assert new_task.category == "escalation"
    assert new_task.severity == "critical"
    # Should assign to admin user
    assert new_task.assignee_id == user.id


def test_evaluate_rules_idempotent(db, seed_user):
    user, org = seed_user
    txn = Transaction(
        id=uuid.uuid4(), org_id=org.id, title="123 Test St", status="active", health_score="GREEN"
    )
    db.add(txn)

    task = Task(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        title="Schedule Inspection",
        status="todo",
        due_at=datetime.now(UTC),
    )
    db.add(task)
    db.commit()

    created_tasks_1 = evaluate_rules(db, trigger="task.due_soon", source_task=task)
    assert len(created_tasks_1) == 1

    created_tasks_2 = evaluate_rules(db, trigger="task.due_soon", source_task=task)
    assert len(created_tasks_2) == 0
