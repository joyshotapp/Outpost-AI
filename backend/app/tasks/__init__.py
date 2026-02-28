"""Celery tasks package"""

from app.tasks.email import send_email_task, send_bulk_emails
from app.tasks.video import process_video_metadata, generate_thumbnails
from app.tasks.analytics import update_view_counts, track_user_activity
from app.tasks.maintenance import cleanup_old_sessions

__all__ = [
    "send_email_task",
    "send_bulk_emails",
    "process_video_metadata",
    "generate_thumbnails",
    "update_view_counts",
    "track_user_activity",
    "cleanup_old_sessions",
]
