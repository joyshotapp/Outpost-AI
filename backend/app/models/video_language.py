"""Video language version model"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey

from app.models.base import BaseModel


class VideoLanguageVersion(BaseModel):
    """Multi-language version of video content"""

    __tablename__ = "video_language_versions"

    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    language_code = Column(String(10), nullable=False, index=True)  # en, zh, es, fr, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subtitle_url = Column(String(500), nullable=True)  # URL to subtitle file
    voice_url = Column(String(500), nullable=True)  # URL to dubbed voice

    def __repr__(self) -> str:
        return f"<VideoLanguageVersion {self.language_code}>"
