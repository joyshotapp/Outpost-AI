"""DirectMessage model — Sprint 10 (10.7: buyer ↔ supplier messaging)."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DirectMessage(BaseModel):
    """A single message in a buyer ↔ supplier conversation.

    sender_type values: 'buyer' | 'supplier' | 'system'
    """

    __tablename__ = "direct_messages"

    conversation_id = Column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sender_type = Column(String(20), nullable=False, index=True)   # buyer | supplier | system
    sender_id = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, server_default="false")
    read_at = Column(DateTime(timezone=True), nullable=True)
    attachment_url = Column(String(1000), nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="direct_messages")

    def __repr__(self) -> str:
        return f"<DirectMessage conv={self.conversation_id} from={self.sender_type}>"
