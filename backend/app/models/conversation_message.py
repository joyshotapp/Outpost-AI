"""Conversation message model for AI chat history"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class ConversationMessage(BaseModel):
    """Individual message in conversation"""

    __tablename__ = "conversation_messages"

    conversation_id = Column(Integer, nullable=False, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    sender_type = Column(String(20), nullable=False, index=True)
    message_text = Column(Text, nullable=False)
    language = Column(String(10), default="en", nullable=False, index=True)
    confidence_score = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<ConversationMessage {self.conversation_id}:{self.sender_type}>"
