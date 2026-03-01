"""Webhook endpoints — Sprint 7 (7.9).

Supported webhooks:
  POST /webhooks/heyreach   — HeyReach LinkedIn event callbacks

HeyReach event types handled:
  lead_replied          → mark hot lead, Slack alert, in-app notification
  connection_accepted   → update sequence progress
  connection_declined   → mark sequence as declined
  message_opened        → update sequence day progress
  sequence_completed    → mark sequence as completed (no reply)
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.linkedin_sequence import LinkedInSequence
from app.models.notification import Notification
from app.models.outbound_campaign import OutboundCampaign
from app.models.outbound_contact import OutboundContact

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

_HOT_LEAD_EVENT = "lead_replied"
_ISO_NOW = lambda: datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────────────
# Signature verification helper
# ──────────────────────────────────────────────────────────────────────────────

def _verify_heyreach_signature(body: bytes, signature_header: str | None) -> bool:
    """Verify HMAC-SHA256 signature from HeyReach webhook.

    Returns True when signature is valid OR when no secret is configured
    (dev / stub mode).
    """
    secret = settings.HEYREACH_WEBHOOK_SECRET
    if not secret:
        return True  # Dev mode — accept all

    if not signature_header:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)


# ──────────────────────────────────────────────────────────────────────────────
# HeyReach webhook endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/heyreach", status_code=status.HTTP_200_OK)
async def heyreach_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Receive HeyReach LinkedIn sequence events.

    Expects JSON payload:
    {
        "event_type": "lead_replied",
        "campaign_id": "hr_campaign_123",
        "contact_id": "hr_contact_456",
        "data": {
            "reply_content": "...",
            "current_day": 3,
            "linkedin_url": "...",
            ...
        }
    }
    """
    raw_body = await request.body()
    sig_header = request.headers.get("X-HeyReach-Signature")

    if not _verify_heyreach_signature(raw_body, sig_header):
        logger.warning("HeyReach webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload: dict[str, Any] = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}")

    event_type: str = payload.get("event_type", "")
    hr_campaign_id: str = payload.get("campaign_id", "")
    hr_contact_id: str = payload.get("contact_id", "")
    data: dict[str, Any] = payload.get("data", {})

    logger.info(
        "HeyReach webhook received: event=%s campaign=%s contact=%s",
        event_type, hr_campaign_id, hr_contact_id,
    )

    # ── Dispatch to handler ──────────────────────────────────────────────────
    handler = {
        "lead_replied": _handle_lead_replied,
        "connection_accepted": _handle_connection_accepted,
        "connection_declined": _handle_connection_declined,
        "message_opened": _handle_message_opened,
        "sequence_completed": _handle_sequence_completed,
    }.get(event_type)

    if handler:
        await handler(db, hr_campaign_id, hr_contact_id, data)
    else:
        logger.info("HeyReach webhook: unhandled event_type '%s'", event_type)

    return {"received": True, "event_type": event_type}


# ──────────────────────────────────────────────────────────────────────────────
# Event handlers
# ──────────────────────────────────────────────────────────────────────────────

async def _resolve_sequence_and_contact(
    db: AsyncSession,
    hr_campaign_id: str,
    hr_contact_id: str,
) -> tuple[LinkedInSequence | None, OutboundContact | None]:
    """Look up LinkedInSequence + OutboundContact by HeyReach IDs."""
    seq_result = await db.execute(
        select(LinkedInSequence).where(
            LinkedInSequence.heyreach_campaign_id == hr_campaign_id,
            LinkedInSequence.heyreach_contact_id == hr_contact_id,
        )
    )
    seq = seq_result.scalar_one_or_none()

    contact = None
    if seq:
        cont_result = await db.execute(
            select(OutboundContact).where(OutboundContact.id == seq.contact_id)
        )
        contact = cont_result.scalar_one_or_none()

    return seq, contact


async def _handle_lead_replied(
    db: AsyncSession,
    hr_campaign_id: str,
    hr_contact_id: str,
    data: dict[str, Any],
) -> None:
    """Mark contact as hot lead, push Slack + in-app notification."""
    seq, contact = await _resolve_sequence_and_contact(db, hr_campaign_id, hr_contact_id)

    now_iso = _ISO_NOW()
    reply_content = data.get("reply_content", "")
    current_day = data.get("current_day")

    if seq:
        seq.sequence_status = "replied"
        seq.is_hot_lead = True
        seq.replied_at = now_iso
        seq.reply_content = reply_content
        seq.hot_lead_flagged_at = now_iso
        if current_day:
            seq.current_day = current_day
        await db.commit()

    if contact:
        contact.status = "replied"
        contact.is_hot_lead = True
        contact.hot_lead_reason = f"LinkedIn reply on day {current_day or '?'}"
        await db.commit()

        # Increment campaign hot_leads counter
        await db.execute(
            update(OutboundCampaign)
            .where(OutboundCampaign.id == contact.campaign_id)
            .values(hot_leads=OutboundCampaign.hot_leads + 1)
        )

        # In-app notification
        notif = Notification(
            supplier_id=contact.supplier_id,
            notification_type="linkedin_hot_lead",
            title=f"🔥 LinkedIn 熱線索：{contact.full_name or 'Unknown'}",
            message=(
                f"{contact.full_name or '聯絡人'} ({contact.job_title or ''} @ {contact.company_name or ''})"
                f" 在 LinkedIn Day {current_day or '?'} 回覆了：{reply_content[:200]}"
            ),
            metadata_json=json.dumps({
                "campaign_id": contact.campaign_id,
                "contact_id": contact.id,
                "heyreach_campaign_id": hr_campaign_id,
                "heyreach_contact_id": hr_contact_id,
                "reply_content": reply_content,
                "current_day": current_day,
            }),
        )
        db.add(notif)
        await db.commit()

        # Slack push
        await _push_hot_lead_to_slack(contact, reply_content, current_day)


async def _handle_connection_accepted(
    db: AsyncSession,
    hr_campaign_id: str,
    hr_contact_id: str,
    data: dict[str, Any],
) -> None:
    """Update sequence: connection accepted → advance to Day 2."""
    seq, _contact = await _resolve_sequence_and_contact(db, hr_campaign_id, hr_contact_id)
    if seq:
        seq.connection_accepted_at = _ISO_NOW()
        seq.current_day = max(seq.current_day, 2)
        await db.commit()
        logger.info(
            "Connection accepted: campaign=%s contact=%s",
            hr_campaign_id, hr_contact_id,
        )


async def _handle_connection_declined(
    db: AsyncSession,
    hr_campaign_id: str,
    hr_contact_id: str,
    data: dict[str, Any],
) -> None:
    """Mark sequence as declined."""
    seq, contact = await _resolve_sequence_and_contact(db, hr_campaign_id, hr_contact_id)
    if seq:
        seq.sequence_status = "declined"
        await db.commit()
    if contact:
        contact.status = "excluded"
        await db.commit()
    logger.info(
        "Connection declined: campaign=%s contact=%s",
        hr_campaign_id, hr_contact_id,
    )


async def _handle_message_opened(
    db: AsyncSession,
    hr_campaign_id: str,
    hr_contact_id: str,
    data: dict[str, Any],
) -> None:
    """Update current_day when a follow-up message is opened."""
    seq, _contact = await _resolve_sequence_and_contact(db, hr_campaign_id, hr_contact_id)
    if seq:
        current_day = data.get("current_day")
        if current_day:
            seq.current_day = current_day
        if not seq.first_message_sent_at:
            seq.first_message_sent_at = _ISO_NOW()
        await db.commit()


async def _handle_sequence_completed(
    db: AsyncSession,
    hr_campaign_id: str,
    hr_contact_id: str,
    data: dict[str, Any],
) -> None:
    """Mark sequence as completed (all 25 days done, no reply)."""
    seq, contact = await _resolve_sequence_and_contact(db, hr_campaign_id, hr_contact_id)
    if seq:
        seq.sequence_status = "completed"
        seq.current_day = seq.total_days
        await db.commit()
    if contact and contact.status == "in_sequence":
        contact.status = "replied"  # keep in replied for review; no hot_lead flag
        await db.commit()
    logger.info(
        "Sequence completed (no reply): campaign=%s contact=%s",
        hr_campaign_id, hr_contact_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Slack hot lead notification
# ──────────────────────────────────────────────────────────────────────────────

async def _push_hot_lead_to_slack(
    contact: OutboundContact,
    reply_content: str,
    current_day: int | None,
) -> None:
    """Send hot lead Slack notification asynchronously (best-effort)."""
    if not settings.SLACK_WEBHOOK_URL:
        return

    try:
        import aiohttp
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔥 LinkedIn 熱線索回覆！",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*姓名：*\n{contact.full_name or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*職稱：*\n{contact.job_title or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*公司：*\n{contact.company_name or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Day：*\n{current_day or 'N/A'} / 25"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*回覆內容：*\n{reply_content[:500]}",
                    },
                },
            ]
        }

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                settings.SLACK_WEBHOOK_URL,
                json=message,
                timeout=aiohttp.ClientTimeout(total=5),
            )
            if resp.status != 200:
                logger.warning("Slack hot lead push returned %d", resp.status)
            else:
                logger.info(
                    "Slack hot lead notified for contact %d (campaign %d)",
                    contact.id, contact.campaign_id,
                )
    except Exception as exc:
        logger.warning("Slack hot lead notification failed: %s", exc)
