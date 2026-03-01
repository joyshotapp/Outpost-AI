"""Outbound campaign model"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class OutboundCampaign(BaseModel):
    """Outbound marketing campaign model.

    campaign_type: linkedin | email
    status lifecycle: draft → running → paused → completed
    """

    __tablename__ = "outbound_campaigns"

    supplier_id = Column(Integer, nullable=False, index=True)
    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False, index=True)  # linkedin | email
    status = Column(String(50), default="draft", nullable=False, index=True)

    # ── ICP criteria (JSON-serialised) ──────────────────────────────────────
    icp_criteria = Column(Text, nullable=True)

    # ── Clay integration ────────────────────────────────────────────────────
    clay_table_id = Column(String(100), nullable=True)          # Clay table ID for enrichment
    clay_enrichment_status = Column(
        String(50), default="pending", nullable=False
    )  # pending | running | completed | failed

    # ── HeyReach integration ────────────────────────────────────────────────
    heyreach_campaign_id = Column(String(100), nullable=True, index=True)

    # ── Target & performance counters ───────────────────────────────────────
    target_count = Column(Integer, default=0, nullable=False)
    contacts_reached = Column(Integer, default=0, nullable=False)
    responses_received = Column(Integer, default=0, nullable=False)
    response_rate = Column(Integer, nullable=True)  # Percentage × 100
    hot_leads = Column(Integer, default=0, nullable=False)

    # ── LinkedIn safety daily counters (reset at midnight) ──────────────────
    daily_connections_sent = Column(Integer, default=0, nullable=False)
    daily_messages_sent = Column(Integer, default=0, nullable=False)
    safety_paused = Column(Integer, default=0, nullable=False)  # 0 | 1 bool flag

    def __repr__(self) -> str:
        return f"<OutboundCampaign {self.campaign_name} ({self.status})>"
