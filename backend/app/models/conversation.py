"""Conversation model (AI chat & buyer-supplier communication)"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class Conversation(BaseModel):
    """Buyer-supplier or visitor-AI conversation model"""

    __tablename__ = "conversations"

    supplier_id = Column(Integer, nullable=False, index=True)
    buyer_id = Column(Integer, nullable=True, index=True)
    visitor_session_id = Column(String(255), nullable=True, index=True)

    # Conversation Context
    conversation_type = Column(String(50), default="ai_chat", nullable=False, index=True)  # ai_chat, buyer_inquiry, etc.
    subject = Column(String(255), nullable=True)
    language = Column(String(10), default="en", nullable=False)

    # Status
    status = Column(String(50), default="active", nullable=False, index=True)  # active, closed, resolved
    is_escalated = Column(Integer, default=False, nullable=False, index=True)

    # Metadata
    message_count = Column(Integer, default=0, nullable=False)
    ai_confidence_score = Column(Integer, nullable=True)  # For AI responses

    def __repr__(self) -> str:
        return f"<Conversation {self.conversation_type}:{self.status}>"
