"""Outbound contact model — Clay-enriched contacts for LinkedIn/email campaigns"""

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    String,
    Text,
)

from app.models.base import BaseModel


class OutboundContact(BaseModel):
    """A single enriched contact belonging to an outbound campaign.

    Lifecycle:
        pending  → Clay enrichment queued
        enriched → Clay returned full data
        approved → Supplier approved for outreach
        excluded → Supplier excluded from outreach
        in_sequence → Imported into HeyReach / Instantly
        replied  → Replied to LinkedIn / email message
        hot_lead → Marked as hot lead (high-intent reply)
    """

    __tablename__ = "outbound_contacts"

    campaign_id = Column(Integer, nullable=False, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)

    # ── Identity ────────────────────────────────────────────────────────────
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    linkedin_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)

    # ── Company ─────────────────────────────────────────────────────────────
    company_name = Column(String(255), nullable=True, index=True)
    company_domain = Column(String(255), nullable=True)
    company_industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)   # e.g. "51-200"
    company_country = Column(String(100), nullable=True)

    # ── Role ────────────────────────────────────────────────────────────────
    job_title = Column(String(200), nullable=True)
    seniority = Column(String(50), nullable=True)      # e.g. "Director", "VP"
    department = Column(String(100), nullable=True)

    # ── Clay enrichment data ─────────────────────────────────────────────────
    clay_row_id = Column(String(100), nullable=True, unique=True, index=True)
    enriched_data = Column(Text, nullable=True)        # JSON – full Clay row payload

    # ── AI personalisation ──────────────────────────────────────────────────
    linkedin_opener = Column(Text, nullable=True)      # AI-generated connection request
    opener_generated_at = Column(String(50), nullable=True)  # ISO datetime string

    # ── Status ──────────────────────────────────────────────────────────────
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )  # pending | enriched | approved | excluded | in_sequence | replied | hot_lead

    is_hot_lead = Column(Boolean, default=False, nullable=False, index=True)
    hot_lead_reason = Column(Text, nullable=True)

    # ── LinkedIn safety counters (per contact per day) ───────────────────────
    connection_requests_sent = Column(Integer, default=0, nullable=False)
    messages_sent = Column(Integer, default=0, nullable=False)

    # ── HeyReach reference ──────────────────────────────────────────────────
    heyreach_contact_id = Column(String(100), nullable=True, index=True)
    sequence_day = Column(Integer, nullable=True)      # Current day in Day 1-25 sequence

    # ── Lead score ──────────────────────────────────────────────────────────
    lead_score = Column(Float, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OutboundContact {self.full_name} @ {self.company_name} [{self.status}]>"
