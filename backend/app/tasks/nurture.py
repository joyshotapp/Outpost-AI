"""Email Nurturing sequence service — Sprint 12 (Task 12.5).

Generates monthly industry-insight emails for C-grade leads using Claude,
then dispatches them via the Instantly integration (or logs to stdout in
stub mode when INSTANTLY_API_KEY is not configured).

Public interface:
    send_monthly_nurture_emails()    — Celery task; called by Beat schedule
    generate_nurture_email(...)      — async helper used by task + tests
    unsubscribe_contact(email, ...)  — marks NurtureSequence as unsubscribed
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from celery import shared_task

logger = logging.getLogger(__name__)

NURTURE_INTERVAL_DAYS = 30         # monthly cadence
MAX_BATCH_SIZE = 100               # contacts per Celery run


# ─────────────────────────────────────────────────────────────────────────────
# 12.5  Claude: generate monthly industry-insight email
# ─────────────────────────────────────────────────────────────────────────────


async def generate_nurture_email(
    supplier_name: str,
    contact_name: Optional[str],
    industry: Optional[str],
    locale: str = "en",
) -> dict[str, str]:
    """Generate a personalised monthly industry-insight email via Claude.

    Args:
        supplier_name:  Name of the supplier sending the email.
        contact_name:   Buyer's name (salutation). Optional.
        industry:       Buyer's industry (e.g. "automotive", "electronics").
        locale:         Language code ("en", "de", "ja", "es", "zh").

    Returns:
        {"subject": "...", "body": "..."}

    Falls back to a generic template when ANTHROPIC_API_KEY is absent.
    """
    try:
        import anthropic
        from app.config import settings

        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        industry_ctx = f" in the {industry} industry" if industry else ""
        greeting = f"Dear {contact_name}," if contact_name else "Dear Valued Partner,"
        lang_instruction = {
            "de": "Write the email in German.",
            "ja": "Write the email in Japanese.",
            "es": "Write the email in Spanish.",
            "zh": "Write the email in Traditional Chinese (繁體中文).",
        }.get(locale, "Write the email in English.")

        prompt = (
            f"{lang_instruction}\n\n"
            f"You are a B2B sales professional writing a monthly industry-insights newsletter "
            f"on behalf of {supplier_name}, a manufacturing supplier.\n\n"
            f"The recipient is a buyer{industry_ctx}. Start with: {greeting}\n\n"
            "Write a concise, engaging monthly update (200-300 words) covering:\n"
            "1. One relevant industry trend or market insight\n"
            "2. A brief mention of how the supplier can help the buyer\n"
            "3. A soft call-to-action (reply, visit link, or book a call)\n\n"
            "Keep a professional yet warm tone. No hard-sell language.\n"
            "Return a JSON object with keys: 'subject' and 'body'."
        )

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        return {
            "subject": str(parsed.get("subject", "Monthly Industry Update")),
            "body": str(parsed.get("body", "")),
        }

    except Exception as exc:
        logger.warning("generate_nurture_email Claude call failed: %s — using template", exc)
        industry_label = industry or "manufacturing"
        greeting = f"Dear {contact_name}," if contact_name else "Dear Valued Partner,"
        return {
            "subject": f"Monthly Update from {supplier_name} | {industry_label.title()} Insights",
            "body": (
                f"{greeting}\n\n"
                f"We hope this message finds you well. As your trusted manufacturing partner, "
                f"we wanted to share some insights relevant to the {industry_label} sector this month.\n\n"
                "Industry trends continue to evolve rapidly, and we're committed to keeping you "
                "informed so you can make the best decisions for your business.\n\n"
                "If you have any upcoming projects or requirements, we'd love to hear from you. "
                "Feel free to reply to this email or submit an RFQ on our platform.\n\n"
                f"Best regards,\n{supplier_name} Team"
            ),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 12.5  Dispatch via Instantly (or stub log)
# ─────────────────────────────────────────────────────────────────────────────


def _dispatch_email(to_email: str, subject: str, body: str, from_name: str) -> bool:
    """Send email via Instantly API or log in stub mode.

    Returns True if dispatched successfully (or in stub mode), False on error.
    """
    try:
        from app.config import settings

        if not getattr(settings, "INSTANTLY_API_KEY", None):
            logger.info(
                "[STUB] Nurture email to %s | Subject: %s | Body: %s…",
                to_email, subject, body[:80],
            )
            return True

        from app.services.instantly import InstantlyService
        svc = InstantlyService(api_key=settings.INSTANTLY_API_KEY)
        svc.send_transactional_email(
            to_email=to_email,
            subject=subject,
            body_text=body,
            from_name=from_name,
        )
        return True
    except Exception as exc:
        logger.error("Email dispatch to %s failed: %s", to_email, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 12.5  Celery Beat task
# ─────────────────────────────────────────────────────────────────────────────


@shared_task(name="app.tasks.nurture.send_monthly_nurture_emails", bind=True, max_retries=3)
def send_monthly_nurture_emails(self) -> dict:
    """Process due nurture sequences and send monthly emails.

    Runs daily; only dispatches to contacts whose next_send_at ≤ now.
    """
    import asyncio
    return asyncio.run(_async_send_nurture_emails())


async def _async_send_nurture_emails() -> dict:
    from app.database import async_session_factory
    from app.models.nurture_sequence import NurtureSequence
    from app.models.supplier import Supplier
    from sqlalchemy import select, and_

    now = datetime.now(tz=timezone.utc)
    sent = 0
    skipped = 0
    errors = 0

    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(NurtureSequence).where(
                    and_(
                        NurtureSequence.status == "active",
                        NurtureSequence.unsubscribed == False,
                        NurtureSequence.next_send_at <= now,
                    )
                ).limit(MAX_BATCH_SIZE)
            )
            sequences = list(result.scalars().all())

            for seq in sequences:
                # Fetch supplier name
                sup_result = await db.execute(
                    select(Supplier).where(Supplier.id == seq.supplier_id)
                )
                supplier = sup_result.scalar_one_or_none()
                supplier_name = (
                    getattr(supplier, "company_name", None) or "Factory Insider Supplier"
                )

                # Generate email via Claude
                email_content = await generate_nurture_email(
                    supplier_name=supplier_name,
                    contact_name=seq.contact_name,
                    industry=seq.industry,
                )

                # Dispatch
                success = _dispatch_email(
                    to_email=seq.contact_email,
                    subject=email_content["subject"],
                    body=email_content["body"],
                    from_name=supplier_name,
                )

                if success:
                    seq.emails_sent += 1
                    seq.last_sent_at = now
                    seq.next_send_at = now + timedelta(days=NURTURE_INTERVAL_DAYS)
                    seq.last_email_subject = email_content["subject"]
                    seq.last_email_body = email_content["body"]
                    seq.updated_at = now
                    sent += 1
                    logger.info("Nurture email sent to %s (seq %d)", seq.contact_email, seq.id)
                else:
                    errors += 1
                    skipped += 1

            await db.commit()
    except Exception as exc:
        logger.error("send_monthly_nurture_emails failed: %s", exc)
        return {"status": "error", "error": str(exc)}

    return {
        "status": "completed",
        "sent": sent,
        "skipped": skipped,
        "errors": errors,
        "timestamp": now.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Unsubscribe helper (called from webhook or UI)
# ─────────────────────────────────────────────────────────────────────────────


async def unsubscribe_contact(email: str, supplier_id: int) -> bool:
    """Mark all active nurture sequences for a contact as unsubscribed."""
    from app.database import async_session_factory
    from app.models.nurture_sequence import NurtureSequence
    from sqlalchemy import select

    now = datetime.now(tz=timezone.utc)
    updated = 0

    async with async_session_factory() as db:
        result = await db.execute(
            select(NurtureSequence).where(
                NurtureSequence.contact_email == email,
                NurtureSequence.supplier_id == supplier_id,
                NurtureSequence.unsubscribed == False,
            )
        )
        seqs = list(result.scalars().all())
        for seq in seqs:
            seq.unsubscribed = True
            seq.unsubscribed_at = now
            seq.status = "unsubscribed"
            updated += 1
        await db.commit()

    logger.info("Unsubscribed %s from %d nurture sequences (supplier %d)", email, updated, supplier_id)
    return updated > 0
