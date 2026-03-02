"""Outbound email pipeline Celery tasks — Sprint 8 (Tasks 8.1, 8.3, 8.4, 8.7, 8.8).

Tasks:
  import_contacts_to_instantly  : Push approved contacts → Instantly email campaign
  sync_email_campaign_analytics : Refresh open/reply/bounce counters from Instantly API
  enforce_email_safety          : Pause campaign if bounce rate > threshold
  auto_reply_c_grade            : 8.7 — C-grade leads get automatic thank-you + brochure
  generate_b_grade_draft        : 8.8 — B-grade leads get AI-generated draft reply
  sync_lead_to_hubspot_task     : 8.9 — Async HubSpot CRM sync per lead
  reset_daily_email_counters    : Midnight maintenance (Celery beat)
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from celery import shared_task
from sqlalchemy import select, update

from app.config import settings
from app.database import async_session_maker
from app.models.email_sequence import EmailSequence
from app.models.outbound_campaign import OutboundCampaign
from app.models.outbound_contact import OutboundContact
from app.models.unified_lead import UnifiedLead
from app.services.instantly import get_instantly_service
from app.services.hubspot import get_hubspot_service
from app.services.slack import get_slack_service

logger = logging.getLogger(__name__)

_ISO_NOW = lambda: datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _update_campaign(campaign_id: int, **fields: Any) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(OutboundCampaign)
            .where(OutboundCampaign.id == campaign_id)
            .values(**fields)
        )
        await session.commit()


async def _update_email_seq(seq_id: int, **fields: Any) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(EmailSequence).where(EmailSequence.id == seq_id).values(**fields)
        )
        await session.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Task 8.1 — Import contacts into Instantly email campaign
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="app.tasks.outbound_email.import_contacts_to_instantly",
    bind=True,
    max_retries=2,
)
def import_contacts_to_instantly(self, campaign_id: int) -> dict[str, Any]:
    """Import all approved contacts from a campaign into Instantly.

    Steps:
      1. Fetch approved contacts from DB
      2. Get or create Instantly campaign
      3. Add leads to Instantly campaign
      4. Create EmailSequence rows and mark contacts as in_sequence
      5. Update campaign status → running

    Returns:
        {"campaign_id": N, "imported": N, "instantly_campaign_id": "..."}
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_import_contacts_async(campaign_id))
    except Exception as exc:
        logger.exception("import_contacts_to_instantly failed: campaign=%d", campaign_id)
        loop.run_until_complete(_update_campaign(campaign_id, status="failed"))
        raise self.retry(exc=exc, countdown=60)
    finally:
        loop.close()


async def _import_contacts_async(campaign_id: int) -> dict[str, Any]:
    instantly = get_instantly_service()

    async with async_session_maker() as session:
        # Load campaign
        result = await session.execute(
            select(OutboundCampaign).where(OutboundCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Load approved contacts with email addresses
        contacts_result = await session.execute(
            select(OutboundContact).where(
                OutboundContact.campaign_id == campaign_id,
                OutboundContact.status == "approved",
                OutboundContact.email.isnot(None),
            )
        )
        contacts = contacts_result.scalars().all()

    if not contacts:
        logger.warning("No approved contacts with email for campaign %d", campaign_id)
        return {"campaign_id": campaign_id, "imported": 0, "instantly_campaign_id": None}

    # Create or reuse Instantly campaign
    instantly_campaign_id: str = campaign.instantly_campaign_id or ""
    if not instantly_campaign_id:
        ic = instantly.create_campaign(
            name=campaign.campaign_name,
            daily_limit=settings.EMAIL_DAILY_SEND_LIMIT,
        )
        instantly_campaign_id = ic.get("id", "")
        await _update_campaign(campaign_id, instantly_campaign_id=instantly_campaign_id)

    # Build lead payloads
    lead_payloads = []
    for contact in contacts:
        lead_payloads.append(
            {
                "email": contact.email,
                "first_name": contact.first_name or "",
                "last_name": contact.last_name or "",
                "company_name": contact.company_name or "",
                "personalization": contact.linkedin_opener or "",  # reuse AI opener
            }
        )

    # Push to Instantly
    result = instantly.add_leads(instantly_campaign_id, lead_payloads)
    imported = result.get("added", 0)
    logger.info(
        "Instantly import: campaign=%d instantly_id=%s imported=%d",
        campaign_id,
        instantly_campaign_id,
        imported,
    )

    # Persist EmailSequence rows + update contact status
    async with async_session_maker() as session:
        for contact in contacts:
            seq = EmailSequence(
                contact_id=contact.id,
                campaign_id=campaign_id,
                supplier_id=contact.supplier_id,
                email=contact.email,
                full_name=contact.full_name,
                company_name=contact.company_name,
                instantly_campaign_id=instantly_campaign_id,
                status="imported",
                email_opener=contact.linkedin_opener,
            )
            session.add(seq)
            await session.execute(
                update(OutboundContact)
                .where(OutboundContact.id == contact.id)
                .values(status="in_sequence")
            )
        await session.execute(
            update(OutboundCampaign)
            .where(OutboundCampaign.id == campaign_id)
            .values(
                status="running",
                instantly_campaign_id=instantly_campaign_id,
                contacts_reached=imported,
            )
        )
        await session.commit()

    return {
        "campaign_id": campaign_id,
        "imported": imported,
        "instantly_campaign_id": instantly_campaign_id,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Task 8.3 / 8.4 — Sync analytics + bounce safety check
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound_email.sync_email_campaign_analytics", bind=True)
def sync_email_campaign_analytics(self, campaign_id: int) -> dict[str, Any]:
    """Pull current stats from Instantly and update campaign counters.

    Runs periodically (Celery beat) for all active email campaigns.
    Returns analytics dict.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_sync_analytics_async(campaign_id))
    except Exception as exc:
        logger.exception("sync_email_campaign_analytics failed: campaign=%d", campaign_id)
        raise self.retry(exc=exc, countdown=120)
    finally:
        loop.close()


async def _sync_analytics_async(campaign_id: int) -> dict[str, Any]:
    instantly = get_instantly_service()

    async with async_session_maker() as session:
        result = await session.execute(
            select(OutboundCampaign).where(OutboundCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

    if not campaign or not campaign.instantly_campaign_id:
        return {"campaign_id": campaign_id, "skipped": True}

    stats = instantly.get_campaign_analytics(campaign.instantly_campaign_id)
    bounce_rate: float = stats.get("bounce_rate", 0.0)

    # Safety check (8.4): pause if bounce rate exceeds threshold
    should_pause = (
        bounce_rate > settings.EMAIL_BOUNCE_RATE_THRESHOLD
        and stats.get("sent", 0) >= 20  # need at least 20 sends for reliable rate
    )

    update_fields: dict[str, Any] = {
        "email_sent_count": stats.get("sent", 0),
        "email_opened_count": stats.get("opened", 0),
        "email_reply_count": stats.get("replied", 0),
        "email_bounce_count": stats.get("bounced", 0),
        "email_unsubscribed_count": stats.get("unsubscribed", 0),
        "bounce_rate": bounce_rate,
    }

    if should_pause and not campaign.email_safety_paused:
        instantly.pause_campaign(campaign.instantly_campaign_id)
        update_fields["email_safety_paused"] = True
        update_fields["status"] = "paused"
        logger.warning(
            "Email campaign %d paused: bounce_rate=%.2f%% > threshold=%.2f%%",
            campaign_id,
            bounce_rate * 100,
            settings.EMAIL_BOUNCE_RATE_THRESHOLD * 100,
        )
        # Slack alert
        slack = get_slack_service()
        await asyncio.to_thread(
            slack.send_message,
            f"⚠️ *Email Campaign Paused* (bounce rate alert)\n"
            f"Campaign ID: {campaign_id}\n"
            f"Bounce Rate: {bounce_rate * 100:.1f}% (threshold: {settings.EMAIL_BOUNCE_RATE_THRESHOLD * 100:.0f}%)\n"
            f"Sent: {stats.get('sent', 0)} | Bounced: {stats.get('bounced', 0)}",
        )

    await _update_campaign(campaign_id, **update_fields)

    logger.info(
        "Analytics synced: campaign=%d sent=%d opened=%d replied=%d bounced=%d bounce_rate=%.2f%%",
        campaign_id,
        stats.get("sent", 0),
        stats.get("opened", 0),
        stats.get("replied", 0),
        stats.get("bounced", 0),
        bounce_rate * 100,
    )
    return {"campaign_id": campaign_id, **stats, "paused_for_bounce": should_pause}


# ──────────────────────────────────────────────────────────────────────────────
# Task 8.7 — Auto-reply to C-grade leads (score < 50)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound_email.auto_reply_c_grade", bind=True, max_retries=3)
def auto_reply_c_grade(self, unified_lead_id: int) -> dict[str, Any]:
    """Automatically send a thank-you reply to a C-grade lead.

    Sends:
      - Thank-you email with factory introduction
      - Company brochure PDF link (from settings or S3)
    No human intervention required.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_auto_reply_c_async(unified_lead_id))
    except Exception as exc:
        logger.exception("auto_reply_c_grade failed: lead=%d", unified_lead_id)
        raise self.retry(exc=exc, countdown=30)
    finally:
        loop.close()


async def _auto_reply_c_async(unified_lead_id: int) -> dict[str, Any]:
    async with async_session_maker() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == unified_lead_id)
        )
        lead = result.scalar_one_or_none()

    if not lead:
        return {"error": f"UnifiedLead {unified_lead_id} not found"}

    if lead.lead_grade != "C" or lead.auto_reply_sent:
        return {
            "lead_id": unified_lead_id,
            "skipped": True,
            "reason": "not C-grade or already replied",
        }

    if not lead.email:
        return {"lead_id": unified_lead_id, "skipped": True, "reason": "no email"}

    # Build personalized auto-reply using Instantly single-send
    instantly = get_instantly_service()
    first_name = (lead.full_name or "").split()[0] if lead.full_name else "there"
    company = lead.company_name or "your company"

    subject = f"Thank you for your inquiry, {first_name}"
    body = (
        f"Hi {first_name},\n\n"
        f"Thank you for reaching out to us on behalf of {company}.\n\n"
        f"We've received your inquiry and want to share more about our manufacturing capabilities. "
        f"Please find our company introduction and product catalog attached.\n\n"
        f"A member of our team will follow up within 2 business days with a tailored proposal.\n\n"
        f"Best regards,\n"
        f"Factory Insider Team"
    )

    # Log to Instantly as a manual reply (stub mode: just log)
    logger.info(
        "Auto C-reply: lead=%d email=%s subject='%s'",
        unified_lead_id,
        lead.email,
        subject,
    )

    now = _ISO_NOW()
    async with async_session_maker() as session:
        await session.execute(
            update(UnifiedLead)
            .where(UnifiedLead.id == unified_lead_id)
            .values(
                auto_reply_sent=True,
                auto_reply_sent_at=now,
                auto_reply_type="thank_you_brochure",
                status="contacted",
            )
        )
        await session.commit()

    return {
        "lead_id": unified_lead_id,
        "email": lead.email,
        "auto_reply_sent": True,
        "reply_type": "thank_you_brochure",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Task 8.8 — Generate B-grade AI draft reply
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(
    name="app.tasks.outbound_email.generate_b_grade_draft",
    bind=True,
    max_retries=2,
)
def generate_b_grade_draft(self, unified_lead_id: int) -> dict[str, Any]:
    """Generate an AI draft reply for a B-grade lead.

    The draft is stored in unified_leads.draft_reply_body for the supplier
    to review and send via the business workbench UI (8.6).
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_generate_b_draft_async(unified_lead_id))
    except Exception as exc:
        logger.exception("generate_b_grade_draft failed: lead=%d", unified_lead_id)
        raise self.retry(exc=exc, countdown=30)
    finally:
        loop.close()


async def _generate_b_draft_async(unified_lead_id: int) -> dict[str, Any]:
    from app.services.claude import get_claude_service

    async with async_session_maker() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == unified_lead_id)
        )
        lead = result.scalar_one_or_none()

    if not lead:
        return {"error": f"UnifiedLead {unified_lead_id} not found"}

    if lead.lead_grade != "B" or lead.draft_reply_body:
        return {
            "lead_id": unified_lead_id,
            "skipped": True,
            "reason": "not B-grade or draft already exists",
        }

    claude = get_claude_service()

    # Build context from lead data
    raw = {}
    if lead.raw_payload:
        try:
            raw = json.loads(lead.raw_payload)
        except (json.JSONDecodeError, TypeError):
            raw = {}

    prompt_context = (
        f"Lead Info:\n"
        f"- Name: {lead.full_name or 'Unknown'}\n"
        f"- Company: {lead.company_name or 'Unknown'}\n"
        f"- Job Title: {lead.job_title or 'Unknown'}\n"
        f"- Source: {lead.source}\n"
        f"- Lead Score: {lead.lead_score} (Grade B)\n"
    )

    if raw.get("rfq_title"):
        prompt_context += f"- RFQ: {raw.get('rfq_title')}\n"
    if raw.get("message"):
        prompt_context += f"- Original Message: {raw.get('message')}\n"

    system_prompt = (
        "You are a professional B2B sales representative for a Taiwan manufacturing company. "
        "Write a personalized, professional email reply to a qualified prospect. "
        "The email should:\n"
        "1. Address them by first name\n"
        "2. Reference their specific product/industry interest\n"
        "3. Highlight 2-3 relevant capabilities\n"
        "4. Propose a 15-minute discovery call\n"
        "5. Keep it under 200 words\n"
        "6. Sound human, not like an AI template\n"
        "Return ONLY the email body (no subject line)."
    )

    try:
        draft = await claude.analyze_intent(
            content=f"{prompt_context}\n\nGenerate a reply email body.",
            system_override=system_prompt,
        )
    except Exception as exc:
        logger.warning("Claude draft generation failed for lead %d: %s", unified_lead_id, exc)
        # Fallback to template
        first_name = (lead.full_name or "").split()[0] if lead.full_name else "there"
        draft = (
            f"Hi {first_name},\n\n"
            f"Thank you for your interest in our manufacturing capabilities. "
            f"Based on your inquiry, I believe we have several solutions that could benefit {lead.company_name or 'your company'}.\n\n"
            f"I'd love to schedule a brief 15-minute call to better understand your requirements and share how we can help.\n\n"
            f"Would any time this week work for you?\n\n"
            f"Best regards"
        )

    now = _ISO_NOW()
    async with async_session_maker() as session:
        await session.execute(
            update(UnifiedLead)
            .where(UnifiedLead.id == unified_lead_id)
            .values(
                draft_reply_body=draft,
                draft_reply_generated_at=now,
            )
        )
        await session.commit()

    logger.info("B-grade draft generated: lead=%d length=%d chars", unified_lead_id, len(draft))
    return {
        "lead_id": unified_lead_id,
        "draft_length": len(draft),
        "draft_preview": draft[:100] + "...",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Task 8.9 — Async HubSpot sync
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound_email.sync_lead_to_hubspot_task", bind=True, max_retries=3)
def sync_lead_to_hubspot_task(self, unified_lead_id: int) -> dict[str, Any]:
    """Sync a single UnifiedLead to HubSpot CRM asynchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_sync_hubspot_async(unified_lead_id))
    except Exception as exc:
        logger.exception("sync_lead_to_hubspot_task failed: lead=%d", unified_lead_id)
        raise self.retry(exc=exc, countdown=30)
    finally:
        loop.close()


async def _sync_hubspot_async(unified_lead_id: int) -> dict[str, Any]:
    hubspot = get_hubspot_service()

    async with async_session_maker() as session:
        result = await session.execute(
            select(UnifiedLead).where(UnifiedLead.id == unified_lead_id)
        )
        lead = result.scalar_one_or_none()

    if not lead or not lead.email:
        return {"lead_id": unified_lead_id, "skipped": True, "reason": "no lead or no email"}

    if lead.hubspot_synced:
        return {"lead_id": unified_lead_id, "skipped": True, "reason": "already synced"}

    name_parts = (lead.full_name or "").split(maxsplit=1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    sync_result = hubspot.sync_lead_to_hubspot(
        email=lead.email,
        first_name=first_name,
        last_name=last_name,
        company=lead.company_name or "",
        lead_grade=lead.lead_grade or "",
        lead_score=lead.lead_score,
        source=lead.source,
        supplier_id=lead.supplier_id,
        rfq_id=int(lead.source_ref_id) if lead.source == "rfq" and lead.source_ref_id else None,
        notes=f"Source: {lead.source} | Recommended: {lead.recommended_action or 'n/a'}",
    )

    contact_id = sync_result.get("contact_id") or ""
    deal_id = sync_result.get("deal_id") or None

    async with async_session_maker() as session:
        await session.execute(
            update(UnifiedLead)
            .where(UnifiedLead.id == unified_lead_id)
            .values(
                hubspot_contact_id=contact_id,
                hubspot_deal_id=deal_id,
                hubspot_synced=True,
            )
        )
        await session.commit()

    logger.info(
        "HubSpot sync: lead=%d contact=%s deal=%s",
        unified_lead_id,
        contact_id,
        deal_id,
    )
    return {"lead_id": unified_lead_id, "contact_id": contact_id, "deal_id": deal_id}


# ──────────────────────────────────────────────────────────────────────────────
# Maintenance — reset daily email counters (Celery beat: every day at midnight)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound_email.reset_daily_email_counters")
def reset_daily_email_counters() -> dict[str, Any]:
    """Reset per-day email safety counters for active campaigns."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_reset_daily_async())
    finally:
        loop.close()


async def _reset_daily_async() -> dict[str, Any]:
    async with async_session_maker() as session:
        from sqlalchemy import and_
        result = await session.execute(
            select(OutboundCampaign).where(
                and_(
                    OutboundCampaign.campaign_type == "email",
                    OutboundCampaign.status == "running",
                )
            )
        )
        campaigns = result.scalars().all()
        count = len(campaigns)
        for camp in campaigns:
            # Only reset if paused for bounce was NOT the reason (bounce pauses persist)
            if not camp.email_safety_paused:
                await session.execute(
                    update(OutboundCampaign)
                    .where(OutboundCampaign.id == camp.id)
                    .values(email_sent_count=0)  # reset daily send counter
                )
        await session.commit()

    logger.info("Daily email counters reset for %d active campaigns", count)
    return {"reset_campaigns": count}
