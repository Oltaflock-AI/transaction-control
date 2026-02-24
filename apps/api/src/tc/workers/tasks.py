from __future__ import annotations

import logging

from tc.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tc.generate_timeline", acks_late=True)
def generate_timeline(transaction_id: str) -> dict:
    from uuid import UUID

    from tc.db.session import SessionLocal
    from tc.services.timeline_service import generate_default_timeline

    db = SessionLocal()
    try:
        tasks = generate_default_timeline(db, UUID(transaction_id))
        result = {"transaction_id": transaction_id, "tasks_created": len(tasks)}
        logger.info("generate_timeline: %s", result)
        return result
    except Exception:
        logger.exception("generate_timeline failed for transaction_id=%s", transaction_id)
        raise
    finally:
        db.close()


@celery_app.task(name="tc.check_deadlines", acks_late=True)
def check_deadlines_task() -> dict:
    from tc.db.session import SessionLocal
    from tc.services.deadline_service import check_deadlines

    db = SessionLocal()
    try:
        result = check_deadlines(db)
        logger.info("check_deadlines: %s", result)
        return result
    except Exception:
        logger.exception("check_deadlines failed")
        raise
    finally:
        db.close()
