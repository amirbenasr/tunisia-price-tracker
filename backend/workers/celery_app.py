"""Celery application configuration."""

from celery import Celery

from src.core.config import settings

# Create Celery app
celery_app = Celery(
    "tunisia_tracker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.scrape",
        "workers.tasks.cleanup",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=2,

    # Result settings
    result_expires=3600,  # Results expire after 1 hour

    # Beat scheduler settings
    beat_schedule={
        "scrape-all-websites-daily": {
            "task": "workers.tasks.scrape.scrape_all_websites",
            "schedule": 86400.0,  # Every 24 hours
            "options": {"queue": "scraping"},
        },
        "cleanup-old-prices-weekly": {
            "task": "workers.tasks.cleanup.cleanup_old_prices",
            "schedule": 604800.0,  # Every 7 days
            "options": {"queue": "maintenance"},
        },
    },

    # Queue routing
    task_routes={
        "workers.tasks.scrape.*": {"queue": "scraping"},
        "workers.tasks.cleanup.*": {"queue": "maintenance"},
    },
)
