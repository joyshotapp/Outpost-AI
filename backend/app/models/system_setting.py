"""SystemSetting model — Sprint 11: platform-wide key-value settings"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.models.base import BaseModel


class SystemSetting(BaseModel):
    """Key-value store for platform-wide configuration (admin-managed)."""

    __tablename__ = "system_settings"

    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    def __repr__(self) -> str:
        return f"<SystemSetting {self.key}={self.value!r}>"
