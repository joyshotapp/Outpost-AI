"""Content viral pipeline Celery tasks — Sprint 9 (Task 9.4).

Tasks:
  trigger_content_viral_pipeline : Master orchestrator — given a video_id, fan
                                   out all content generation work in sequence.
  generate_linkedin_posts_task   : 9.2 — Claude LinkedIn post batch
  generate_seo_articles_task     : 9.2 — Claude SEO article batch
  clip_short_videos_task         : 9.1 — OpusClip short-video job submission
  poll_opusclip_job              : 9.1 — Poll job until complete, persist clips
  schedule_approved_post         : 9.5 — Push approved item to Repurpose.io
  sync_content_analytics_task    : 9.10 — Refresh platform engagement metrics
  run_quality_guard_task         : 9.3 — Re-run quality check on a content item

Pipeline flow (per video):
  trigger_content_viral_pipeline
    ├─► generate_linkedin_posts_task   (async Claude batch → N ContentItem rows)
    ├─► generate_seo_articles_task     (async Claude batch → N ContentItem rows)
    └─► clip_short_videos_task         (OpusClip job submission)
          └─► poll_opusclip_job        (retry until complete → M ContentItem rows)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from celery import shared_task
from sqlalchemy import select, update

from app.config import settings
from app.database import async_session_maker
from app.models.content_item import ContentItem
from app.models.video import Video
from app.services.content_generation import ContentGenerationService
from app.services.content_analytics import ContentAnalyticsService
from app.services.opusclip import OpusClipService
from app.services.repurpose import RepurposeService

logger = logging.getLogger(__name__)

_ISO_NOW = lambda: datetime.now(timezone.utc).isoformat()  # noqa: E731


def _run_async(coro: Any) -> Any:
    """Run async coroutine in an isolated event loop (Celery-safe)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _get_video(video_id: int) -> Video | None:
    async with async_session_maker() as session:
        result = await session.execute(select(Video).where(Video.id == video_id))
        return result.scalars().first()


async def _bulk_insert_content_items(items: list[dict[str, Any]]) -> list[int]:
    """Insert a batch of content item dicts; return their new IDs."""
    ids: list[int] = []
    async with async_session_maker() as session:
        for item_data in items:
            obj = ContentItem(**item_data)
            session.add(obj)
            await session.flush()
            ids.append(obj.id)
        await session.commit()
    return ids


async def _update_content_item(item_id: int, **fields: Any) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(ContentItem).where(ContentItem.id == item_id).values(**fields)
        )
        await session.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.4 — Master orchestrator
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="content.trigger_content_viral_pipeline",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def trigger_content_viral_pipeline(self, video_id: int) -> dict[str, Any]:
    """Fan out all Sprint 9 content generation tasks for a given video.

    Submits parallel Celery tasks for:
      1. LinkedIn post generation
      2. SEO article generation
      3. OpusClip short-video submission

    Returns a summary dict with task IDs for each sub-job.
    """
    logger.info("content_viral_pipeline: starting for video_id=%s", video_id)
    try:
        li_task = generate_linkedin_posts_task.apply_async(args=[video_id])
        seo_task = generate_seo_articles_task.apply_async(args=[video_id])
        clip_task = clip_short_videos_task.apply_async(args=[video_id])

        return {
            "video_id": video_id,
            "linkedin_task_id": li_task.id,
            "seo_task_id": seo_task.id,
            "clip_task_id": clip_task.id,
            "status": "dispatched",
        }
    except Exception as exc:
        logger.exception("content_viral_pipeline failed for video_id=%s: %s", video_id, exc)
        raise self.retry(exc=exc)


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.2 — LinkedIn post generation
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="content.generate_linkedin_posts",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def generate_linkedin_posts_task(self, video_id: int) -> dict[str, Any]:
    """Generate up to CONTENT_MAX_LINKEDIN_POSTS posts from a video transcript."""
    return _run_async(_async_generate_linkedin_posts(video_id))


async def _async_generate_linkedin_posts(video_id: int) -> dict[str, Any]:
    video = await _get_video(video_id)
    if not video:
        return {"error": f"video {video_id} not found", "created": 0}

    transcript = getattr(video, "transcript", "") or ""
    if not transcript:
        logger.warning("generate_linkedin_posts: video %s has no transcript", video_id)
        transcript = f"[Transcript unavailable — fallback for video '{getattr(video, 'title', video_id)}']"

    supplier_name = f"Supplier #{getattr(video, 'supplier_id', 0)}"

    svc = ContentGenerationService()
    posts = await svc.generate_linkedin_posts(transcript, supplier_name)

    items_to_create = [
        {
            "supplier_id": getattr(video, "supplier_id", 0),
            "source_video_id": video_id,
            "content_type": "linkedin_post",
            "title": p["title"],
            "body": svc.clean_text(p["body"]),
            "hashtags": p.get("hashtags", ""),
            "quality_score": p["quality_score"],
            "quality_checked": True,
            "status": p["status"],
        }
        for p in posts
    ]

    ids = await _bulk_insert_content_items(items_to_create)
    logger.info("generate_linkedin_posts: created %d items for video %s", len(ids), video_id)
    return {"video_id": video_id, "created": len(ids), "item_ids": ids}


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.2 — SEO article generation
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="content.generate_seo_articles",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def generate_seo_articles_task(self, video_id: int) -> dict[str, Any]:
    """Generate up to CONTENT_MAX_SEO_ARTICLES articles from a video transcript."""
    return _run_async(_async_generate_seo_articles(video_id))


async def _async_generate_seo_articles(video_id: int) -> dict[str, Any]:
    video = await _get_video(video_id)
    if not video:
        return {"error": f"video {video_id} not found", "created": 0}

    transcript = getattr(video, "transcript", "") or ""
    supplier_name = f"Supplier #{getattr(video, 'supplier_id', 0)}"

    svc = ContentGenerationService()
    articles = await svc.generate_seo_articles(transcript, supplier_name)

    items_to_create = [
        {
            "supplier_id": getattr(video, "supplier_id", 0),
            "source_video_id": video_id,
            "content_type": "seo_article",
            "title": a["title"],
            "body": svc.clean_text(a["body"]),
            "keywords": a.get("keywords", ""),
            "excerpt": a.get("excerpt", ""),
            "quality_score": a["quality_score"],
            "quality_checked": True,
            "status": a["status"],
        }
        for a in articles
    ]

    ids = await _bulk_insert_content_items(items_to_create)
    logger.info("generate_seo_articles: created %d items for video %s", len(ids), video_id)
    return {"video_id": video_id, "created": len(ids), "item_ids": ids}


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.1 — OpusClip job submission
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="content.clip_short_videos",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def clip_short_videos_task(self, video_id: int) -> dict[str, Any]:
    """Submit video to OpusClip for short-clip generation."""
    return _run_async(_async_clip_short_videos(self, video_id))


async def _async_clip_short_videos(task_self: Any, video_id: int) -> dict[str, Any]:
    video = await _get_video(video_id)
    if not video:
        return {"error": f"video {video_id} not found"}

    video_url = getattr(video, "s3_url", None) or getattr(video, "url", None)
    if not video_url:
        return {"error": f"video {video_id} has no accessible URL"}

    opus = OpusClipService()
    try:
        job = opus.create_clip_job(video_url)
    except Exception as exc:
        logger.error("OpusClip job submission failed: %s", exc)
        raise task_self.retry(exc=exc)

    job_id = job.get("job_id", "")
    # Create placeholder ContentItem rows (one per expected clip)
    n_clips = settings.OPUSCLIP_CLIPS_PER_VIDEO
    items_to_create = [
        {
            "supplier_id": getattr(video, "supplier_id", 0),
            "source_video_id": video_id,
            "content_type": "short_video",
            "title": f"Short Clip {i+1}",
            "body": "[Processing — OpusClip]",
            "status": "processing",
            "opusclip_job_id": job_id,
        }
        for i in range(n_clips)
    ]
    ids = await _bulk_insert_content_items(items_to_create)

    # Chain polling task with 5-min delay
    poll_opusclip_job.apply_async(
        args=[job_id, video_id, ids],
        countdown=300,
    )
    logger.info("clip_short_videos: submitted job %s, created %d placeholder items", job_id, len(ids))
    return {"video_id": video_id, "opusclip_job_id": job_id, "placeholder_ids": ids}


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.1 — OpusClip polling
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="content.poll_opusclip_job",
    bind=True,
    max_retries=24,           # retry up to 2 hours (24 × 5 min)
    default_retry_delay=300,  # 5 minutes
)
def poll_opusclip_job(
    self,
    job_id: str,
    video_id: int,
    placeholder_ids: list[int],
) -> dict[str, Any]:
    """Poll OpusClip until the job completes, then write clip URLs back."""
    opus = OpusClipService()
    status_data = opus.get_job_status(job_id)
    status = status_data.get("status", "processing")

    if status == "processing":
        logger.info("OpusClip job %s still processing — will retry", job_id)
        raise self.retry()

    if status == "failed":
        _run_async(_mark_clips_failed(placeholder_ids, "OpusClip job failed"))
        return {"job_id": job_id, "status": "failed"}

    # Completed — fetch clips
    clips = opus.get_clips(job_id)
    _run_async(_write_clip_results(placeholder_ids, clips))
    logger.info("OpusClip job %s completed — %d clips written", job_id, len(clips))
    return {"job_id": job_id, "status": "completed", "clips_written": len(clips)}


async def _write_clip_results(
    placeholder_ids: list[int],
    clips: list[dict[str, Any]],
) -> None:
    async with async_session_maker() as session:
        for i, pid in enumerate(placeholder_ids):
            if i >= len(clips):
                # Mark extras as archived (didn't receive enough clips)
                await session.execute(
                    update(ContentItem)
                    .where(ContentItem.id == pid)
                    .values(status="archived")
                )
                continue
            clip = clips[i]
            await session.execute(
                update(ContentItem)
                .where(ContentItem.id == pid)
                .values(
                    title=f"Short Clip {i+1}",
                    body=clip.get("transcript_excerpt", ""),
                    short_video_url=clip.get("url", ""),
                    short_video_duration_s=clip.get("duration_s"),
                    opusclip_highlights_score=clip.get("highlights_score"),
                    status="draft",
                )
            )
        await session.commit()


async def _mark_clips_failed(placeholder_ids: list[int], reason: str) -> None:
    async with async_session_maker() as session:
        for pid in placeholder_ids:
            await session.execute(
                update(ContentItem)
                .where(ContentItem.id == pid)
                .values(status="archived", review_notes=reason)
            )
        await session.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.5 — Schedule approved post via Repurpose.io
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="content.schedule_approved_post",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def schedule_approved_post(
    self,
    content_item_id: int,
    workflow_id: str,
    scheduled_at: str | None = None,
) -> dict[str, Any]:
    """Push an approved ContentItem to Repurpose.io for scheduled publishing."""
    return _run_async(_async_schedule_approved_post(self, content_item_id, workflow_id, scheduled_at))


async def _async_schedule_approved_post(
    task_self: Any,
    content_item_id: int,
    workflow_id: str,
    scheduled_at: str | None,
) -> dict[str, Any]:
    async with async_session_maker() as session:
        result = await session.execute(
            select(ContentItem).where(ContentItem.id == content_item_id)
        )
        item = result.scalars().first()

    if not item:
        return {"error": f"ContentItem {content_item_id} not found"}

    if item.status != "approved":
        return {
            "error": f"ContentItem {content_item_id} must be approved before scheduling",
            "status": item.status,
        }

    svc = RepurposeService()
    try:
        if item.content_type == "short_video" and item.short_video_url:
            job = svc.schedule_video_post(
                workflow_id=workflow_id,
                title=item.title,
                video_url=item.short_video_url,
                platform=item.platform or "youtube",
                description=item.body,
                scheduled_at=scheduled_at,
                hashtags=(item.hashtags or "").split(",") if item.hashtags else [],
            )
        else:
            job = svc.schedule_text_post(
                workflow_id=workflow_id,
                title=item.title,
                body=item.body,
                platform=item.platform or "linkedin",
                scheduled_at=scheduled_at,
                hashtags=(item.hashtags or "").split(",") if item.hashtags else [],
            )
    except Exception as exc:
        logger.error("Repurpose schedule error for item %s: %s", content_item_id, exc)
        raise task_self.retry(exc=exc)

    job_id = job.get("job_id", "")
    await _update_content_item(
        content_item_id,
        repurpose_job_id=job_id,
        status="scheduled",
        scheduled_publish_date=scheduled_at or _ISO_NOW(),
    )
    return {"content_item_id": content_item_id, "repurpose_job_id": job_id}


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.10 — Sync platform analytics
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="content.sync_content_analytics",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def sync_content_analytics_task(
    self,
    supplier_id: int | None = None,
) -> dict[str, Any]:
    """Sync impression / engagement data from LinkedIn & YouTube.

    Processes all published ContentItems (optionally filtered by supplier_id).
    """
    return _run_async(_async_sync_content_analytics(supplier_id))


async def _async_sync_content_analytics(supplier_id: int | None) -> dict[str, Any]:
    analytics = ContentAnalyticsService()
    updated = 0

    async with async_session_maker() as session:
        q = select(ContentItem).where(ContentItem.status == "published")
        if supplier_id:
            q = q.where(ContentItem.supplier_id == supplier_id)
        result = await session.execute(q)
        items = result.scalars().all()

    for item in items:
        if not item.platform or not item.platform_post_id:
            continue
        try:
            stats = analytics.fetch_stats_for_item(item.platform, item.platform_post_id)
            if stats:
                await _update_content_item(
                    item.id,
                    impressions=stats.get("impressions", item.impressions),
                    clicks=stats.get("clicks", item.clicks),
                    likes=stats.get("likes", item.likes),
                    comments=stats.get("comments", item.comments),
                    shares=stats.get("shares", item.shares),
                    engagements=stats.get("engagements", item.engagements),
                    last_analytics_sync=_ISO_NOW(),
                )
                updated += 1
        except Exception as exc:
            logger.warning("Analytics sync failed for item %s: %s", item.id, exc)

    logger.info("sync_content_analytics: updated %d items (supplier=%s)", updated, supplier_id)
    return {"updated": updated, "supplier_id": supplier_id}


# ──────────────────────────────────────────────────────────────────────────────
# Task 9.3 — Re-run quality guard on a single item
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="content.run_quality_guard")
def run_quality_guard_task(content_item_id: int) -> dict[str, Any]:
    """Re-run quality check on a ContentItem and update its score and status."""
    return _run_async(_async_run_quality_guard(content_item_id))


async def _async_run_quality_guard(content_item_id: int) -> dict[str, Any]:
    async with async_session_maker() as session:
        result = await session.execute(
            select(ContentItem).where(ContentItem.id == content_item_id)
        )
        item = result.scalars().first()

    if not item:
        return {"error": f"ContentItem {content_item_id} not found"}

    svc = ContentGenerationService()
    score, flagged = svc.quality_check(item.body)
    new_status = item.status
    if new_status in ("draft", "review"):
        new_status = "draft" if score >= 70 else "review"

    await _update_content_item(
        content_item_id,
        quality_score=score,
        quality_checked=True,
        review_notes=f"Auto quality check — flagged: {', '.join(flagged) or 'none'}",
        status=new_status,
    )
    return {"content_item_id": content_item_id, "quality_score": score, "flagged": flagged}
