"""In-app notification model"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class Notification(BaseModel):
    """Supplier in-app notification"""

    __tablename__ = "notifications"

    supplier_id = Column(Integer, nullable=False, index=True)
    conversation_id = Column(Integer, nullable=True, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Integer, default=0, nullable=False, index=True)
    metadata_json = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Notification {self.notification_type}:{self.supplier_id}>"
