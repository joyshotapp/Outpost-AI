"""Content item model (generated content)"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class ContentItem(BaseModel):
    """Generated content model (LinkedIn posts, SEO articles, etc.)"""

    __tablename__ = "content_items"

    supplier_id = Column(Integer, nullable=False, index=True)
    source_video_id = Column(Integer, nullable=True, index=True)

    # Content Details
    content_type = Column(String(50), nullable=False, index=True)  # linkedin_post, seo_article, short_video, etc.
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    keywords = Column(String(500), nullable=True)

    # Status & Publishing
    status = Column(String(50), default="draft", nullable=False, index=True)  # draft, scheduled, published, archived
    scheduled_publish_date = Column(String(50), nullable=True)
    published_url = Column(String(500), nullable=True)

    # Performance
    impressions = Column(Integer, default=0, nullable=False)
    engagements = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<ContentItem {self.content_type}:{self.status}>"
