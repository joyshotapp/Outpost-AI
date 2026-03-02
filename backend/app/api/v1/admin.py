"""Admin endpoints: HeyGen usage / cost tracking — Sprint 6
          + Platform KPI / Supplier mgmt / Buyer mgmt / Content Review /
            Outbound Health / API Usage / System Settings — Sprint 11
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, Supplier, Buyer, RFQ
from app.models.heygen_usage import HeyGenUsageRecord
from app.models.content_item import ContentItem
from app.models.outbound_contact import OutboundContact
from app.models.email_sequence import EmailSequence
from app.models.subscription import Subscription
from app.models.api_usage_record import ApiUsageRecord
from app.models.system_setting import SystemSetting
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas (inline — no Pydantic models needed for simple aggregation)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/heygen-usage/summary")
async def get_heygen_usage_summary(
    year: Optional[int] = Query(default=None, description="Year (default: current year)"),
    month: Optional[int] = Query(default=None, ge=1, le=12, description="Month 1-12 (default: current month)"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return HeyGen usage and estimated cost for a given month.

    Returns:
        total_jobs: total number of localization jobs
        completed_jobs: successfully completed jobs
        failed_jobs: failed jobs
        skipped_jobs: skipped jobs (no API key)
        total_minutes: total billable minutes
        total_cost_usd: estimated total cost in USD
        monthly_budget_usd: configured budget limit (0 = disabled)
        over_budget: True if total_cost_usd exceeds budget
        per_language: breakdown by language code
    """
    now = datetime.now(tz=timezone.utc)
    target_year = year or now.year
    target_month = month or now.month

    # Date range for the target month
    from datetime import date
    import calendar
    _, last_day = calendar.monthrange(target_year, target_month)
    period_start = datetime(target_year, target_month, 1, tzinfo=timezone.utc)
    period_end = datetime(target_year, target_month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    result = await db.execute(
        select(HeyGenUsageRecord).where(
            HeyGenUsageRecord.created_at >= period_start,
            HeyGenUsageRecord.created_at <= period_end,
        )
    )
    records = list(result.scalars().all())

    total_jobs = len(records)
    completed = sum(1 for r in records if r.job_status == "completed")
    failed = sum(1 for r in records if r.job_status == "failed")
    skipped = sum(1 for r in records if r.job_status == "skipped")
    total_minutes = sum(r.minutes_processed or 0.0 for r in records)
    total_cost = sum(r.cost_usd or 0.0 for r in records)

    # Per-language breakdown
    lang_map: dict[str, dict] = {}
    for r in records:
        lc = r.language_code
        if lc not in lang_map:
            lang_map[lc] = {"jobs": 0, "minutes": 0.0, "cost_usd": 0.0}
        lang_map[lc]["jobs"] += 1
        lang_map[lc]["minutes"] += r.minutes_processed or 0.0
        lang_map[lc]["cost_usd"] += r.cost_usd or 0.0

    budget = settings.HEYGEN_MONTHLY_BUDGET_USD
    over_budget = budget > 0 and total_cost > budget

    return {
        "period": {"year": target_year, "month": target_month},
        "total_jobs": total_jobs,
        "completed_jobs": completed,
        "failed_jobs": failed,
        "skipped_jobs": skipped,
        "total_minutes": round(total_minutes, 3),
        "total_cost_usd": round(total_cost, 4),
        "cost_per_minute_usd": settings.HEYGEN_COST_PER_MINUTE_USD,
        "monthly_budget_usd": budget,
        "over_budget": over_budget,
        "per_language": {
            lc: {
                "jobs": data["jobs"],
                "minutes": round(data["minutes"], 3),
                "cost_usd": round(data["cost_usd"], 4),
            }
            for lc, data in lang_map.items()
        },
    }


@router.get("/heygen-usage/records")
async def list_heygen_usage_records(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    video_id: Optional[int] = None,
    language_code: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Paginated list of raw HeyGen usage records."""
    query = select(HeyGenUsageRecord).order_by(HeyGenUsageRecord.created_at.desc())

    if video_id is not None:
        query = query.where(HeyGenUsageRecord.video_id == video_id)
    if language_code:
        query = query.where(HeyGenUsageRecord.language_code == language_code.lower())

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    data_result = await db.execute(query.offset(offset).limit(limit))
    rows = list(data_result.scalars().all())

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [
            {
                "id": r.id,
                "video_id": r.video_id,
                "language_code": r.language_code,
                "provider_job_id": r.provider_job_id,
                "job_status": r.job_status,
                "source_duration_seconds": r.source_duration_seconds,
                "minutes_processed": r.minutes_processed,
                "cost_usd": r.cost_usd,
                "error_message": r.error_message,
                "created_at": str(r.created_at),
            }
            for r in rows
        ],
    }


# ============================================================
# Sprint 11 — Platform KPI Overview (11.4)
# ============================================================

@router.get("/kpi/overview")
async def get_kpi_overview(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Full-platform KPI snapshot: suppliers, buyers, RFQs, revenue."""
    total_suppliers = (await db.execute(select(func.count()).select_from(Supplier))).scalar_one()
    active_suppliers = (await db.execute(
        select(func.count()).select_from(Supplier).where(Supplier.is_active == True)
    )).scalar_one()
    verified_suppliers = (await db.execute(
        select(func.count()).select_from(Supplier).where(Supplier.is_verified == True)
    )).scalar_one()

    total_buyers = (await db.execute(select(func.count()).select_from(Buyer))).scalar_one()

    total_rfqs = (await db.execute(select(func.count()).select_from(RFQ))).scalar_one()
    open_rfqs = (await db.execute(
        select(func.count()).select_from(RFQ).where(RFQ.status == "open")
    )).scalar_one()

    # Subscription revenue breakdown
    sub_result = await db.execute(select(Subscription.plan_tier, func.count()).group_by(Subscription.plan_tier))
    sub_breakdown = {row[0]: row[1] for row in sub_result.all()}

    # Estimate MRR from active paid subscriptions
    TIER_PRICE = {
        "starter": settings.STRIPE_STARTER_PRICE_USD,
        "professional": settings.STRIPE_PROFESSIONAL_PRICE_USD,
        "enterprise": settings.STRIPE_ENTERPRISE_PRICE_USD,
    }
    mrr_usd = sum(
        sub_breakdown.get(tier, 0) * price for tier, price in TIER_PRICE.items()
    )

    return {
        "suppliers": {
            "total": total_suppliers,
            "active": active_suppliers,
            "verified": verified_suppliers,
        },
        "buyers": {"total": total_buyers},
        "rfqs": {"total": total_rfqs, "open": open_rfqs},
        "subscriptions": sub_breakdown,
        "mrr_usd": mrr_usd,
    }


# ============================================================
# Sprint 11 — Supplier Management (11.5)
# ============================================================

@router.get("/suppliers")
async def admin_list_suppliers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    plan_tier: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Paginated supplier list with filtering for admin management."""
    query = select(Supplier).order_by(Supplier.created_at.desc())
    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)
    if is_verified is not None:
        query = query.where(Supplier.is_verified == is_verified)
    if plan_tier:
        query = query.where(Supplier.subscription_tier == plan_tier)
    if search:
        query = query.where(Supplier.company_name.ilike(f"%{search}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return {
        "total": total,
        "page": page,
        "pages": max(1, -(-total // page_size)),
        "suppliers": [
            {
                "id": s.id,
                "company_name": s.company_name,
                "company_slug": s.company_slug,
                "country": s.country,
                "industry": s.industry,
                "is_active": s.is_active,
                "is_verified": s.is_verified,
                "subscription_tier": getattr(s, "subscription_tier", "free"),
                "created_at": str(s.created_at),
            }
            for s in rows
        ],
    }


class SupplierAdminUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


@router.patch("/suppliers/{supplier_id}")
async def admin_update_supplier(
    supplier_id: int,
    body: SupplierAdminUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify/unverify or activate/deactivate a supplier."""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalars().first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    if body.is_active is not None:
        supplier.is_active = body.is_active
    if body.is_verified is not None:
        supplier.is_verified = body.is_verified
    await db.commit()
    return {"supplier_id": supplier_id, "is_active": supplier.is_active, "is_verified": supplier.is_verified}


# ============================================================
# Sprint 11 — Buyer Management (11.6)
# ============================================================

@router.get("/buyers")
async def admin_list_buyers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Paginated buyer list for admin management."""
    query = select(Buyer).order_by(Buyer.created_at.desc())
    if is_active is not None:
        query = query.where(Buyer.is_active == is_active)
    if search:
        query = query.where(Buyer.company_name.ilike(f"%{search}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return {
        "total": total,
        "page": page,
        "pages": max(1, -(-total // page_size)),
        "buyers": [
            {
                "id": b.id,
                "company_name": b.company_name,
                "country": getattr(b, "country", None),
                "is_active": getattr(b, "is_active", True),
                "created_at": str(b.created_at),
            }
            for b in rows
        ],
    }


class BuyerAdminUpdateRequest(BaseModel):
    is_active: bool


@router.patch("/buyers/{buyer_id}/block")
async def admin_block_buyer(
    buyer_id: int,
    body: BuyerAdminUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Block or unblock a buyer account."""
    result = await db.execute(select(Buyer).where(Buyer.id == buyer_id))
    buyer = result.scalars().first()
    if not buyer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer not found")
    buyer.is_active = body.is_active
    await db.commit()
    return {"buyer_id": buyer_id, "is_active": buyer.is_active}


# ============================================================
# Sprint 11 — AI Content Review Queue (11.7)
# ============================================================

@router.get("/content/review-queue")
async def admin_content_review_queue(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    review_status: Optional[str] = Query(default="pending"),
    content_type: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Paginated AI-generated content pending quality review."""
    query = select(ContentItem).order_by(ContentItem.created_at.desc())
    if review_status:
        query = query.where(ContentItem.review_status == review_status)
    if content_type:
        query = query.where(ContentItem.content_type == content_type)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return {
        "total": total,
        "page": page,
        "pages": max(1, -(-total // page_size)),
        "items": [
            {
                "id": c.id,
                "supplier_id": c.supplier_id,
                "content_type": c.content_type,
                "title": getattr(c, "title", None),
                "body_preview": (getattr(c, "body", None) or "")[:200],
                "review_status": getattr(c, "review_status", "pending"),
                "review_note": getattr(c, "review_note", None),
                "created_at": str(c.created_at),
            }
            for c in rows
        ],
    }


class ContentReviewRequest(BaseModel):
    review_status: str   # approved | rejected | flagged
    review_note: Optional[str] = None


@router.patch("/content/{content_id}/review")
async def admin_review_content(
    content_id: int,
    body: ContentReviewRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Approve, reject, or flag an AI-generated content item."""
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found")
    if body.review_status not in ("approved", "rejected", "flagged", "pending"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review_status")
    item.review_status = body.review_status
    item.review_note = body.review_note
    item.reviewed_by = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "content_id": content_id,
        "review_status": item.review_status,
        "review_note": item.review_note,
    }


# ============================================================
# Sprint 11 — Outbound Health Dashboard (11.8)
# ============================================================

@router.get("/outbound/health")
async def admin_outbound_health(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Outbound system health: LinkedIn ban rate + Email bounce rate."""
    # LinkedIn contacts
    li_total = (await db.execute(select(func.count()).select_from(OutboundContact))).scalar_one()
    li_connected = (await db.execute(
        select(func.count()).select_from(OutboundContact).where(OutboundContact.status == "connected")
    )).scalar_one()
    li_banned = (await db.execute(
        select(func.count()).select_from(OutboundContact).where(OutboundContact.status == "blocked")
    )).scalar_one()

    # Email sequences
    email_total = (await db.execute(select(func.count()).select_from(EmailSequence))).scalar_one()
    email_active = (await db.execute(
        select(func.count()).select_from(EmailSequence).where(EmailSequence.status == "active")
    )).scalar_one()
    email_bounced = (await db.execute(
        select(func.count()).select_from(EmailSequence).where(EmailSequence.status == "bounced")
    )).scalar_one()

    li_ban_rate = round(li_banned / li_total, 4) if li_total > 0 else 0.0
    email_bounce_rate = round(email_bounced / email_total, 4) if email_total > 0 else 0.0

    return {
        "linkedin": {
            "total_contacts": li_total,
            "connected": li_connected,
            "blocked": li_banned,
            "ban_rate": li_ban_rate,
            "daily_limit": settings.LINKEDIN_DAILY_CONNECTION_LIMIT,
            "alert": li_ban_rate > 0.05,  # alert if > 5%
        },
        "email": {
            "total_sequences": email_total,
            "active": email_active,
            "bounced": email_bounced,
            "bounce_rate": email_bounce_rate,
            "daily_limit": settings.EMAIL_DAILY_SEND_LIMIT,
            "alert": email_bounce_rate > settings.EMAIL_BOUNCE_RATE_THRESHOLD,
        },
    }


# ============================================================
# Sprint 11 — API Usage Dashboard (11.9)
# ============================================================

@router.get("/api-usage/summary")
async def admin_api_usage_summary(
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Monthly API usage and cost breakdown per service."""
    import calendar as cal_mod
    now = datetime.now(tz=timezone.utc)
    y = year or now.year
    m = month or now.month
    _, last_day = cal_mod.monthrange(y, m)
    period_start = datetime(y, m, 1, tzinfo=timezone.utc)
    period_end = datetime(y, m, last_day, 23, 59, 59, tzinfo=timezone.utc)

    # Include HeyGen usage as a service aggregation
    heygen_result = await db.execute(
        select(
            func.count(HeyGenUsageRecord.id),
            func.sum(HeyGenUsageRecord.cost_usd),
            func.sum(HeyGenUsageRecord.minutes_processed),
        ).where(
            HeyGenUsageRecord.created_at >= period_start,
            HeyGenUsageRecord.created_at <= period_end,
        )
    )
    hg_count, hg_cost, hg_minutes = heygen_result.one()

    # Generic API usage records
    usage_result = await db.execute(
        select(
            ApiUsageRecord.service_name,
            func.count(ApiUsageRecord.id),
            func.sum(ApiUsageRecord.cost_usd),
            func.sum(ApiUsageRecord.units),
        ).where(
            ApiUsageRecord.recorded_at >= period_start,
            ApiUsageRecord.recorded_at <= period_end,
        ).group_by(ApiUsageRecord.service_name)
    )
    per_service: dict = {}
    for service, count, cost, units in usage_result.all():
        per_service[service] = {
            "calls": count,
            "cost_usd": float(cost or 0),
            "units": int(units or 0),
        }

    # Add HeyGen
    per_service["heygen"] = {
        "calls": hg_count or 0,
        "cost_usd": float(hg_cost or 0),
        "units": float(hg_minutes or 0),
        "unit_type": "minutes",
    }

    total_cost = sum(s["cost_usd"] for s in per_service.values())
    return {
        "period": {"year": y, "month": m},
        "total_cost_usd": round(total_cost, 4),
        "per_service": per_service,
    }


# ============================================================
# Sprint 11 — System Settings (11.10)
# ============================================================

@router.get("/settings")
async def admin_get_settings(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return all system settings as a key-value dict."""
    rows = (await db.execute(select(SystemSetting).order_by(SystemSetting.key))).scalars().all()
    return {
        "settings": [
            {
                "key": s.key,
                "value": s.value,
                "description": s.description,
                "updated_at": str(s.updated_at),
            }
            for s in rows
        ]
    }


class SystemSettingUpsertRequest(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


@router.put("/settings")
async def admin_upsert_setting(
    body: SystemSettingUpsertRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create or update a system setting."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == body.key))
    setting = result.scalars().first()
    if setting:
        setting.value = body.value
        if body.description is not None:
            setting.description = body.description
        setting.updated_by = current_user.id
    else:
        setting = SystemSetting(
            key=body.key,
            value=body.value,
            description=body.description,
            updated_by=current_user.id,
        )
        db.add(setting)
    await db.commit()
    return {"key": setting.key, "value": setting.value}


@router.delete("/settings/{key}")
async def admin_delete_setting(
    key: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a system setting by key."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalars().first()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    await db.delete(setting)
    await db.commit()
    return {"deleted": key}

