"""Celery application configuration"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery app
celery_app = Celery(
    "factory_insider",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard time limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft time limit
    result_expires=3600,  # Results expire after 1 hour
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routes for different queues
celery_app.conf.task_routes = {
    "app.tasks.email.*": {"queue": "email"},
    "app.tasks.video.*": {"queue": "video"},
    "app.tasks.analytics.*": {"queue": "analytics"},
    "app.tasks.ai.*": {"queue": "ai"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Example: Clean up old sessions every hour
    "cleanup-old-sessions": {
        "task": "app.tasks.maintenance.cleanup_old_sessions",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Update view counts every 15 minutes
    "update-view-counts": {
        "task": "app.tasks.analytics.update_view_counts",
        "schedule": crontab(minute="*/15"),
    },
}

# Auto-discover tasks from app
celery_app.autodiscover_tasks(["app"])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f"Request: {self.request!r}")
