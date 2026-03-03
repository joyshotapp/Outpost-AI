"""Remarketing sequence model — Sprint 12 (Task 12.4).

Tracks re-engagement sequences triggered by:
  - C-grade leads: re-scored after 90 days
  - B-grade leads: enter automated nurture sequence after 30 days
  - Custom: manually triggered by supplier
"""

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.models.base import BaseModel


class RemarketingSequence(BaseModel):
    """Automated re-marketing sequence entry for a lead/contact."""

    __tablename__ = "remarketing_sequences"

    supplier_id = Column(Integer, nullable=False, index=True)
    rfq_id = Column(Integer, nullable=True, index=True)         # source RFQ

    # ── Contact ───────────────────────────────────────────────────────────
    contact_email = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(200), nullable=True)

    # ── Trigger type ─────────────────────────────────────────────────────
    # c_grade_90d | b_grade_30d | custom
    trigger_type = Column(String(50), nullable=False)

    # ── Lead scoring ─────────────────────────────────────────────────────
    original_lead_grade = Column(String(5), nullable=True)      # A | B | C
    rescored_lead_grade = Column(String(5), nullable=True)
    original_lead_score = Column(Integer, nullable=True)
    rescored_lead_score = Column(Integer, nullable=True)

    # ── Sequence state ────────────────────────────────────────────────────
    # scheduled | running | completed | paused | cancelled
    status = Column(String(30), nullable=False, default="scheduled")
    sequence_step = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=3)

    # ── Scheduling ────────────────────────────────────────────────────────
    next_action_at = Column(DateTime(timezone=True), nullable=True)
    last_action_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
