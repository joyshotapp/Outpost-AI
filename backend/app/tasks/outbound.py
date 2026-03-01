"""Outbound pipeline Celery tasks — Sprint 7.

Tasks:
  enrich_contacts_pipeline     : Clay ICP search + waterfall enrichment → DB
  generate_openers_batch       : Claude AI personalised LinkedIn openers
  import_contacts_to_heyreach  : Push approved contacts into HeyReach sequence
  enforce_linkedin_safety      : Daily limit check + auto-pause
  reset_daily_linkedin_counters: Midnight maintenance (schedule via Celery beat)
"""

import asyncio
import json
import logging
import random
import time
from typing import Any

from celery import shared_task
from sqlalchemy import select, update

from app.database import async_session_maker
from app.config import settings
from app.models.outbound_campaign import OutboundCampaign
from app.models.outbound_contact import OutboundContact
from app.models.linkedin_sequence import LinkedInSequence
from app.services.clay import get_clay_service
from app.services.heyreach import get_heyreach_service
from app.services.slack import get_slack_service

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────────

_ENRICH_POLL_INTERVAL = 5    # seconds between Clay run-status polls
_ENRICH_MAX_POLLS = 36       # 36 × 5 s = 3 minutes maximum


async def _update_campaign_status(campaign_id: int, **fields: Any) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(OutboundCampaign)
            .where(OutboundCampaign.id == campaign_id)
            .values(**fields)
        )
        await session.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Task 7.1 — Clay enrichment pipeline
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound.enrich_contacts_pipeline", bind=True, max_retries=2)
def enrich_contacts_pipeline(self, campaign_id: int, icp_criteria: dict[str, Any]) -> dict[str, Any]:
    """Full Clay enrichment pipeline for a single outbound campaign.

    Steps:
      1. Create Clay table
      2. Upload ICP search criteria
      3. Trigger waterfall enrichment run
      4. Poll until completed / failed (max 3 minutes)
      5. Page through enriched contacts and save to outbound_contacts
      6. Update campaign clay_table_id + clay_enrichment_status

    Returns:
        {"campaign_id": N, "contacts_saved": N, "clay_table_id": "..."}
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            _enrich_contacts_pipeline_async(campaign_id, icp_criteria)
        )
    except Exception as exc:
        logger.exception("enrich_contacts_pipeline failed for campaign %d: %s", campaign_id, exc)
        loop.run_until_complete(
            _update_campaign_status(campaign_id, clay_enrichment_status="failed")
        )
        raise self.retry(exc=exc, countdown=60)
    finally:
        loop.close()


async def _enrich_contacts_pipeline_async(
    campaign_id: int,
    icp_criteria: dict[str, Any],
) -> dict[str, Any]:
    clay = get_clay_service()

    # ── 1. Fetch supplier_id from campaign ──────────────────────────────────
    async with async_session_maker() as session:
        result = await session.execute(
            select(OutboundCampaign).where(OutboundCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        supplier_id = campaign.supplier_id

    # ── 2. Create Clay table ────────────────────────────────────────────────
    table_name = f"campaign_{campaign_id}_{int(time.time())}"
    table_data = clay.create_table(table_name)
    clay_table_id: str = table_data["id"]

    await _update_campaign_status(
        campaign_id,
        clay_table_id=clay_table_id,
        clay_enrichment_status="running",
    )

    # ── 3. Import ICP criteria ──────────────────────────────────────────────
    clay.import_icp_criteria(clay_table_id, icp_criteria)

    # ── 4. Trigger waterfall enrichment ─────────────────────────────────────
    run_data = clay.trigger_waterfall_enrichment(clay_table_id)
    run_id: str = run_data.get("run_id", "")

    # ── 5. Poll until done ──────────────────────────────────────────────────
    final_status = "running"
    for attempt in range(_ENRICH_MAX_POLLS):
        await asyncio.sleep(_ENRICH_POLL_INTERVAL)
        status_data = clay.get_run_status(clay_table_id, run_id)
        final_status = status_data.get("status", "running")
        logger.debug(
            "Clay poll %d/%d — campaign %d status=%s",
            attempt + 1, _ENRICH_MAX_POLLS, campaign_id, final_status,
        )
        if final_status in ("completed", "failed"):
            break

    if final_status == "failed":
        await _update_campaign_status(campaign_id, clay_enrichment_status="failed")
        raise RuntimeError(f"Clay enrichment run failed for campaign {campaign_id}")

    # ── 6. Page through and save contacts ───────────────────────────────────
    contacts_saved = 0
    page = 1
    while True:
        page_data = clay.fetch_enriched_contacts(clay_table_id, page=page, page_size=100)
        contacts_chunk = page_data.get("contacts", [])
        if not contacts_chunk:
            break

        async with async_session_maker() as session:
            for c in contacts_chunk:
                # Skip if already imported (clay_row_id unique)
                existing = await session.execute(
                    select(OutboundContact).where(
                        OutboundContact.clay_row_id == str(c.get("clay_row_id", ""))
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                enriched_json = c.get("enriched_data")
                if isinstance(enriched_json, dict):
                    enriched_json = json.dumps(enriched_json)

                contact = OutboundContact(
                    campaign_id=campaign_id,
                    supplier_id=supplier_id,
                    clay_row_id=str(c.get("clay_row_id", "")),
                    first_name=c.get("first_name"),
                    last_name=c.get("last_name"),
                    full_name=c.get("full_name"),
                    email=c.get("email"),
                    linkedin_url=c.get("linkedin_url"),
                    phone=c.get("phone"),
                    company_name=c.get("company_name"),
                    company_domain=c.get("company_domain"),
                    company_industry=c.get("company_industry"),
                    company_size=c.get("company_size"),
                    company_country=c.get("company_country"),
                    job_title=c.get("job_title"),
                    seniority=c.get("seniority"),
                    department=c.get("department"),
                    enriched_data=enriched_json,
                    status="enriched",
                )
                session.add(contact)
                contacts_saved += 1

            await session.commit()

        if not page_data.get("has_more", False):
            break
        page += 1

    # ── 7. Update campaign counters ──────────────────────────────────────────
    await _update_campaign_status(
        campaign_id,
        clay_enrichment_status="completed",
        target_count=contacts_saved,
    )

    logger.info(
        "enrich_contacts_pipeline done — campaign %d saved %d contacts",
        campaign_id,
        contacts_saved,
    )
    return {
        "campaign_id": campaign_id,
        "contacts_saved": contacts_saved,
        "clay_table_id": clay_table_id,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Task 7.7 — AI personalised opener generation
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound.generate_openers_batch", bind=True, max_retries=2)
def generate_openers_batch(self, campaign_id: int, contact_ids: list[int] | None = None) -> dict[str, Any]:
    """Generate AI-personalised LinkedIn connection request messages (openers).

    If `contact_ids` is None, generates openers for all approved contacts
    in the campaign that do not yet have one.

    Returns {"generated": N, "skipped": N}
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            _generate_openers_batch_async(campaign_id, contact_ids)
        )
    except Exception as exc:
        logger.exception("generate_openers_batch failed for campaign %d: %s", campaign_id, exc)
        raise self.retry(exc=exc, countdown=30)
    finally:
        loop.close()


async def _generate_openers_batch_async(
    campaign_id: int,
    contact_ids: list[int] | None,
) -> dict[str, Any]:
    from app.services.claude import get_claude_service  # avoid circular import
    claude = get_claude_service()

    async with async_session_maker() as session:
        query = select(OutboundContact).where(
            OutboundContact.campaign_id == campaign_id,
            OutboundContact.status.in_(["enriched", "approved"]),
            OutboundContact.linkedin_opener.is_(None),
        )
        if contact_ids:
            query = query.where(OutboundContact.id.in_(contact_ids))

        result = await session.execute(query)
        contacts = result.scalars().all()

    generated = 0
    skipped = 0

    for contact in contacts:
        try:
            opener = await claude.generate_linkedin_opener(
                full_name=contact.full_name or "",
                company_name=contact.company_name or "",
                job_title=contact.job_title or "",
                industry=contact.company_industry or "",
                seniority=contact.seniority or "",
            )
        except Exception as exc:
            logger.warning("Opener generation failed for contact %d: %s", contact.id, exc)
            skipped += 1
            continue

        async with async_session_maker() as session:
            await session.execute(
                update(OutboundContact)
                .where(OutboundContact.id == contact.id)
                .values(
                    linkedin_opener=opener,
                    opener_generated_at=_iso_now(),
                )
            )
            await session.commit()

        generated += 1
        # Small random delay to avoid thundering herd on Claude API
        await asyncio.sleep(random.uniform(0.3, 0.8))

    logger.info(
        "generate_openers_batch — campaign %d: generated=%d skipped=%d",
        campaign_id, generated, skipped,
    )
    return {"generated": generated, "skipped": skipped}


# ──────────────────────────────────────────────────────────────────────────────
# Task 7.2/7.8 — Import approved contacts to HeyReach + start sequence
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound.import_contacts_to_heyreach", bind=True, max_retries=2)
def import_contacts_to_heyreach(self, campaign_id: int) -> dict[str, Any]:
    """Import all approved contacts from a campaign into HeyReach and activate the sequence.

    Steps:
      1. Verify daily LinkedIn safety limits before proceeding
      2. Fetch all 'approved' contacts for the campaign
      3. Create HeyReach campaign (if not already created)
      4. Import contacts with personalised openers as custom variables
      5. Activate sequence
      6. Write linkedin_sequences rows; update contact status → in_sequence

    Returns {"imported": N, "heyreach_campaign_id": "..."}
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            _import_contacts_to_heyreach_async(campaign_id)
        )
    except Exception as exc:
        logger.exception("import_contacts_to_heyreach failed for campaign %d: %s", campaign_id, exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        loop.close()


async def _import_contacts_to_heyreach_async(campaign_id: int) -> dict[str, Any]:
    heyreach = get_heyreach_service()

    async with async_session_maker() as session:
        result = await session.execute(
            select(OutboundCampaign).where(OutboundCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # ── Safety check ────────────────────────────────────────────────────
        if campaign.safety_paused:
            logger.warning(
                "Campaign %d is safety-paused; skipping HeyReach import", campaign_id
            )
            return {"imported": 0, "reason": "safety_paused"}

        # ── Fetch approved contacts ──────────────────────────────────────────
        contacts_result = await session.execute(
            select(OutboundContact).where(
                OutboundContact.campaign_id == campaign_id,
                OutboundContact.status == "approved",
            )
        )
        contacts = contacts_result.scalars().all()

    if not contacts:
        return {"imported": 0, "reason": "no_approved_contacts"}

    # ── Create or reuse HeyReach campaign ───────────────────────────────────
    heyreach_campaign_id = campaign.heyreach_campaign_id
    if not heyreach_campaign_id:
        hr_data = heyreach.create_campaign(campaign.campaign_name)
        heyreach_campaign_id = hr_data["id"]
        await _update_campaign_status(
            campaign_id,
            heyreach_campaign_id=heyreach_campaign_id,
        )

    # ── Build payload for HeyReach ───────────────────────────────────────────
    contact_payloads = [
        {
            "linkedin_url": c.linkedin_url or "",
            "first_name": c.first_name or "",
            "last_name": c.last_name or "",
            "email": c.email or "",
            "custom_variables": {
                "opener": c.linkedin_opener or "",
                "company": c.company_name or "",
                "title": c.job_title or "",
            },
        }
        for c in contacts
        if c.linkedin_url
    ]

    import_result = heyreach.import_contacts(heyreach_campaign_id, contact_payloads)
    imported_count: int = import_result.get("imported", len(contact_payloads))
    hr_contact_ids: list[str] = import_result.get("contact_ids", [])

    # ── Activate sequence ────────────────────────────────────────────────────
    heyreach.start_sequence(heyreach_campaign_id)

    # ── Write linkedin_sequences + update contact status ─────────────────────
    async with async_session_maker() as session:
        for idx, contact in enumerate(contacts):
            if not contact.linkedin_url:
                continue

            hr_cid = hr_contact_ids[idx] if idx < len(hr_contact_ids) else None
            seq = LinkedInSequence(
                campaign_id=campaign_id,
                contact_id=contact.id,
                supplier_id=campaign.supplier_id,
                heyreach_campaign_id=heyreach_campaign_id,
                heyreach_contact_id=hr_cid,
                sequence_status="active",
                current_day=1,
            )
            session.add(seq)

            await session.execute(
                update(OutboundContact)
                .where(OutboundContact.id == contact.id)
                .values(
                    status="in_sequence",
                    heyreach_contact_id=hr_cid,
                    sequence_day=1,
                )
            )

        await _update_campaign_status(
            campaign_id,
            status="running",
            contacts_reached=imported_count,
        )
        await session.commit()

    logger.info(
        "import_contacts_to_heyreach done — campaign %d imported %d contacts",
        campaign_id, imported_count,
    )
    return {"imported": imported_count, "heyreach_campaign_id": heyreach_campaign_id}


# ──────────────────────────────────────────────────────────────────────────────
# Task 7.8 — LinkedIn safety enforcement (scheduled daily)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound.enforce_linkedin_safety")
def enforce_linkedin_safety(campaign_id: int) -> dict[str, Any]:
    """Check daily LinkedIn safety limits for a campaign; auto-pause if exceeded.

    Limits (configurable via env):
      - connections per day: LINKEDIN_DAILY_CONNECTION_LIMIT (default 25)
      - messages per day   : LINKEDIN_DAILY_MESSAGE_LIMIT   (default 30)

    Returns {"paused": bool, "reason": str|None}
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_enforce_linkedin_safety_async(campaign_id))
    finally:
        loop.close()


async def _enforce_linkedin_safety_async(campaign_id: int) -> dict[str, Any]:
    heyreach = get_heyreach_service()

    async with async_session_maker() as session:
        result = await session.execute(
            select(OutboundCampaign).where(OutboundCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign or not campaign.heyreach_campaign_id:
            return {"paused": False, "reason": "campaign_not_found_or_no_heyreach"}

    try:
        daily = heyreach.get_daily_stats(campaign.heyreach_campaign_id)
    except Exception as exc:
        logger.warning("Could not fetch daily stats for campaign %d: %s", campaign_id, exc)
        return {"paused": False, "reason": "stats_fetch_failed"}

    connections = daily.get("connections_sent_today", 0)
    messages = daily.get("messages_sent_today", 0)

    conn_limit = settings.LINKEDIN_DAILY_CONNECTION_LIMIT
    msg_limit = settings.LINKEDIN_DAILY_MESSAGE_LIMIT

    paused = False
    reason = None
    if connections >= conn_limit:
        reason = f"daily_connection_limit_reached ({connections}/{conn_limit})"
        paused = True
    elif messages >= msg_limit:
        reason = f"daily_message_limit_reached ({messages}/{msg_limit})"
        paused = True

    if paused:
        logger.warning("Safety pause triggered for campaign %d: %s", campaign_id, reason)
        try:
            heyreach.pause_campaign(campaign.heyreach_campaign_id)
        except Exception as exc:
            logger.error("Failed to pause HeyReach campaign: %s", exc)

        await _update_campaign_status(
            campaign_id,
            safety_paused=1,
            daily_connections_sent=connections,
            daily_messages_sent=messages,
        )
        # Notify via Slack
        try:
            slack = get_slack_service()
            slack.send_message(
                f":warning: LinkedIn 安全防護：Campaign #{campaign_id} 已自動暫停\n"
                f"原因：{reason}"
            )
        except Exception as exc:
            logger.warning("Slack notify failed: %s", exc)
    else:
        await _update_campaign_status(
            campaign_id,
            daily_connections_sent=connections,
            daily_messages_sent=messages,
        )

    return {"paused": paused, "reason": reason}


# ──────────────────────────────────────────────────────────────────────────────
# Task 7.8 — Reset daily counters (Celery beat: midnight UTC)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.outbound.reset_daily_linkedin_counters")
def reset_daily_linkedin_counters() -> dict[str, Any]:
    """Reset daily LinkedIn safety counters for all running campaigns.
    Schedule via Celery beat at 00:00 UTC every day.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_reset_daily_linkedin_counters_async())
    finally:
        loop.close()


async def _reset_daily_linkedin_counters_async() -> dict[str, Any]:
    async with async_session_maker() as session:
        result = await session.execute(
            update(OutboundCampaign)
            .where(OutboundCampaign.status == "running")
            .values(
                daily_connections_sent=0,
                daily_messages_sent=0,
                safety_paused=0,
            )
        )
        await session.commit()
        rows = result.rowcount

    logger.info("reset_daily_linkedin_counters — reset %d running campaigns", rows)
    return {"reset_campaigns": rows}


# ──────────────────────────────────────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────────────────────────────────────

def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
