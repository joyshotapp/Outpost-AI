"""HeyGen usage / cost tracking model — Sprint 6"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from app.models.base import Base


class HeyGenUsageRecord(Base):
    """Records each HeyGen localization job for cost + quota tracking.

    Estimated cost = minutes_processed * HEYGEN_COST_PER_MINUTE.
    """

    __tablename__ = "heygen_usage_records"

    id = Column(Integer, primary_key=True, index=True)

    # Source context
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    language_code = Column(String(10), nullable=False)

    # HeyGen job details
    provider_job_id = Column(String(128), nullable=True, unique=True, index=True)
    job_status = Column(String(32), nullable=False, default="completed")  # completed | failed | skipped

    # Cost metrics
    source_duration_seconds = Column(Float, nullable=True)  # source video length
    minutes_processed = Column(Float, nullable=True)  # billable minutes
    cost_usd = Column(Float, nullable=True)  # estimated cost in USD

    # Error info (for failed jobs)
    error_message = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_heygen_usage_video_lang", "video_id", "language_code"),
        Index("ix_heygen_usage_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<HeyGenUsageRecord id={self.id} video_id={self.video_id} "
            f"lang={self.language_code} cost={self.cost_usd}>"
        )
