"""Visitor event tracking model"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class VisitorEvent(BaseModel):
    """Visitor behavior tracking model"""

    __tablename__ = "visitor_events"

    supplier_id = Column(Integer, nullable=False, index=True)
    visitor_session_id = Column(String(255), nullable=False, index=True)
    visitor_email = Column(String(255), nullable=True, index=True)
    visitor_company = Column(String(255), nullable=True, index=True)
    visitor_country = Column(String(2), nullable=True, index=True)

    # Event Data
    event_type = Column(String(50), nullable=False, index=True)  # page_view, click, scroll, etc.
    page_url = Column(String(500), nullable=True)
    event_data = Column(Text, nullable=True)  # JSON-serialized

    # Duration & Intent
    session_duration_seconds = Column(Integer, nullable=True)
    intent_score = Column(Integer, nullable=True)  # 1-100
    intent_level = Column(String(10), nullable=True, index=True)  # low, medium, high

    def __repr__(self) -> str:
        return f"<VisitorEvent {self.event_type}>"
