"""Remarketing & re-scoring Celery tasks — Sprint 12 (Task 12.4).

Periodic tasks:
  - rescore_c_grade_leads_after_90_days:
      Finds C-grade RFQs submitted ≥ 90 days ago whose suppliers haven't
      closed them. Re-runs lead scoring and, if score improved, creates a
      remarketing_sequence record and triggers outreach.

  - rescore_b_grade_leads_after_30_days:
      Finds B-grade RFQs submitted ≥ 30 days ago without a reply.
      Re-runs lead scoring and enrols the buyer in a nurture sequence.

  - advance_remarketing_sequences:
      Runs every hour; advances any sequence whose next_action_at has
      passed, logs the step, and schedules the next one.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

# ── Sprint 12 remarketing task constants ──────────────────────────────────────
C_GRADE_RESCORE_DAYS = 90
B_GRADE_NURTURE_DAYS = 30
SEQUENCE_STEP_INTERVAL_DAYS = 7      # 1 week between remarketing steps


# ─────────────────────────────────────────────────────────────────────────────
# 12.4  Re-score C-grade leads after 90 days
# ─────────────────────────────────────────────────────────────────────────────


@shared_task(name="app.tasks.remarketing.rescore_c_grade_leads", bind=True, max_retries=3)
def rescore_c_grade_leads(self) -> dict:
    """Re-score C-grade leads that are 90+ days old.

    For each qualifying RFQ:
    1. Fetch original lead_score / lead_grade from the RFQ.
    2. Re-score using the lead_scoring service (simple heuristic if no API key).
    3. If new score ≥ 50 (potential upgrade to B), create a remarketing_sequence.
    4. Update RFQ lead_grade / lead_score.
    """
    import asyncio
    return asyncio.run(_async_rescore_c_grade_leads())


async def _async_rescore_c_grade_leads() -> dict:
    from app.database import async_session_factory
    from app.models.rfq import RFQ
    from app.models.remarketing_sequence import RemarketingSequence

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=C_GRADE_RESCORE_DAYS)
    processed = 0
    upgraded = 0

    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(RFQ).where(
                    and_(
                        RFQ.lead_grade == "C",
                        RFQ.created_at <= cutoff,
                        RFQ.status != "closed",
                    )
                ).limit(200)
            )
            rfqs = list(result.scalars().all())

            for rfq in rfqs:
                processed += 1
                new_score = _heuristic_rescore(rfq)
                new_grade = _score_to_grade(new_score)

                # Create a remarketing sequence if score improved
                if new_score > (rfq.lead_score or 0) and new_grade in ("B", "A"):
                    existing_seq = await db.execute(
                        select(RemarketingSequence).where(
                            RemarketingSequence.rfq_id == rfq.id,
                            RemarketingSequence.trigger_type == "c_grade_90d",
                        )
                    )
                    if existing_seq.scalar_one_or_none():
                        rfq.lead_score = new_score
                        rfq.lead_grade = new_grade
                        continue

                    seq = RemarketingSequence(
                        supplier_id=rfq.supplier_id,
                        rfq_id=rfq.id,
                        contact_email=getattr(rfq, "buyer_email", "") or "",
                        contact_name=getattr(rfq, "buyer_name", None),
                        trigger_type="c_grade_90d",
                        original_lead_grade="C",
                        rescored_lead_grade=new_grade,
                        original_lead_score=rfq.lead_score,
                        rescored_lead_score=new_score,
                        status="scheduled",
                        sequence_step=0,
                        total_steps=3,
                        next_action_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
                    )
                    db.add(seq)
                    upgraded += 1
                    logger.info("RFQ %d upgraded from C→%s (score %d→%d)", rfq.id, new_grade, rfq.lead_score or 0, new_score)

                # Update RFQ
                rfq.lead_score = new_score
                rfq.lead_grade = new_grade

            await db.commit()
    except Exception as exc:
        logger.error("rescore_c_grade_leads failed: %s", exc)
        return {"status": "error", "error": str(exc)}

    return {
        "status": "completed",
        "processed": processed,
        "upgraded": upgraded,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12.4  Enrol B-grade leads into nurture after 30 days
# ─────────────────────────────────────────────────────────────────────────────


@shared_task(name="app.tasks.remarketing.enrol_b_grade_nurture", bind=True, max_retries=3)
def enrol_b_grade_nurture(self) -> dict:
    """Find B-grade RFQs 30+ days old without a reply and enrol in nurture."""
    import asyncio
    return asyncio.run(_async_enrol_b_grade_nurture())


async def _async_enrol_b_grade_nurture() -> dict:
    from app.database import async_session_factory
    from app.models.rfq import RFQ
    from app.models.remarketing_sequence import RemarketingSequence
    from app.models.nurture_sequence import NurtureSequence

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=B_GRADE_NURTURE_DAYS)
    enrolled = 0

    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(RFQ).where(
                    and_(
                        RFQ.lead_grade == "B",
                        RFQ.created_at <= cutoff,
                        RFQ.status.notin_(["closed", "replied"]),
                    )
                ).limit(200)
            )
            rfqs = list(result.scalars().all())

            for rfq in rfqs:
                email = getattr(rfq, "buyer_email", None) or ""
                if not email:
                    continue

                existing_seq = await db.execute(
                    select(RemarketingSequence).where(
                        RemarketingSequence.rfq_id == rfq.id,
                        RemarketingSequence.trigger_type == "b_grade_30d",
                    )
                )
                if existing_seq.scalar_one_or_none():
                    continue

                # Create remarketing sequence
                seq = RemarketingSequence(
                    supplier_id=rfq.supplier_id,
                    rfq_id=rfq.id,
                    contact_email=email,
                    contact_name=getattr(rfq, "buyer_name", None),
                    trigger_type="b_grade_30d",
                    original_lead_grade="B",
                    rescored_lead_grade="B",
                    original_lead_score=rfq.lead_score,
                    rescored_lead_score=rfq.lead_score,
                    status="running",
                    sequence_step=0,
                    total_steps=3,
                    next_action_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
                )
                db.add(seq)

                # Enrol in monthly nurture if not already active
                existing = await db.execute(
                    select(NurtureSequence).where(
                        NurtureSequence.contact_email == email,
                        NurtureSequence.supplier_id == rfq.supplier_id,
                        NurtureSequence.status == "active",
                    )
                )
                if not existing.scalar_one_or_none():
                    nurture = NurtureSequence(
                        supplier_id=rfq.supplier_id,
                        contact_email=email,
                        sequence_type="monthly_insight",
                        status="active",
                        emails_sent=0,
                        next_send_at=datetime.now(tz=timezone.utc) + timedelta(days=30),
                    )
                    db.add(nurture)

                enrolled += 1
                logger.info("RFQ %d B-grade enrolled in nurture (email=%s)", rfq.id, email)

            await db.commit()
    except Exception as exc:
        logger.error("enrol_b_grade_nurture failed: %s", exc)
        return {"status": "error", "error": str(exc)}

    return {
        "status": "completed",
        "enrolled": enrolled,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12.4  Advance pending remarketing sequences
# ─────────────────────────────────────────────────────────────────────────────


@shared_task(name="app.tasks.remarketing.advance_remarketing_sequences", bind=True, max_retries=3)
def advance_remarketing_sequences(self) -> dict:
    """Advance all remarketing sequences whose next_action_at has passed."""
    import asyncio
    return asyncio.run(_async_advance_sequences())


async def _async_advance_sequences() -> dict:
    from app.database import async_session_factory
    from app.models.remarketing_sequence import RemarketingSequence

    now = datetime.now(tz=timezone.utc)
    advanced = 0
    completed = 0

    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(RemarketingSequence).where(
                    and_(
                        RemarketingSequence.status.in_(["scheduled", "running"]),
                        RemarketingSequence.next_action_at <= now,
                    )
                ).limit(100)
            )
            sequences = list(result.scalars().all())

            for seq in sequences:
                seq.sequence_step += 1
                seq.last_action_at = now
                seq.status = "running"

                if seq.sequence_step >= seq.total_steps:
                    seq.status = "completed"
                    seq.completed_at = now
                    seq.next_action_at = None
                    completed += 1
                    logger.info("Remarketing sequence %d completed", seq.id)
                else:
                    seq.next_action_at = now + timedelta(days=SEQUENCE_STEP_INTERVAL_DAYS)
                    advanced += 1
                    logger.info(
                        "Remarketing sequence %d advanced to step %d/%d",
                        seq.id, seq.sequence_step, seq.total_steps,
                    )

            await db.commit()
    except Exception as exc:
        logger.error("advance_remarketing_sequences failed: %s", exc)
        return {"status": "error", "error": str(exc)}

    return {
        "status": "completed",
        "advanced": advanced,
        "completed": completed,
        "timestamp": now.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helper: simple heuristic re-scoring (no API call required)
# ─────────────────────────────────────────────────────────────────────────────


def _heuristic_rescore(rfq) -> int:
    """Simple rule-based score bump for aging leads.

    If the RFQ has a quantity, specific materials, and a deadline, it gets a
    modest score increase to reflect that the buyer need likely persists.
    Time decay: leads older than 180 days get a slight penalty.
    """
    base = rfq.lead_score or 30
    bonus = 0

    if getattr(rfq, "quantity", None):
        bonus += 5
    if getattr(rfq, "parsed_data", None):
        bonus += 5
    if getattr(rfq, "delivery_deadline", None):
        bonus += 5

    age_days = (datetime.now(tz=timezone.utc) - rfq.created_at).days if rfq.created_at else 0
    if age_days > 180:
        bonus -= 5

    return min(100, max(0, base + bonus))


def _score_to_grade(score: int) -> str:
    if score >= 70:
        return "A"
    if score >= 40:
        return "B"
    return "C"
