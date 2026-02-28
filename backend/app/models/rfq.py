"""RFQ (Request for Quotation) model"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class RFQ(BaseModel):
    """RFQ inquiry model"""

    __tablename__ = "rfqs"

    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)

    # RFQ Content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    specifications = Column(Text, nullable=True)  # JSON-serialized

    # Quantity & Delivery
    quantity = Column(Integer, nullable=True)
    unit = Column(String(50), nullable=True)
    required_delivery_date = Column(String(50), nullable=True)

    # Attachments
    attachment_url = Column(String(500), nullable=True)  # PDF URL in S3

    # Status & Scoring
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, replied, closed
    lead_score = Column(Integer, nullable=True)  # 1-100
    lead_grade = Column(String(1), nullable=True, index=True)  # A, B, C

    # AI Analysis Results
    parsed_data = Column(Text, nullable=True)  # JSON-serialized parsed RFQ (text)
    pdf_vision_data = Column(Text, nullable=True)  # JSON-serialized PDF vision analysis
    ai_summary = Column(Text, nullable=True)
    draft_reply = Column(Text, nullable=True)

    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id])
    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    def __repr__(self) -> str:
        return f"<RFQ {self.title} ({self.status})>"
