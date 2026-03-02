"""Unified lead model — Sprint 8 (Task 8.5/8.6).

Aggregates all inbound lead signals from every source into a single table:
  - RFQ submission         (source: rfq)
  - LinkedIn reply         (source: linkedin)
  - Email reply            (source: email)
  - Visitor high-intent    (source: visitor)
  - AI chat interaction    (source: chat)
  - Exhibition / manual    (source: manual)

One lead record per unique inbound signal; deduplicated by email + supplier_id.
"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.models.base import BaseModel


class UnifiedLead(BaseModel):
    """A single processed inbound lead from any source.

    Grade:  A (score ≥ 80) | B (50–79) | C (< 50)
    Status: new → contacted → replied | converted | lost
    """

    __tablename__ = "unified_leads"

    supplier_id = Column(Integer, nullable=False, index=True)

    # ── Identity ──────────────────────────────────────────────────────────
    email = Column(String(255), nullable=True, index=True)
    full_name = Column(String(200), nullable=True)
    company_name = Column(String(255), nullable=True, index=True)
    company_domain = Column(String(255), nullable=True)
    job_title = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)

    # ── Source attribution ─────────────────────────────────────────────────
    source = Column(String(50), nullable=False, index=True)
    # rfq | linkedin | email | visitor | chat | manual
    source_ref_id = Column(String(100), nullable=True)   # FK to source entity (rfq_id, etc.)

    # ── Scoring ───────────────────────────────────────────────────────────
    lead_score = Column(Integer, default=0, nullable=False, index=True)
    lead_grade = Column(String(1), nullable=True, index=True)  # A | B | C
    score_breakdown = Column(Text, nullable=True)             # JSON

    # ── Status / state machine ────────────────────────────────────────────
    status = Column(String(50), default="new", nullable=False, index=True)
    # new | contacted | replied | converted | lost

    # ── Recommended action (computed by 8.5 rules engine) ─────────────────
    recommended_action = Column(String(100), nullable=True)
    # auto_reply_c | draft_reply_b | immediate_followup_a | sequence_email | ...

    # ── Auto-reply tracking (C-grade: 8.7) ────────────────────────────────
    auto_reply_sent = Column(Boolean, default=False, nullable=False)
    auto_reply_sent_at = Column(String(50), nullable=True)
    auto_reply_type = Column(String(50), nullable=True)  # thank_you | brochure | etc.

    # ── Draft reply (B-grade: 8.8) ────────────────────────────────────────
    draft_reply_body = Column(Text, nullable=True)
    draft_reply_generated_at = Column(String(50), nullable=True)
    draft_reply_sent = Column(Boolean, default=False, nullable=False)
    draft_reply_sent_at = Column(String(50), nullable=True)

    # ── Hot-lead / urgency flags ───────────────────────────────────────────
    is_hot_lead = Column(Boolean, default=False, nullable=False)
    hot_lead_reason = Column(Text, nullable=True)
    slack_notified = Column(Boolean, default=False, nullable=False)

    # ── HubSpot CRM sync (8.9) ────────────────────────────────────────────
    hubspot_contact_id = Column(String(100), nullable=True)
    hubspot_deal_id = Column(String(100), nullable=True)
    hubspot_synced = Column(Boolean, default=False, nullable=False)

    # ── Raw payload ───────────────────────────────────────────────────────
    raw_payload = Column(Text, nullable=True)   # JSON dump of original signal

    def __repr__(self) -> str:
        return (
            f"<UnifiedLead {self.company_name or self.email} "
            f"grade={self.lead_grade} source={self.source}>"
        )
