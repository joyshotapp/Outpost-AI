"""Celery tasks package"""

from app.tasks.email import send_email_task, send_bulk_emails
from app.tasks.video import process_video_metadata, generate_thumbnails, transcribe_video_with_whisper
from app.tasks.analytics import update_view_counts, track_user_activity
from app.tasks.maintenance import cleanup_old_sessions
from app.tasks.knowledge_base import ingest_knowledge_document
from app.tasks.visitor_intent import process_visitor_intent_event

__all__ = [
    "send_email_task",
    "send_bulk_emails",
    "process_video_metadata",
    "generate_thumbnails",
    "transcribe_video_with_whisper",
    "update_view_counts",
    "track_user_activity",
    "process_visitor_intent_event",
    "cleanup_old_sessions",
    "ingest_knowledge_document",
]
