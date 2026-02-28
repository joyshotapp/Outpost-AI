"""Utility functions for Celery task management"""

from app.celery import celery_app
from app.tasks import (
    send_email_task,
    send_bulk_emails,
    process_video_metadata,
    generate_thumbnails,
    track_user_activity,
)


def queue_email(to_email: str, subject: str, html_content: str):
    """
    Queue an email to be sent asynchronously

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email content

    Returns:
        Task ID for tracking
    """
    task = send_email_task.delay(to_email, subject, html_content)
    return task.id


def queue_bulk_emails(recipient_list: list, subject: str, html_content: str):
    """
    Queue emails to multiple recipients asynchronously

    Args:
        recipient_list: List of email addresses
        subject: Email subject
        html_content: HTML email content

    Returns:
        Task ID for tracking
    """
    task = send_bulk_emails.delay(recipient_list, subject, html_content)
    return task.id


def queue_video_processing(video_id: int, video_url: str):
    """
    Queue video metadata processing

    Args:
        video_id: ID of the video
        video_url: S3 URL of the video

    Returns:
        Task ID for tracking
    """
    task = process_video_metadata.delay(video_id, video_url)
    return task.id


def queue_thumbnail_generation(video_id: int, video_url: str, timestamps: list = None):
    """
    Queue thumbnail generation for a video

    Args:
        video_id: ID of the video
        video_url: S3 URL of the video
        timestamps: Optional list of timestamps for thumbnails

    Returns:
        Task ID for tracking
    """
    if timestamps is None:
        timestamps = [10, 30, 60]
    task = generate_thumbnails.delay(video_id, video_url, timestamps)
    return task.id


def queue_user_activity(user_id: int, action: str, resource_type: str, resource_id: int):
    """
    Queue user activity tracking

    Args:
        user_id: ID of the user
        action: Action type (view, click, download, etc.)
        resource_type: Type of resource (video, supplier, etc.)
        resource_id: ID of the resource

    Returns:
        Task ID for tracking
    """
    task = track_user_activity.delay(user_id, action, resource_type, resource_id)
    return task.id


def get_task_status(task_id: str) -> dict:
    """
    Get the status of a Celery task

    Args:
        task_id: Celery task ID

    Returns:
        Dict with task status and result
    """
    task = celery_app.AsyncResult(task_id)
    return {
        "id": task.id,
        "state": task.state,
        "result": task.result,
        "traceback": task.traceback if task.failed() else None,
    }


def revoke_task(task_id: str, terminate: bool = False):
    """
    Revoke (cancel) a Celery task

    Args:
        task_id: Celery task ID
        terminate: If True, terminate running tasks immediately

    Returns:
        Dict with revocation status
    """
    celery_app.control.revoke(task_id, terminate=terminate)
    return {
        "task_id": task_id,
        "revoked": True,
        "terminate": terminate,
    }
