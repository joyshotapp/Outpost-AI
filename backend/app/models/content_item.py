"""Content item model (generated content) — Sprint 9 enhanced."""

from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime

from app.models.base import BaseModel


class ContentItem(BaseModel):
    """Generated content model (LinkedIn posts, SEO articles, short videos).

    content_type values:
        linkedin_post  — AI-generated LinkedIn post (up to 30 per video)
        seo_article    — Long-form SEO blog post (up to 10 per video)
        short_video    — OpusClip-generated short clip (up to 10 per video)

    status lifecycle:
        draft → review → approved → scheduled → published → archived
        draft → rejected
    """

    __tablename__ = "content_items"

    supplier_id = Column(Integer, nullable=False, index=True)
    source_video_id = Column(Integer, nullable=True, index=True)

    # ── Content Details ───────────────────────────────────────────────────────
    content_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    keywords = Column(String(500), nullable=True)
    hashtags = Column(String(500), nullable=True)            # comma-separated hashtags
    excerpt = Column(Text, nullable=True)                    # 280-char summary for preview

    # ── Source transcript excerpt used for generation ─────────────────────────
    source_transcript_chunk = Column(Text, nullable=True)

    # ── Short-video (OpusClip) fields ─────────────────────────────────────────
    opusclip_job_id = Column(String(100), nullable=True, index=True)
    short_video_url = Column(String(1000), nullable=True)
    short_video_duration_s = Column(Integer, nullable=True)  # seconds
    opusclip_highlights_score = Column(Integer, nullable=True)  # 0-100

    # ── Repurpose.io publishing ───────────────────────────────────────────────
    repurpose_job_id = Column(String(100), nullable=True)
    platform = Column(String(50), nullable=True, index=True)  # linkedin, youtube, instagram
    platform_post_id = Column(String(200), nullable=True)     # external ID after publish

    # ── Status & Publishing ───────────────────────────────────────────────────
    status = Column(String(50), default="draft", nullable=False, index=True)
    # draft | review | approved | scheduled | published | rejected | archived
    scheduled_publish_date = Column(String(50), nullable=True)
    published_at = Column(String(50), nullable=True)
    published_url = Column(String(1000), nullable=True)

    # ── Review workflow ───────────────────────────────────────────────────────
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True)             # FK → users.id
    quality_checked = Column(Boolean, default=False, nullable=False)
    quality_score = Column(Integer, nullable=True)           # 0-100 from AI guard

    # ── Sprint 11: Admin content review queue ────────────────────────────────
    review_status = Column(String(20), default="pending", nullable=False)
    # pending | approved | rejected | flagged
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Performance metrics (synced from platform analytics) ─────────────────
    impressions = Column(Integer, default=0, nullable=False)
    engagements = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    shares = Column(Integer, default=0, nullable=False)
    comments = Column(Integer, default=0, nullable=False)
    last_analytics_sync = Column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<ContentItem {self.content_type}:{self.status} supplier={self.supplier_id}>"
