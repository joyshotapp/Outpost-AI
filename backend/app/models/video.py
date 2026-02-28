"""Video model"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class Video(BaseModel):
    """Supplier product video model"""

    __tablename__ = "videos"

    supplier_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    video_type = Column(String(50), nullable=True, index=True)  # product, company, testimonial, etc.
    is_published = Column(Integer, default=True, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Video {self.title}>"
