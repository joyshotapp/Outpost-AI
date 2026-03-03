"""Nurture sequence model — Sprint 12 (Task 12.5).

Manages monthly industry-insight email nurturing for C-grade leads.
AI generates personalised content per supplier + industry via Claude.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.models.base import BaseModel


class NurtureSequence(BaseModel):
    """Monthly email nurture programme for a single contact."""

    __tablename__ = "nurture_sequences"

    supplier_id = Column(Integer, nullable=False, index=True)

    # ── Contact ───────────────────────────────────────────────────────────
    contact_email = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=True)

    # ── Sequence config ───────────────────────────────────────────────────
    # monthly_insight | quarterly_update | custom
    sequence_type = Column(String(50), nullable=False, default="monthly_insight")

    # ── Status ────────────────────────────────────────────────────────────
    # active | paused | completed | unsubscribed
    status = Column(String(30), nullable=False, default="active")

    # ── Metrics ───────────────────────────────────────────────────────────
    emails_sent = Column(Integer, nullable=False, default=0)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    next_send_at = Column(DateTime(timezone=True), nullable=True)

    # ── Opt-out ───────────────────────────────────────────────────────────
    unsubscribed = Column(Boolean, nullable=False, default=False)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Cached last generated content ─────────────────────────────────────
    last_email_subject = Column(String(500), nullable=True)
    last_email_body = Column(Text, nullable=True)
