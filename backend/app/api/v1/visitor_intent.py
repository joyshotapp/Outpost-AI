"""Visitor intent tracking and dashboard API endpoints."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Notification, Supplier, User, VisitorEvent
from app.schemas import (
    VisitorIntentBenchmarkResponse,
    VisitorIntentEventCreateRequest,
    VisitorIntentEventCreateResponse,
    VisitorIntentEventListResponse,
    VisitorIntentOpsMetricsResponse,
    VisitorIntentProviderBreakdown,
    VisitorIntentQualityGates,
    VisitorIntentRateMetrics,
    VisitorIntentSummaryResponse,
)
from app.tasks.visitor_intent import process_visitor_intent_event

router = APIRouter(prefix="/visitor-intent", tags=["visitor-intent"])


def _verify_webhook_signature(secret: str | None, body: bytes, signature: str | None) -> bool:
    if not secret or not signature:
        return False

    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    candidates = {digest, f"sha256={digest}", f"v1={digest}"}
    received = signature.strip()

    return any(hmac.compare_digest(received, candidate) for candidate in candidates)


def _normalize_country(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().upper()
    if len(normalized) >= 2:
        return normalized[:2]
    return None


def _normalize_rb2b_payload(payload: dict) -> VisitorIntentEventCreateRequest:
    supplier_id = payload.get("supplier_id")
    if supplier_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="supplier_id is required")

    session_id = payload.get("visitor_session_id") or payload.get("session_id") or payload.get("visitor_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="visitor session id is required")

    raw_event_data = payload.get("event_data") if isinstance(payload.get("event_data"), dict) else {}
    event_data = {
        **raw_event_data,
        "provider": "rb2b",
        "raw_event": payload.get("event_name") or payload.get("event_type"),
    }

    return VisitorIntentEventCreateRequest(
        supplier_id=int(supplier_id),
        visitor_session_id=str(session_id),
        event_type=str(payload.get("event_type") or "page_view"),
        page_url=payload.get("page_url") or payload.get("url"),
        event_data=event_data,
        session_duration_seconds=payload.get("session_duration_seconds"),
        visitor_email=payload.get("email") or payload.get("visitor_email"),
        visitor_company=payload.get("company") or payload.get("company_name"),
        visitor_country=_normalize_country(payload.get("country") or payload.get("visitor_country")),
        consent_given=True,
    )


def _normalize_leadfeeder_payload(payload: dict) -> VisitorIntentEventCreateRequest:
    supplier_id = payload.get("supplier_id")
    if supplier_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="supplier_id is required")

    company = payload.get("company") if isinstance(payload.get("company"), dict) else {}
    contact = payload.get("contact") if isinstance(payload.get("contact"), dict) else {}

    session_id = (
        payload.get("visitor_session_id")
        or payload.get("session_id")
        or payload.get("visit_id")
        or company.get("id")
    )
    if not session_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="visitor session id is required")

    event_data = {
        "provider": "leadfeeder",
        "leadfeeder_event": payload.get("event_name") or payload.get("event_type"),
        "company_domain": company.get("domain"),
        "company_industry": company.get("industry"),
    }

    return VisitorIntentEventCreateRequest(
        supplier_id=int(supplier_id),
        visitor_session_id=str(session_id),
        event_type=str(payload.get("event_type") or "company_identified"),
        page_url=payload.get("page_url") or payload.get("url"),
        event_data=event_data,
        session_duration_seconds=payload.get("session_duration_seconds"),
        visitor_email=contact.get("email") or payload.get("visitor_email"),
        visitor_company=company.get("name") or payload.get("visitor_company"),
        visitor_country=_normalize_country(company.get("country") or payload.get("visitor_country")),
        consent_given=True,
    )


async def _persist_event_and_queue_scoring(
    request: VisitorIntentEventCreateRequest,
    db: AsyncSession,
) -> VisitorIntentEventCreateResponse:
    if not request.consent_given:
        return VisitorIntentEventCreateResponse(
            accepted=False,
            queued_for_scoring=False,
            reason="tracking_skipped_without_cookie_consent",
        )

    event = VisitorEvent(
        supplier_id=request.supplier_id,
        visitor_session_id=request.visitor_session_id,
        visitor_email=request.visitor_email,
        visitor_company=request.visitor_company,
        visitor_country=request.visitor_country,
        event_type=request.event_type,
        page_url=request.page_url,
        event_data=json.dumps(request.event_data, ensure_ascii=False) if request.event_data else None,
        session_duration_seconds=request.session_duration_seconds,
        intent_score=None,
        intent_level=None,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    process_visitor_intent_event.delay(event.id)

    return VisitorIntentEventCreateResponse(
        accepted=True,
        queued_for_scoring=True,
        event_id=event.id,
    )


async def _resolve_supplier_for_user(current_user: User, db: AsyncSession) -> Supplier:
    if current_user.role.value != "supplier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can access visitor intent dashboard",
        )

    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.user_id == current_user.id)
    )
    supplier = supplier_result.scalars().first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier profile not found",
        )
    return supplier


@router.post("/events", response_model=VisitorIntentEventCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_visitor_event(
    request: VisitorIntentEventCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> VisitorIntentEventCreateResponse:
    return await _persist_event_and_queue_scoring(request, db)


@router.post("/webhooks/rb2b", response_model=VisitorIntentEventCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_rb2b_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_rb2b_signature: Optional[str] = Header(default=None, alias="X-RB2B-Signature"),
) -> VisitorIntentEventCreateResponse:
    if not settings.RB2B_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RB2B webhook secret not configured",
        )

    raw_body = await request.body()
    if not _verify_webhook_signature(settings.RB2B_WEBHOOK_SECRET, raw_body, x_rb2b_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid RB2B signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc

    normalized_request = _normalize_rb2b_payload(payload)
    return await _persist_event_and_queue_scoring(normalized_request, db)


@router.post(
    "/webhooks/leadfeeder",
    response_model=VisitorIntentEventCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_leadfeeder_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_leadfeeder_signature: Optional[str] = Header(default=None, alias="X-Leadfeeder-Signature"),
) -> VisitorIntentEventCreateResponse:
    if not settings.LEADFEEDER_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Leadfeeder webhook secret not configured",
        )

    raw_body = await request.body()
    if not _verify_webhook_signature(settings.LEADFEEDER_WEBHOOK_SECRET, raw_body, x_leadfeeder_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Leadfeeder signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc

    normalized_request = _normalize_leadfeeder_payload(payload)
    return await _persist_event_and_queue_scoring(normalized_request, db)


@router.get("/events", response_model=list[VisitorIntentEventListResponse])
async def list_visitor_events(
    level: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VisitorIntentEventListResponse]:
    supplier = await _resolve_supplier_for_user(current_user, db)

    query = select(VisitorEvent).filter(VisitorEvent.supplier_id == supplier.id)
    if level:
        query = query.filter(VisitorEvent.intent_level == level)

    result = await db.execute(query.order_by(desc(VisitorEvent.created_at)).limit(limit))
    events = result.scalars().all()

    return [VisitorIntentEventListResponse.model_validate(item) for item in events]


@router.get("/summary", response_model=VisitorIntentSummaryResponse)
async def get_visitor_intent_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisitorIntentSummaryResponse:
    supplier = await _resolve_supplier_for_user(current_user, db)

    total_events_q = await db.execute(
        select(func.count(VisitorEvent.id)).filter(VisitorEvent.supplier_id == supplier.id)
    )
    total_events = int(total_events_q.scalar() or 0)

    high_q = await db.execute(
        select(func.count(VisitorEvent.id)).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.intent_level == "high",
        )
    )
    high_intent_count = int(high_q.scalar() or 0)

    medium_q = await db.execute(
        select(func.count(VisitorEvent.id)).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.intent_level == "medium",
        )
    )
    medium_intent_count = int(medium_q.scalar() or 0)

    avg_q = await db.execute(
        select(func.avg(VisitorEvent.intent_score)).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.intent_score.is_not(None),
        )
    )
    avg_intent_score = float(avg_q.scalar() or 0)

    latest_q = await db.execute(
        select(VisitorEvent).filter(VisitorEvent.supplier_id == supplier.id).order_by(desc(VisitorEvent.created_at)).limit(1)
    )
    latest = latest_q.scalars().first()

    return VisitorIntentSummaryResponse(
        supplier_id=supplier.id,
        total_events=total_events,
        high_intent_count=high_intent_count,
        medium_intent_count=medium_intent_count,
        avg_intent_score=round(avg_intent_score, 2),
        latest_event_at=latest.created_at if latest else None,
        generated_at=datetime.utcnow(),
    )


@router.get("/benchmark", response_model=VisitorIntentBenchmarkResponse)
async def get_visitor_intent_benchmark(
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisitorIntentBenchmarkResponse:
    supplier = await _resolve_supplier_for_user(current_user, db)

    since = datetime.utcnow() - timedelta(days=days)
    events_result = await db.execute(
        select(VisitorEvent).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.created_at >= since,
        )
    )
    events = events_result.scalars().all()
    total_events = len(events)

    rb2b_events = 0
    leadfeeder_events = 0
    unidentified_provider_events = 0
    email_identified = 0
    company_identified = 0
    country_identified = 0
    intent_scored = 0
    high_or_medium_intent = 0

    for event in events:
        provider = None
        if event.event_data:
            try:
                parsed = json.loads(event.event_data)
                provider = (parsed or {}).get("provider")
            except json.JSONDecodeError:
                provider = None

        if provider == "rb2b":
            rb2b_events += 1
        elif provider == "leadfeeder":
            leadfeeder_events += 1
        else:
            unidentified_provider_events += 1

        if event.visitor_email:
            email_identified += 1
        if event.visitor_company:
            company_identified += 1
        if event.visitor_country:
            country_identified += 1
        if event.intent_score is not None and event.intent_level:
            intent_scored += 1
        if event.intent_level in {"high", "medium"}:
            high_or_medium_intent += 1

    denominator = max(1, total_events)
    provider_coverage_rate = (rb2b_events + leadfeeder_events) / denominator
    email_identified_rate = email_identified / denominator
    company_identified_rate = company_identified / denominator
    country_identified_rate = country_identified / denominator
    intent_scored_rate = intent_scored / denominator
    high_or_medium_intent_rate = high_or_medium_intent / denominator

    provider_coverage_pass = provider_coverage_rate >= 0.70
    identification_pass = (
        email_identified_rate >= 0.50
        and company_identified_rate >= 0.50
        and country_identified_rate >= 0.50
    )
    scoring_pass = intent_scored_rate >= 0.95
    overall_pass = provider_coverage_pass and identification_pass and scoring_pass

    return VisitorIntentBenchmarkResponse(
        supplier_id=supplier.id,
        window_days=days,
        total_events=total_events,
        provider_breakdown=VisitorIntentProviderBreakdown(
            rb2b_events=rb2b_events,
            leadfeeder_events=leadfeeder_events,
            unidentified_provider_events=unidentified_provider_events,
        ),
        rates=VisitorIntentRateMetrics(
            email_identified_rate=round(email_identified_rate, 4),
            company_identified_rate=round(company_identified_rate, 4),
            country_identified_rate=round(country_identified_rate, 4),
            intent_scored_rate=round(intent_scored_rate, 4),
            high_or_medium_intent_rate=round(high_or_medium_intent_rate, 4),
            provider_coverage_rate=round(provider_coverage_rate, 4),
        ),
        quality_gates=VisitorIntentQualityGates(
            provider_coverage_pass=provider_coverage_pass,
            identification_pass=identification_pass,
            scoring_pass=scoring_pass,
            overall_pass=overall_pass,
        ),
        generated_at=datetime.utcnow(),
    )


@router.get("/ops-metrics", response_model=VisitorIntentOpsMetricsResponse)
async def get_visitor_intent_ops_metrics(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisitorIntentOpsMetricsResponse:
    supplier = await _resolve_supplier_for_user(current_user, db)
    since = datetime.utcnow() - timedelta(hours=hours)

    total_q = await db.execute(
        select(func.count(VisitorEvent.id)).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.created_at >= since,
        )
    )
    total_events = int(total_q.scalar() or 0)

    high_q = await db.execute(
        select(func.count(VisitorEvent.id)).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.created_at >= since,
            VisitorEvent.intent_level == "high",
        )
    )
    high_intent_events = int(high_q.scalar() or 0)

    medium_q = await db.execute(
        select(func.count(VisitorEvent.id)).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.created_at >= since,
            VisitorEvent.intent_level == "medium",
        )
    )
    medium_intent_events = int(medium_q.scalar() or 0)

    unread_q = await db.execute(
        select(func.count(Notification.id)).filter(
            Notification.supplier_id == supplier.id,
            Notification.notification_type == "high_intent_visitor",
            Notification.is_read == 0,
        )
    )
    unread_high_intent_notifications = int(unread_q.scalar() or 0)

    avg_q = await db.execute(
        select(func.avg(VisitorEvent.intent_score)).filter(
            VisitorEvent.supplier_id == supplier.id,
            VisitorEvent.created_at >= since,
            VisitorEvent.intent_score.is_not(None),
        )
    )
    avg_intent_score = float(avg_q.scalar() or 0.0)

    alert_high_intent_spike = high_intent_events >= 10
    alert_unread_backlog = unread_high_intent_notifications >= 15

    return VisitorIntentOpsMetricsResponse(
        supplier_id=supplier.id,
        window_hours=hours,
        total_events=total_events,
        high_intent_events=high_intent_events,
        medium_intent_events=medium_intent_events,
        unread_high_intent_notifications=unread_high_intent_notifications,
        avg_intent_score=round(avg_intent_score, 2),
        alert_high_intent_spike=alert_high_intent_spike,
        alert_unread_backlog=alert_unread_backlog,
        generated_at=datetime.utcnow(),
    )
