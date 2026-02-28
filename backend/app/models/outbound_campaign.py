"""Outbound campaign model"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class OutboundCampaign(BaseModel):
    """Outbound marketing campaign model"""

    __tablename__ = "outbound_campaigns"

    supplier_id = Column(Integer, nullable=False, index=True)
    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False, index=True)  # linkedin, email, etc.
    status = Column(String(50), default="draft", nullable=False, index=True)  # draft, running, paused, completed

    # Target & ICP
    target_count = Column(Integer, default=0, nullable=False)
    icp_criteria = Column(Text, nullable=True)  # JSON-serialized

    # Performance
    contacts_reached = Column(Integer, default=0, nullable=False)
    responses_received = Column(Integer, default=0, nullable=False)
    response_rate = Column(Integer, nullable=True)  # Percentage
    hot_leads = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<OutboundCampaign {self.campaign_name} ({self.status})>"
