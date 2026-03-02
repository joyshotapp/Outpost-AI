"""Unified lead processing pipeline — Sprint 8 (Task 8.5).

All inbound lead signals flow through this module regardless of source.
Supported sources:
  rfq       — RFQ submission via buyer portal
  linkedin  — LinkedIn reply from HeyReach webhook
  email     — Email reply from Instantly webhook
  visitor   — High-intent visitor (RB2B / Leadfeeder)
  chat      — AI chatbot interaction with contact data
  manual    — Manual entry (exhibition, business card)

Processing matrix:
  Grade A (score ≥ 80) → Slack hot-lead alert + immediate draft + HubSpot deal
  Grade B (50 – 79)    → AI draft reply queued + HubSpot contact
  Grade C (< 50)       → Auto thank-you email + HubSpot contact
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unified_lead import UnifiedLead
from app.services.lead_scoring import LeadScoringService

logger = logging.getLogger(__name__)

_ISO_NOW = lambda: datetime.now(timezone.utc).isoformat()

# ── Grade thresholds ──────────────────────────────────────────────────────────
GRADE_A_THRESHOLD = 80
GRADE_B_THRESHOLD = 50


def _compute_grade(score: int) -> str:
    if score >= GRADE_A_THRESHOLD:
        return "A"
    if score >= GRADE_B_THRESHOLD:
        return "B"
    return "C"


def _recommended_action(grade: str, source: str) -> str:
    actions = {
        "A": "immediate_followup_a",
        "B": "draft_reply_b",
        "C": "auto_reply_c",
    }
    # LinkedIn/email replies already have human context — A-grade gets sequence
    if grade == "A" and source in ("linkedin", "email"):
        return "hot_lead_sequence_a"
    return actions.get(grade, "review")


class LeadPipelineService:
    """Route inbound signals through the unified lead processing matrix."""

    def __init__(self) -> None:
        self.scorer = LeadScoringService()

    # ── Main entry point ──────────────────────────────────────────────────────

    async def process_inbound(
        self,
        db: AsyncSession,
        *,
        supplier_id: int,
        source: str,
        source_ref_id: str | None = None,
        email: str | None = None,
        full_name: str | None = None,
        company_name: str | None = None,
        company_domain: str | None = None,
        job_title: str | None = None,
        phone: str | None = None,
        linkedin_url: str | None = None,
        raw_payload: dict[str, Any] | None = None,
        override_score: int | None = None,
    ) -> UnifiedLead:
        """Create or update a UnifiedLead and trigger downstream actions.

        Returns the persisted UnifiedLead instance.
        """
        # ── Score ─────────────────────────────────────────────────────────────
        if override_score is not None:
            score = override_score
            score_breakdown: dict[str, Any] = {"override": True}
        else:
            score_input = {
                "company_name": company_name or "",
                "company_domain": company_domain or "",
                "job_title": job_title or "",
                "source": source,
                **(raw_payload or {}),
            }
            score_result = self.scorer.score_lead(score_input)
            score = score_result.get("total_score", 0)
            score_breakdown = score_result

        grade = _compute_grade(score)
        action = _recommended_action(grade, source)

        # ── Deduplication: same email + supplier within last 7 days ────────────
        existing: UnifiedLead | None = None
        if email:
            from sqlalchemy import and_
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            result = await db.execute(
                select(UnifiedLead).where(
                    and_(
                        UnifiedLead.supplier_id == supplier_id,
                        UnifiedLead.email == email,
                        UnifiedLead.created_at >= cutoff,
                    )
                )
            )
            existing = result.scalar_one_or_none()

        if existing:
            # Upgrade if new score is higher
            if score > existing.lead_score:
                existing.lead_score = score
                existing.lead_grade = grade
                existing.recommended_action = action
                existing.score_breakdown = json.dumps(score_breakdown)
                if grade == "A" and not existing.is_hot_lead:
                    existing.is_hot_lead = True
                    existing.hot_lead_reason = f"Score upgraded to {score} via {source}"
            await db.commit()
            await db.refresh(existing)
            logger.info(
                "LeadPipeline: updated existing lead id=%d email=%s score=%d grade=%s",
                existing.id, email, score, grade,
            )
            lead = existing
        else:
            # New lead
            lead = UnifiedLead(
                supplier_id=supplier_id,
                source=source,
                source_ref_id=str(source_ref_id) if source_ref_id else None,
                email=email,
                full_name=full_name,
                company_name=company_name,
                company_domain=company_domain,
                job_title=job_title,
                phone=phone,
                linkedin_url=linkedin_url,
                lead_score=score,
                lead_grade=grade,
                score_breakdown=json.dumps(score_breakdown),
                recommended_action=action,
                is_hot_lead=(grade == "A"),
                hot_lead_reason=f"Grade A on first contact via {source}" if grade == "A" else None,
                raw_payload=json.dumps(raw_payload) if raw_payload else None,
            )
            db.add(lead)
            await db.commit()
            await db.refresh(lead)
            logger.info(
                "LeadPipeline: new lead id=%d email=%s score=%d grade=%s source=%s",
                lead.id, email, score, grade, source,
            )

        # ── Trigger downstream tasks ───────────────────────────────────────────
        await self._dispatch(lead)
        return lead

    async def _dispatch(self, lead: UnifiedLead) -> None:
        """Fire background tasks based on grade and action."""
        from app.tasks.outbound_email import (
            auto_reply_c_grade,
            generate_b_grade_draft,
            sync_lead_to_hubspot_task,
        )

        # HubSpot sync for all grades with an email
        if lead.email and not lead.hubspot_synced:
            sync_lead_to_hubspot_task.delay(lead.id)

        if lead.lead_grade == "C" and not lead.auto_reply_sent:
            auto_reply_c_grade.delay(lead.id)

        elif lead.lead_grade == "B" and not lead.draft_reply_body:
            generate_b_grade_draft.delay(lead.id)

        elif lead.lead_grade == "A":
            # Grade A: Slack notification + draft reply
            if not lead.slack_notified:
                await self._notify_slack_hot_lead(lead)
            if not lead.draft_reply_body:
                generate_b_grade_draft.delay(lead.id)   # also generate draft for A

    async def _notify_slack_hot_lead(self, lead: UnifiedLead) -> None:
        """Send Slack hot-lead alert for Grade A leads."""
        from app.services.slack import get_slack_service

        slack = get_slack_service()
        message = (
            f"🔥 *Hot Lead — Grade A* (score {lead.lead_score})\n"
            f"• *Name:* {lead.full_name or 'Unknown'}\n"
            f"• *Company:* {lead.company_name or 'Unknown'}\n"
            f"• *Email:* {lead.email or 'N/A'}\n"
            f"• *Source:* {lead.source}\n"
            f"• *Action required:* {lead.recommended_action}\n"
            f"• *Lead ID:* #{lead.id}"
        )
        try:
            import asyncio
            await asyncio.to_thread(slack.send_message, message)
            # Mark notified (best-effort, will be committed by caller)
            lead.slack_notified = True
        except Exception as exc:
            logger.warning("Slack hot-lead alert failed for lead %d: %s", lead.id, exc)


_lead_pipeline: LeadPipelineService | None = None


def get_lead_pipeline() -> LeadPipelineService:
    global _lead_pipeline
    if _lead_pipeline is None:
        _lead_pipeline = LeadPipelineService()
    return _lead_pipeline
