"""Admin endpoints: HeyGen usage / cost tracking — Sprint 6"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User
from app.models.heygen_usage import HeyGenUsageRecord
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
