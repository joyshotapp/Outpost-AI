"""Content management API — Sprint 9 (Tasks 9.6-9.9).

Endpoints:
  POST /content/viral/{video_id}              — Trigger content viral pipeline
  GET  /content                               — List content items (paginated + filtered)
  GET  /content/{item_id}                     — Get single item
  PATCH /content/{item_id}                    — Edit title / body / keywords / hashtags
  PATCH /content/{item_id}/status             — Change status (approve / reject / schedule)
  POST  /content/{item_id}/schedule           — Push to Repurpose.io
  GET  /content/review-queue                  — Items pending human review
  PATCH /content/review-queue/bulk            — Bulk approve / reject
  GET  /content/analytics/summary             — Aggregate performance stats
  POST /content/webhooks/opusclip             — OpusClip completion webhook
  POST /content/webhooks/repurpose            — Repurpose.io publish webhook
"""

import hashlib
import hmac
import logging
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_supplier
from app.models.content_item import ContentItem
from app.services.opusclip import OpusClipService
from app.services.repurpose import RepurposeService
from app.tasks.content_viral import (
    run_quality_guard_task,
    schedule_approved_post,
    sync_content_analytics_task,
    trigger_content_viral_pipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])

# ── Pydantic schemas ──────────────────────────────────────────────────────────


class ContentItemOut(BaseModel):
    id: int
    supplier_id: int
    source_video_id: int | None
    content_type: str
    title: str
    body: str
    keywords: str | None
    hashtags: str | None
    excerpt: str | None
    status: str
    platform: str | None
    platform_post_id: str | None
    scheduled_publish_date: str | None
    published_at: str | None
    published_url: str | None
    quality_score: int | None
    quality_checked: bool
    impressions: int
    engagements: int
    clicks: int
    likes: int
    shares: int
    comments: int
    last_analytics_sync: str | None
    opusclip_job_id: str | None
    short_video_url: str | None
    short_video_duration_s: int | None
    opusclip_highlights_score: int | None
    review_notes: str | None

    class Config:
        from_attributes = True


class ContentItemPatch(BaseModel):
    title: str | None = None
    body: str | None = None
    keywords: str | None = None
    hashtags: str | None = None
    excerpt: str | None = None
    platform: str | None = None


class StatusUpdate(BaseModel):
    status: Literal["draft", "review", "approved", "rejected", "archived"]
    review_notes: str | None = None


class ScheduleRequest(BaseModel):
    workflow_id: str
    scheduled_at: str | None = None
    platform: str | None = None


class BulkReviewAction(BaseModel):
    item_ids: list[int] = Field(..., min_length=1)
    action: Literal["approve", "reject", "archive"]
    review_notes: str | None = None


# ── Helper ────────────────────────────────────────────────────────────────────


async def _get_item_for_supplier(
    item_id: int,
    supplier_id: int,
    db: AsyncSession,
) -> ContentItem:
    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == item_id,
            ContentItem.supplier_id == supplier_id,
        )
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    return item


# ── Trigger pipeline ──────────────────────────────────────────────────────────


@router.post(
    "/viral/{video_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger content viral pipeline for a video (9.4)",
)
async def trigger_viral(
    video_id: int,
    current_supplier: dict = Depends(get_current_supplier),
) -> dict[str, Any]:
    """Fan out content generation tasks for a given video.

    Returns task IDs for LinkedIn, SEO, and OpusClip sub-jobs.
    """
    result = trigger_content_viral_pipeline.apply_async(args=[video_id])
    return {
        "message": "Content viral pipeline dispatched",
        "video_id": video_id,
        "task_id": result.id,
    }


# ── Content CRUD ──────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=dict[str, Any],
    summary="List content items with filters (9.6/9.7/9.8)",
)
async def list_content_items(
    content_type: str | None = Query(None, description="linkedin_post|seo_article|short_video"),
    status_filter: str | None = Query(None, alias="status"),
    platform: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> dict[str, Any]:
    supplier_id = current_supplier["id"]
    q = select(ContentItem).where(ContentItem.supplier_id == supplier_id)

    if content_type:
        q = q.where(ContentItem.content_type == content_type)
    if status_filter:
        q = q.where(ContentItem.status == status_filter)
    if platform:
        q = q.where(ContentItem.platform == platform)

    # Count
    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(ContentItem.created_at.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().all()

    return {
        "items": [ContentItemOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),
    }


@router.get(
    "/{item_id:int}",
    response_model=ContentItemOut,
    summary="Get single content item",
)
async def get_content_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> ContentItemOut:
    item = await _get_item_for_supplier(item_id, current_supplier["id"], db)
    return ContentItemOut.model_validate(item)


@router.patch(
    "/{item_id:int}",
    response_model=ContentItemOut,
    summary="Edit content item (title/body/keywords/hashtags)",
)
async def patch_content_item(
    item_id: int,
    patch: ContentItemPatch,
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> ContentItemOut:
    item = await _get_item_for_supplier(item_id, current_supplier["id"], db)
    updates = patch.model_dump(exclude_none=True)
    if updates:
        await db.execute(
            update(ContentItem).where(ContentItem.id == item_id).values(**updates)
        )
        await db.commit()
        await db.refresh(item)
    return ContentItemOut.model_validate(item)


@router.patch(
    "/{item_id:int}/status",
    response_model=ContentItemOut,
    summary="Update content item status (approve/reject/schedule)",
)
async def update_content_status(
    item_id: int,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> ContentItemOut:
    item = await _get_item_for_supplier(item_id, current_supplier["id"], db)
    updates: dict[str, Any] = {
        "status": body.status,
        "reviewed_by": current_supplier["id"],
    }
    if body.review_notes:
        updates["review_notes"] = body.review_notes
    await db.execute(update(ContentItem).where(ContentItem.id == item_id).values(**updates))
    await db.commit()
    await db.refresh(item)
    return ContentItemOut.model_validate(item)


@router.post(
    "/{item_id:int}/schedule",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Schedule item for publishing via Repurpose.io (9.5)",
)
async def schedule_content_item(
    item_id: int,
    body: ScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> dict[str, Any]:
    item = await _get_item_for_supplier(item_id, current_supplier["id"], db)
    if item.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Item must be approved before scheduling (current status: {item.status})",
        )
    if body.platform:
        await db.execute(
            update(ContentItem).where(ContentItem.id == item_id).values(platform=body.platform)
        )
        await db.commit()

    task = schedule_approved_post.apply_async(
        args=[item_id, body.workflow_id, body.scheduled_at]
    )
    return {"message": "Scheduling submitted", "task_id": task.id}


# ── Review queue ──────────────────────────────────────────────────────────────


@router.get(
    "/review-queue",
    response_model=dict[str, Any],
    summary="Items pending human review (9.9)",
)
async def get_review_queue(
    content_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> dict[str, Any]:
    supplier_id = current_supplier["id"]
    q = select(ContentItem).where(
        ContentItem.supplier_id == supplier_id,
        ContentItem.status == "review",
    )
    if content_type:
        q = q.where(ContentItem.content_type == content_type)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items = (
        await db.execute(
            q.order_by(ContentItem.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return {
        "items": [ContentItemOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),
    }


@router.patch(
    "/review-queue/bulk",
    summary="Bulk approve / reject / archive content items (9.9)",
)
async def bulk_review_action(
    body: BulkReviewAction,
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> dict[str, Any]:
    supplier_id = current_supplier["id"]
    action_to_status = {
        "approve": "approved",
        "reject": "rejected",
        "archive": "archived",
    }
    new_status = action_to_status[body.action]
    updates: dict[str, Any] = {
        "status": new_status,
        "reviewed_by": supplier_id,
    }
    if body.review_notes:
        updates["review_notes"] = body.review_notes

    await db.execute(
        update(ContentItem)
        .where(
            ContentItem.id.in_(body.item_ids),
            ContentItem.supplier_id == supplier_id,
        )
        .values(**updates)
    )
    await db.commit()
    return {"updated": len(body.item_ids), "new_status": new_status}


# ── Analytics summary ─────────────────────────────────────────────────────────


@router.get(
    "/analytics/summary",
    summary="Aggregate content performance stats (9.10)",
)
async def content_analytics_summary(
    content_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_supplier: dict = Depends(get_current_supplier),
) -> dict[str, Any]:
    supplier_id = current_supplier["id"]
    q = select(ContentItem).where(
        ContentItem.supplier_id == supplier_id,
        ContentItem.status == "published",
    )
    if content_type:
        q = q.where(ContentItem.content_type == content_type)

    items = (await db.execute(q)).scalars().all()

    total_impressions = sum(i.impressions for i in items)
    total_engagements = sum(i.engagements for i in items)
    total_clicks = sum(i.clicks for i in items)
    total_likes = sum(i.likes for i in items)
    total_shares = sum(i.shares for i in items)
    n = len(items)

    return {
        "total_published": n,
        "total_impressions": total_impressions,
        "total_engagements": total_engagements,
        "total_clicks": total_clicks,
        "total_likes": total_likes,
        "total_shares": total_shares,
        "avg_impressions": round(total_impressions / n, 1) if n else 0,
        "engagement_rate": round(total_engagements / max(total_impressions, 1) * 100, 2),
    }


@router.post(
    "/analytics/sync",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger analytics sync from LinkedIn/YouTube (9.10)",
)
async def trigger_analytics_sync(
    current_supplier: dict = Depends(get_current_supplier),
) -> dict[str, Any]:
    task = sync_content_analytics_task.apply_async(args=[current_supplier["id"]])
    return {"message": "Analytics sync submitted", "task_id": task.id}


# ── Webhooks ──────────────────────────────────────────────────────────────────


@router.post(
    "/webhooks/opusclip",
    status_code=status.HTTP_202_ACCEPTED,
    summary="OpusClip completion webhook (9.1)",
)
async def opusclip_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    body = await request.body()
    sig = request.headers.get("X-OpusClip-Signature", "")
    if not OpusClipService.verify_webhook_signature(body, sig):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event", "")
    job_id = payload.get("job_id", "")

    if event == "clips.completed":
        # The poll task will already be retrying; completion webhook shortcuts it.
        background_tasks.add_task(
            _handle_opusclip_completed, job_id, payload.get("clips", [])
        )
    elif event == "clips.failed":
        logger.warning("OpusClip job %s failed via webhook", job_id)

    return {"status": "accepted"}


async def _handle_opusclip_completed(job_id: str, clips: list[dict[str, Any]]) -> None:
    """Find placeholder ContentItems for this job and write clip results."""
    from app.database import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(
            select(ContentItem).where(ContentItem.opusclip_job_id == job_id)
        )
        items = result.scalars().all()

    from app.tasks.content_viral import _write_clip_results

    ids = [i.id for i in items]
    if ids:
        await _write_clip_results(ids, clips)


@router.post(
    "/webhooks/repurpose",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Repurpose.io publish webhook (9.5)",
)
async def repurpose_webhook(
    request: Request,
) -> dict[str, str]:
    body = await request.body()
    sig = request.headers.get("X-Repurpose-Signature", "")
    if not RepurposeService.verify_webhook_signature(body, sig):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event", "")
    job_id = payload.get("job_id", "")
    platform_post_id = payload.get("platform_post_id", "")
    published_url = payload.get("url", "")

    if event == "post.published" and job_id:
        from app.database import async_session_maker
        from datetime import datetime, timezone

        async with async_session_maker() as session:
            await session.execute(
                update(ContentItem)
                .where(ContentItem.repurpose_job_id == job_id)
                .values(
                    status="published",
                    platform_post_id=platform_post_id,
                    published_url=published_url,
                    published_at=datetime.now(timezone.utc).isoformat(),
                )
            )
            await session.commit()

    return {"status": "accepted"}
