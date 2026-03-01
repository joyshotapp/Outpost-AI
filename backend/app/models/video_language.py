"""Video language version model"""

from sqlalchemy import Column, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class VideoLanguageVersion(BaseModel):
    """Multi-language version of video content"""

    __tablename__ = "video_language_versions"

    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    language_code = Column(String(10), nullable=False, index=True)  # en, zh, es, fr, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subtitle_url = Column(String(500), nullable=True)  # URL to subtitle file
    voice_url = Column(String(500), nullable=True)  # URL to dubbed voice
    # Sprint 6 additions
    localization_status = Column(String(30), default="pending", nullable=False, index=True)
    # pending | processing | completed | failed | skipped
    provider_job_id = Column(String(255), nullable=True, index=True)  # HeyGen job ID
    cdn_url = Column(String(500), nullable=True)  # CloudFront CDN URL for dubbed video
    compression_ratio = Column(Float, nullable=True)  # actual word-count ratio after DE compression
    error_message = Column(Text, nullable=True)  # last failure reason

    video = relationship("Video", back_populates="language_versions")

    def __repr__(self) -> str:
        return f"<VideoLanguageVersion {self.language_code}>"
