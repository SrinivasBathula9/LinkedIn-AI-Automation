from celery import Celery
from backend.config import settings

celery_app = Celery(
    "linkedin_automation",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.queue.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "backend.queue.tasks.run_campaign_task": {"queue": "automation"},
        "backend.queue.tasks.classify_profile_task": {"queue": "ai"},
    },
)
