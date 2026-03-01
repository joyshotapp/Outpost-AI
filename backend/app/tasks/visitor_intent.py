"""Celery tasks for visitor intent processing."""

import asyncio
import json
import logging
from typing import Any

from celery import shared_task

from app.database import async_session_maker
from app.models import Notification, VisitorEvent
from app.services.visitor_enrichment import get_visitor_enrichment_service
from app.services.visitor_intent import get_visitor_intent_service

try:
    from app.socket_server import emit_supplier_notification
except Exception:
    emit_supplier_notification = None

from app.services.slack import get_slack_service

logger = logging.getLogger(__name__)


async def _send_websocket_with_retry(supplier_id: int, payload: dict, max_attempts: int = 3) -> dict:
    if emit_supplier_notification is None:
        return {"success": True, "skipped": True, "reason": "socket server unavailable"}

    last_error: str | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            await emit_supplier_notification(supplier_id, payload)
            return {"success": True, "attempt": attempt}
        except Exception as exc:
            last_error = str(exc)
            if attempt < max_attempts:
                await asyncio.sleep(0.25 * (2 ** (attempt - 1)))

    return {"success": False, "error": last_error or "unknown websocket error"}


async def _send_slack_with_retry(
    supplier_id: int,
    visitor_session_id: str,
    event_type: str,
    intent_score: int,
    page_url: str | None,
    visitor_company: str | None,
    max_attempts: int = 3,
) -> dict:
    slack_service = get_slack_service()
    last_result: dict[str, Any] = {"success": False, "error": "unknown"}

    for attempt in range(1, max_attempts + 1):
        result = await slack_service.send_high_intent_visitor_notification(
            supplier_id=supplier_id,
            visitor_session_id=visitor_session_id,
            event_type=event_type,
            intent_score=intent_score,
            page_url=page_url,
            visitor_company=visitor_company,
        )
        last_result = result

        if result.get("success") or result.get("skipped"):
            return {**result, "attempt": attempt}

        if attempt < max_attempts:
            await asyncio.sleep(0.25 * (2 ** (attempt - 1)))

    return {**last_result, "attempt": max_attempts}


async def _dispatch_high_intent_alerts_with_retry(event: VisitorEvent, metadata: dict[str, Any]) -> dict[str, Any]:
    realtime_payload = {
        "id": None,
        "supplier_id": event.supplier_id,
        "notification_type": "high_intent_visitor",
        "title": "偵測到高意圖訪客",
        "message": "有訪客展現高購買意圖，請盡快跟進。",
        "is_read": 0,
        "metadata_json": json.dumps(metadata, ensure_ascii=False),
        "created_at": None,
    }

    websocket_result, slack_result = await asyncio.gather(
        _send_websocket_with_retry(event.supplier_id, realtime_payload),
        _send_slack_with_retry(
            supplier_id=event.supplier_id,
            visitor_session_id=event.visitor_session_id,
            event_type=event.event_type,
            intent_score=event.intent_score or 0,
            page_url=event.page_url,
            visitor_company=event.visitor_company,
        ),
    )

    return {
        "websocket": websocket_result,
        "slack": slack_result,
    }


def _safe_event_data(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _apply_enrichment(event: VisitorEvent, attributes: dict[str, Any]) -> dict[str, Any]:
    applied: dict[str, Any] = {}

    enriched_email = attributes.get("visitor_email") or attributes.get("email")
    if enriched_email and not event.visitor_email:
        event.visitor_email = str(enriched_email)
        applied["visitor_email"] = event.visitor_email

    enriched_company = attributes.get("visitor_company") or attributes.get("company")
    if enriched_company and not event.visitor_company:
        event.visitor_company = str(enriched_company)
        applied["visitor_company"] = event.visitor_company

    enriched_country = attributes.get("visitor_country") or attributes.get("country")
    if enriched_country and not event.visitor_country:
        event.visitor_country = str(enriched_country).strip().upper()[:2]
        applied["visitor_country"] = event.visitor_country

    return applied


async def process_visitor_intent_event_core(session, visitor_event_id: int) -> dict:
    event = await session.get(VisitorEvent, visitor_event_id)
    if not event:
        return {"success": False, "error": "Visitor event not found"}

    scoring_service = get_visitor_intent_service()
    initial_result = scoring_service.score_event(
        event_type=event.event_type,
        session_duration_seconds=event.session_duration_seconds,
        event_data_raw=event.event_data,
        visitor_email=event.visitor_email,
        visitor_company=event.visitor_company,
        visitor_country=event.visitor_country,
    )

    event.intent_score = initial_result["intent_score"]
    event.intent_level = initial_result["intent_level"]

    enrichment_service = get_visitor_enrichment_service()
    enrichment_result = enrichment_service.enrich_event(event)
    applied_attributes = _apply_enrichment(event, enrichment_result.get("attributes", {}))

    rescored = False
    if applied_attributes:
        rescored_result = scoring_service.score_event(
            event_type=event.event_type,
            session_duration_seconds=event.session_duration_seconds,
            event_data_raw=event.event_data,
            visitor_email=event.visitor_email,
            visitor_company=event.visitor_company,
            visitor_country=event.visitor_country,
        )
        event.intent_score = rescored_result["intent_score"]
        event.intent_level = rescored_result["intent_level"]
        rescored = True

    event_data = _safe_event_data(event.event_data)
    event_data["enrichment"] = {
        "provider": enrichment_result.get("provider"),
        "status": enrichment_result.get("status"),
        "applied_attributes": applied_attributes,
    }
    event.event_data = json.dumps(event_data, ensure_ascii=False)

    should_notify = event.intent_level == "high"
    notification_metadata: dict[str, Any] | None = None
    if should_notify:
        notification_metadata = {
            "visitor_session_id": event.visitor_session_id,
            "event_type": event.event_type,
            "intent_score": event.intent_score,
            "page_url": event.page_url,
            "rescored": rescored,
            "enrichment_provider": enrichment_result.get("provider"),
        }
        session.add(
            Notification(
                supplier_id=event.supplier_id,
                conversation_id=None,
                notification_type="high_intent_visitor",
                title="偵測到高意圖訪客",
                message="有訪客展現高購買意圖，請盡快跟進。",
                is_read=0,
                metadata_json=json.dumps(notification_metadata, ensure_ascii=False),
            )
        )

    await session.commit()

    alert_dispatch = {
        "websocket": {"success": False, "skipped": True},
        "slack": {"success": False, "skipped": True},
    }
    if should_notify and notification_metadata:
        alert_dispatch = await _dispatch_high_intent_alerts_with_retry(event, notification_metadata)

    return {
        "success": True,
        "visitor_event_id": visitor_event_id,
        "intent_score": event.intent_score,
        "intent_level": event.intent_level,
        "notified": should_notify,
        "rescored": rescored,
        "enrichment_provider": enrichment_result.get("provider"),
        "alert_dispatch": alert_dispatch,
    }


@shared_task(bind=True, max_retries=2)
def process_visitor_intent_event(self, visitor_event_id: int) -> dict:
    """Compute intent score/level for a visitor event and persist result."""
    async def _run() -> dict:
        async with async_session_maker() as session:
            return await process_visitor_intent_event_core(session, visitor_event_id)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("process_visitor_intent_event failed for %s: %s", visitor_event_id, str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
