"""ApiUsageRecord model — Sprint 11: API usage tracking"""

from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.sql import func

from app.models.base import BaseModel


class ApiUsageRecord(BaseModel):
    """Tracks third-party API cost per call/batch per supplier."""

    __tablename__ = "api_usage_records"

    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    # e.g. openai | anthropic | heygen | stripe | clay | heyreach | instantly | apollo | opusclip | repurpose
    service_name = Column(String(50), nullable=False, index=True)
    operation = Column(String(100), nullable=True)     # e.g. "rfq_parse", "video_localize"
    cost_usd = Column(Numeric(10, 6), nullable=False, default=Decimal("0"))
    units = Column(Integer, nullable=True)              # tokens, minutes, requests …
    unit_type = Column(String(30), nullable=True)       # "tokens" | "minutes" | "requests"
    meta = Column(Text, nullable=True)                  # JSON blob for extra context
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<ApiUsageRecord service={self.service_name} cost=${self.cost_usd}>"
