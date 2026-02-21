from __future__ import annotations

from tc.workers.celery_app import celery_app


@celery_app.task(name="tc.generate_timeline")
def generate_timeline(transaction_id: str) -> dict:
    from uuid import UUID

    from tc.db.session import SessionLocal
    from tc.services.timeline_service import generate_default_timeline

    db = SessionLocal()
    try:
        tasks = generate_default_timeline(db, UUID(transaction_id))
        return {"transaction_id": transaction_id, "tasks_created": len(tasks)}
    finally:
        db.close()


@celery_app.task(name="tc.check_deadlines")
def check_deadlines_task() -> dict:
    from tc.db.session import SessionLocal
    from tc.services.deadline_service import check_deadlines

    db = SessionLocal()
    try:
        count = check_deadlines(db)
        return {"marked_overdue": count}
    finally:
        db.close()
