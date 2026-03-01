"""LinkedIn sequence tracking model — per-contact HeyReach sequence state"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.models.base import BaseModel


class LinkedInSequence(BaseModel):
    """Tracks the state of a single contact inside a HeyReach LinkedIn sequence.

    sequence_status lifecycle:
        queued     → waiting to be sent to HeyReach
        active     → sequence is running (Day 1–25)
        replied    → contact replied (sequence paused)
        declined   → connection request declined
        completed  → all sequence steps finished, no reply
        paused     → manually paused or safety limit hit
        failed     → error during sequence setup
    """

    __tablename__ = "linkedin_sequences"

    campaign_id = Column(Integer, nullable=False, index=True)
    contact_id = Column(Integer, nullable=False, index=True)   # FK → outbound_contacts.id
    supplier_id = Column(Integer, nullable=False, index=True)

    # ── HeyReach IDs ────────────────────────────────────────────────────────
    heyreach_campaign_id = Column(String(100), nullable=True, index=True)
    heyreach_contact_id = Column(String(100), nullable=True, index=True)

    # ── Sequence progress ───────────────────────────────────────────────────
    sequence_status = Column(
        String(50),
        default="queued",
        nullable=False,
        index=True,
    )
    current_day = Column(Integer, default=0, nullable=False)    # 0 = not started, 1–25
    total_days = Column(Integer, default=25, nullable=False)

    # ── Events ──────────────────────────────────────────────────────────────
    connection_sent_at = Column(String(50), nullable=True)     # ISO datetime string
    connection_accepted_at = Column(String(50), nullable=True)
    first_message_sent_at = Column(String(50), nullable=True)
    replied_at = Column(String(50), nullable=True)
    reply_content = Column(Text, nullable=True)

    # ── Hot lead ────────────────────────────────────────────────────────────
    is_hot_lead = Column(Boolean, default=False, nullable=False, index=True)
    hot_lead_flagged_at = Column(String(50), nullable=True)
    slack_notified = Column(Boolean, default=False, nullable=False)

    # ── Safety ──────────────────────────────────────────────────────────────
    paused_reason = Column(String(200), nullable=True)         # e.g. "daily_limit_reached"

    # ── Stats ───────────────────────────────────────────────────────────────
    open_rate = Column(Float, nullable=True)
    reply_rate = Column(Float, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LinkedInSequence contact={self.contact_id} "
            f"campaign={self.campaign_id} day={self.current_day}/{self.total_days} "
            f"[{self.sequence_status}]>"
        )
