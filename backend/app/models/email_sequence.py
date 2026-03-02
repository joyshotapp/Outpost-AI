"""Email sequence step model — Sprint 8 (Task 8.1/8.2).

Tracks per-contact email sequence progress within an Instantly campaign.
One row per contact per campaign; updated by Instantly webhook events.
"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.models.base import BaseModel


class EmailSequence(BaseModel):
    """Track email outreach sequence progress for a single outbound contact.

    Step lifecycle:
        pending → imported → step_1_sent → step_2_sent → ... → replied | bounced | unsubscribed | completed
    """

    __tablename__ = "email_sequences"

    contact_id = Column(Integer, nullable=False, index=True)
    campaign_id = Column(Integer, nullable=False, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)

    # ── Contact identity (denormalised for quick access) ─────────────────
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    company_name = Column(String(255), nullable=True)

    # ── Instantly integration ─────────────────────────────────────────────
    instantly_campaign_id = Column(String(100), nullable=True, index=True)
    instantly_lead_id = Column(String(100), nullable=True)

    # ── Sequence progress ─────────────────────────────────────────────────
    current_step = Column(Integer, default=0, nullable=False)   # 0 = not started
    total_steps = Column(Integer, default=4, nullable=False)     # default 4-email sequence
    status = Column(
        String(50), default="pending", nullable=False, index=True
    )
    # pending | imported | active | replied | bounced | unsubscribed | completed | error

    # ── Engagement metrics ────────────────────────────────────────────────
    emails_sent = Column(Integer, default=0, nullable=False)
    emails_opened = Column(Integer, default=0, nullable=False)
    emails_clicked = Column(Integer, default=0, nullable=False)
    reply_received = Column(Boolean, default=False, nullable=False)
    reply_text = Column(Text, nullable=True)
    replied_at = Column(String(50), nullable=True)      # ISO timestamp

    # ── Bounce / health ───────────────────────────────────────────────────
    is_bounced = Column(Boolean, default=False, nullable=False)
    bounce_type = Column(String(20), nullable=True)     # hard | soft
    bounced_at = Column(String(50), nullable=True)

    is_unsubscribed = Column(Boolean, default=False, nullable=False)
    unsubscribed_at = Column(String(50), nullable=True)

    # ── Hot-lead flag ─────────────────────────────────────────────────────
    is_hot_lead = Column(Boolean, default=False, nullable=False)
    hot_lead_reason = Column(Text, nullable=True)

    # ── AI personalisation ────────────────────────────────────────────────
    email_opener = Column(Text, nullable=True)     # AI-generated personalised opener

    # ── HubSpot sync ──────────────────────────────────────────────────────
    hubspot_contact_id = Column(String(100), nullable=True)
    hubspot_deal_id = Column(String(100), nullable=True)
    hubspot_synced = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<EmailSequence {self.email} step={self.current_step} status={self.status}>"
