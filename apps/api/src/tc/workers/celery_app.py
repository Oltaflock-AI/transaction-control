from celery import Celery

from tc.core.config import settings

celery_app = Celery(
    "tc",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.autodiscover_tasks(["tc.workers.tasks"])
