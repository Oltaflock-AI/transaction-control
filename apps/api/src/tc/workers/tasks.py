from tc.workers.celery_app import celery_app


@celery_app.task(name="tc.generate_timeline")
def generate_timeline(transaction_id: str) -> dict:
    # TODO: call timeline_service.generate_timeline(transaction_id)
    return {"transaction_id": transaction_id, "status": "queued"}
