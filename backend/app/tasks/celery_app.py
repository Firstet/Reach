"""Celery task queue configuration."""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "reach",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

celery_app.conf.beat_schedule = {
    "run-campaign-tick-every-minute": {
        "task": "run_campaign_tick",
        "schedule": 60.0,
    },
    "fetch-replies-every-two-minutes": {
        "task": "fetch_and_process_replies",
        "schedule": 120.0,
    },
}
