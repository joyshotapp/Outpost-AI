"""Analytics & KPI endpoints — Sprint 12 (Task 12.1 + 12.6).

Endpoints:
  GET  /analytics/kpi                          supplier KPI overview
  GET  /analytics/rfq-trend                    RFQ submission trend (30/90/365 days)
  GET  /analytics/lead-score-distribution      lead grade breakdown (A/B/C)
  GET  /analytics/visitor-trend                visitor intent trend
  GET  /analytics/outbound-performance         outbound campaign performance
  GET  /analytics/content-reach                content item reach / engagement
  GET  /analytics/export/leads                 export leads CSV or JSON   (12.6)
  GET  /analytics/export/rfqs                  export RFQs CSV or JSON    (12.6)
  GET  /analytics/export/analytics             export analytics snapshot  (12.6)
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, RFQ, Supplier
from app.models.outbound_contact import OutboundContact
from app.models.outbound_campaign import OutboundCampaign
from app.models.email_sequence import EmailSequence
from app.models.content_item import ContentItem
from app.models.visitor_event import VisitorEvent

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _window_start(days: int) -> datetime:
    # DB timestamp columns are stored without timezone in this project.
    # Use naive UTC datetime for query boundaries to avoid asyncpg
    # "can't subtract offset-naive and offset-aware datetimes" errors.
    return datetime.utcnow() - timedelta(days=days)


def _supplier_id_from_user(user: User) -> int:
    """Return supplier_id from current user (supplier role only)."""
    sid = getattr(user, "supplier_profile_id", None) or getattr(user, "id", None)
    if not sid:
        raise HTTPException(status_code=403, detail="Supplier profile required")
    return int(sid)


# ─────────────────────────────────────────────────────────────────────────────
# 12.1  KPI Overview
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/kpi")
async def get_kpi_overview(
    window_days: int = Query(default=30, ge=7, le=365, description="Look-back window in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return key performance indicators for the supplier's dashboard.

    Returns aggregate counts across the requested time window:
    - total_rfqs, new_rfqs, rfq_by_grade
    - total_visitors, high_intent_visitors
    - outbound_contacts, outbound_replies, outbound_reply_rate
    - content_items, total_content_reach
    - conversion_rate  (RFQs / visitors * 100)
    """
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    # ── RFQ counts ────────────────────────────────────────────────────────
    rfq_result = await db.execute(
        select(
            func.count(RFQ.id).label("total"),
            func.sum(
                cast(RFQ.lead_grade == "A", Integer)
                if hasattr(RFQ, "lead_grade") else 0
            ).label("grade_a"),
        ).where(
            RFQ.supplier_id == supplier_id,
            RFQ.created_at >= since,
        )
    )
    rfq_row = rfq_result.one_or_none()
    total_rfqs = int(rfq_row[0]) if rfq_row else 0

    # Grade breakdown
    grade_result = await db.execute(
        select(RFQ.lead_grade, func.count(RFQ.id).label("cnt"))
        .where(RFQ.supplier_id == supplier_id, RFQ.created_at >= since)
        .group_by(RFQ.lead_grade)
    )
    rfq_by_grade: dict[str, int] = {}
    for row in grade_result.all():
        if row[0]:
            rfq_by_grade[str(row[0])] = int(row[1])

    # ── Visitor counts ────────────────────────────────────────────────────
    visitor_result = await db.execute(
        select(func.count(VisitorEvent.id))
        .where(
            VisitorEvent.supplier_id == supplier_id,
            VisitorEvent.created_at >= since,
        )
    )
    total_visitors = int(visitor_result.scalar() or 0)

    high_intent_result = await db.execute(
        select(func.count(VisitorEvent.id))
        .where(
            VisitorEvent.supplier_id == supplier_id,
            VisitorEvent.created_at >= since,
            VisitorEvent.intent_score >= 70,
        )
    )
    high_intent_visitors = int(high_intent_result.scalar() or 0)

    # ── Outbound performance ──────────────────────────────────────────────
    outbound_result = await db.execute(
        select(
            func.count(EmailSequence.id).label("total"),
            func.sum(cast(EmailSequence.reply_received == True, Integer)).label("replies"),
        ).where(
            EmailSequence.supplier_id == supplier_id,
            EmailSequence.created_at >= since,
        )
    )
    ob_row = outbound_result.one_or_none()
    outbound_contacts = int(ob_row[0]) if ob_row else 0
    outbound_replies = int(ob_row[1]) if ob_row and ob_row[1] else 0
    reply_rate = round(outbound_replies / outbound_contacts * 100, 1) if outbound_contacts else 0.0

    # ── Content stats ─────────────────────────────────────────────────────
    content_result = await db.execute(
        select(
            func.count(ContentItem.id).label("total"),
            func.sum(ContentItem.impressions).label("reach"),
        ).where(
            ContentItem.supplier_id == supplier_id,
            ContentItem.created_at >= since,
        )
    )
    ct_row = content_result.one_or_none()
    content_items = int(ct_row[0]) if ct_row else 0
    total_content_reach = int(ct_row[1]) if ct_row and ct_row[1] else 0

    # ── Conversion rate ───────────────────────────────────────────────────
    conversion_rate = round(total_rfqs / total_visitors * 100, 2) if total_visitors else 0.0

    return {
        "window_days": window_days,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "rfq": {
            "total": total_rfqs,
            "by_grade": rfq_by_grade,
        },
        "visitors": {
            "total": total_visitors,
            "high_intent": high_intent_visitors,
        },
        "outbound": {
            "contacts": outbound_contacts,
            "replies": outbound_replies,
            "reply_rate_pct": reply_rate,
        },
        "content": {
            "items": content_items,
            "total_reach": total_content_reach,
        },
        "conversion_rate_pct": conversion_rate,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12.1  RFQ Trend (time-series)
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/rfq-trend")
async def get_rfq_trend(
    window_days: int = Query(default=30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Daily RFQ submission counts for charting."""
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    result = await db.execute(
        select(
            func.date(RFQ.created_at).label("day"),
            func.count(RFQ.id).label("count"),
        )
        .where(RFQ.supplier_id == supplier_id, RFQ.created_at >= since)
        .group_by(func.date(RFQ.created_at))
        .order_by(func.date(RFQ.created_at))
    )
    rows = result.all()
    series = [{"date": str(row[0]), "count": int(row[1])} for row in rows]
    return {"window_days": window_days, "series": series}


# ─────────────────────────────────────────────────────────────────────────────
# 12.1  Lead Score Distribution
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/lead-score-distribution")
async def get_lead_score_distribution(
    window_days: int = Query(default=90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lead grade distribution (A/B/C/unscored) for pie/bar chart."""
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    result = await db.execute(
        select(RFQ.lead_grade, func.count(RFQ.id).label("cnt"))
        .where(RFQ.supplier_id == supplier_id, RFQ.created_at >= since)
        .group_by(RFQ.lead_grade)
    )
    distribution: dict[str, int] = {"A": 0, "B": 0, "C": 0, "unscored": 0}
    for row in result.all():
        grade = str(row[0]).upper() if row[0] else "unscored"
        key = grade if grade in ("A", "B", "C") else "unscored"
        distribution[key] = int(row[1])

    total = sum(distribution.values())
    buckets = []
    for grade, cnt in distribution.items():
        buckets.append({
            "grade": grade,
            "count": cnt,
            "pct": round(cnt / total * 100, 1) if total else 0,
        })
    return {"window_days": window_days, "total": total, "distribution": buckets}


# ─────────────────────────────────────────────────────────────────────────────
# 12.1  Visitor Trend
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/visitor-trend")
async def get_visitor_trend(
    window_days: int = Query(default=30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Daily unique visitor event counts."""
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    result = await db.execute(
        select(
            func.date(VisitorEvent.created_at).label("day"),
            func.count(VisitorEvent.id).label("total"),
            func.sum(cast(VisitorEvent.intent_score >= 70, Integer)).label("high_intent"),
        )
        .where(VisitorEvent.supplier_id == supplier_id, VisitorEvent.created_at >= since)
        .group_by(func.date(VisitorEvent.created_at))
        .order_by(func.date(VisitorEvent.created_at))
    )
    series = [
        {"date": str(r[0]), "total": int(r[1]), "high_intent": int(r[2] or 0)}
        for r in result.all()
    ]
    return {"window_days": window_days, "series": series}


# ─────────────────────────────────────────────────────────────────────────────
# 12.1  Outbound Performance
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/outbound-performance")
async def get_outbound_performance(
    window_days: int = Query(default=30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Outbound email/LinkedIn performance summary."""
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    email_result = await db.execute(
        select(
            func.count(EmailSequence.id).label("total"),
            func.sum(EmailSequence.emails_sent).label("sent"),
            func.sum(EmailSequence.emails_opened).label("opened"),
            func.sum(EmailSequence.emails_clicked).label("clicked"),
            func.sum(cast(EmailSequence.reply_received, Integer)).label("replied"),
            func.sum(cast(EmailSequence.is_bounced, Integer)).label("bounced"),
        ).where(
            EmailSequence.supplier_id == supplier_id,
            EmailSequence.created_at >= since,
        )
    )
    row = email_result.one_or_none()

    total    = int(row[0]) if row and row[0] else 0
    sent     = int(row[1]) if row and row[1] else 0
    opened   = int(row[2]) if row and row[2] else 0
    clicked  = int(row[3]) if row and row[3] else 0
    replied  = int(row[4]) if row and row[4] else 0
    bounced  = int(row[5]) if row and row[5] else 0

    def pct(num: int, denom: int) -> float:
        return round(num / denom * 100, 1) if denom else 0.0

    return {
        "window_days": window_days,
        "email": {
            "contacts": total,
            "emails_sent": sent,
            "open_rate_pct": pct(opened, sent),
            "click_rate_pct": pct(clicked, sent),
            "reply_rate_pct": pct(replied, total),
            "bounce_rate_pct": pct(bounced, total),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12.1  Content Reach
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/content-reach")
async def get_content_reach(
    window_days: int = Query(default=30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Content item engagement / reach breakdown by platform."""
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    result = await db.execute(
        select(
            ContentItem.platform,
            func.count(ContentItem.id).label("items"),
            func.sum(ContentItem.impressions).label("reach"),
            func.sum(ContentItem.engagements).label("engagement"),
        )
        .where(ContentItem.supplier_id == supplier_id, ContentItem.created_at >= since)
        .group_by(ContentItem.platform)
        .order_by(func.sum(ContentItem.impressions).desc())
    )
    platforms = [
        {
            "platform": str(row[0]),
            "items": int(row[1]),
            "reach": int(row[2] or 0),
            "engagement": int(row[3] or 0),
        }
        for row in result.all()
    ]
    total_reach = sum(p["reach"] for p in platforms)
    total_engagement = sum(p["engagement"] for p in platforms)
    return {
        "window_days": window_days,
        "total_reach": total_reach,
        "total_engagement": total_engagement,
        "by_platform": platforms,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12.6  Data Export APIs
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/export/leads")
async def export_leads(
    fmt: str = Query(default="csv", regex="^(csv|json)$"),
    window_days: int = Query(default=90, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export outbound leads (contacts + email sequence status) as CSV or JSON."""
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    result = await db.execute(
        select(EmailSequence).where(
            EmailSequence.supplier_id == supplier_id,
            EmailSequence.created_at >= since,
        ).order_by(EmailSequence.created_at.desc())
    )
    leads = list(result.scalars().all())

    fields = [
        "id", "email", "full_name", "company_name", "status",
        "current_step", "emails_sent", "emails_opened", "reply_received",
        "is_bounced", "created_at",
    ]

    if fmt == "json":
        data = [
            {f: str(getattr(lead, f, "")) for f in fields}
            for lead in leads
        ]
        return StreamingResponse(
            io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=leads.json"},
        )

    # CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for lead in leads:
        writer.writerow({f: str(getattr(lead, f, "")) for f in fields})

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/export/rfqs")
async def export_rfqs(
    fmt: str = Query(default="csv", regex="^(csv|json)$"),
    window_days: int = Query(default=90, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export RFQs with lead scores as CSV or JSON."""
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    result = await db.execute(
        select(RFQ).where(
            RFQ.supplier_id == supplier_id,
            RFQ.created_at >= since,
        ).order_by(RFQ.created_at.desc())
    )
    rfqs = list(result.scalars().all())

    fields = [
        "id", "title", "status", "lead_grade", "lead_score",
        "buyer_email", "quantity", "delivery_deadline", "created_at",
    ]

    if fmt == "json":
        data = [
            {f: str(getattr(rfq, f, "")) for f in fields}
            for rfq in rfqs
        ]
        return StreamingResponse(
            io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=rfqs.json"},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for rfq in rfqs:
        writer.writerow({f: str(getattr(rfq, f, "")) for f in fields})

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rfqs.csv"},
    )


@router.get("/export/analytics")
async def export_analytics_snapshot(
    fmt: str = Query(default="json", regex="^(csv|json)$"),
    window_days: int = Query(default=30, ge=7),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export a full analytics snapshot (KPI summary + all time-series) as JSON or CSV."""
    # Reuse the KPI endpoint logic inline for the snapshot
    supplier_id = _supplier_id_from_user(current_user)
    since = _window_start(window_days)

    # RFQ summary
    rfq_r = await db.execute(
        select(RFQ.lead_grade, func.count(RFQ.id))
        .where(RFQ.supplier_id == supplier_id, RFQ.created_at >= since)
        .group_by(RFQ.lead_grade)
    )
    rfq_by_grade = {str(r[0] or "unscored"): int(r[1]) for r in rfq_r.all()}

    # Visitor summary
    vis_r = await db.execute(
        select(func.count(VisitorEvent.id))
        .where(VisitorEvent.supplier_id == supplier_id, VisitorEvent.created_at >= since)
    )
    total_visitors = int(vis_r.scalar() or 0)

    # Email summary
    email_r = await db.execute(
        select(func.count(EmailSequence.id), func.sum(cast(EmailSequence.reply_received, Integer)))
        .where(EmailSequence.supplier_id == supplier_id, EmailSequence.created_at >= since)
    )
    em_row = email_r.one_or_none()

    snapshot = {
        "exported_at": datetime.now(tz=timezone.utc).isoformat(),
        "supplier_id": supplier_id,
        "window_days": window_days,
        "rfq_by_grade": rfq_by_grade,
        "total_rfqs": sum(rfq_by_grade.values()),
        "total_visitors": total_visitors,
        "outbound_contacts": int(em_row[0]) if em_row and em_row[0] else 0,
        "outbound_replies": int(em_row[1]) if em_row and em_row[1] else 0,
    }

    if fmt == "json":
        return StreamingResponse(
            io.BytesIO(json.dumps(snapshot, ensure_ascii=False, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=analytics_snapshot.json"},
        )

    # CSV: flatten to key-value pairs
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value"])
    for k, v in snapshot.items():
        writer.writerow([k, json.dumps(v) if isinstance(v, dict) else str(v)])

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_snapshot.csv"},
    )
