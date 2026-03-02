"""Conversation model (AI chat & buyer-supplier communication)"""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Conversation(BaseModel):
    """Buyer-supplier or visitor-AI conversation model"""

    __tablename__ = "conversations"

    supplier_id = Column(Integer, nullable=False, index=True)
    buyer_id = Column(Integer, nullable=True, index=True)
    visitor_session_id = Column(String(255), nullable=True, index=True)

    # Conversation Context
    conversation_type = Column(String(50), default="ai_chat", nullable=False, index=True)  # ai_chat, direct, buyer_inquiry, etc.
    subject = Column(String(255), nullable=True)
    language = Column(String(10), default="en", nullable=False)

    # Status
    status = Column(String(50), default="active", nullable=False, index=True)  # active, closed, resolved
    is_escalated = Column(Integer, default=False, nullable=False, index=True)

    # Metadata
    message_count = Column(Integer, default=0, nullable=False)
    ai_confidence_score = Column(Integer, nullable=True)  # For AI responses

    # Sprint 10: direct messaging counters
    unread_buyer_count = Column(Integer, default=0, nullable=False, server_default="0")
    unread_supplier_count = Column(Integer, default=0, nullable=False, server_default="0")
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    direct_messages = relationship(
        "DirectMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.conversation_type}:{self.status}>"
