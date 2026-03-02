"""Sprint 9 — Content items table enhanced for content viral matrix

Revision ID: 010
Revises: 009
Create Date: 2026-03-03 10:00:00

Changes:
  - Create content_items table (Task 9.4: full Sprint 9 schema)
    Adds: short-video fields (OpusClip), Repurpose.io publishing,
          review workflow, extended analytics, quality guard score
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── content_items ────────────────────────────────────────────────────────
    op.create_table(
        "content_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Ownership
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("source_video_id", sa.Integer(), nullable=True),
        # Content details
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("keywords", sa.String(length=500), nullable=True),
        sa.Column("hashtags", sa.String(length=500), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("source_transcript_chunk", sa.Text(), nullable=True),
        # OpusClip short-video fields
        sa.Column("opusclip_job_id", sa.String(length=100), nullable=True),
        sa.Column("short_video_url", sa.String(length=1000), nullable=True),
        sa.Column("short_video_duration_s", sa.Integer(), nullable=True),
        sa.Column("opusclip_highlights_score", sa.Integer(), nullable=True),
        # Repurpose.io publishing
        sa.Column("repurpose_job_id", sa.String(length=100), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("platform_post_id", sa.String(length=200), nullable=True),
        # Status & publishing
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("scheduled_publish_date", sa.String(length=50), nullable=True),
        sa.Column("published_at", sa.String(length=50), nullable=True),
        sa.Column("published_url", sa.String(length=1000), nullable=True),
        # Review workflow
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("quality_checked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        # Analytics
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagements", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_analytics_sync", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_items_supplier_id", "content_items", ["supplier_id"])
    op.create_index("ix_content_items_source_video_id", "content_items", ["source_video_id"])
    op.create_index("ix_content_items_content_type", "content_items", ["content_type"])
    op.create_index("ix_content_items_status", "content_items", ["status"])
    op.create_index("ix_content_items_platform", "content_items", ["platform"])
    op.create_index("ix_content_items_opusclip_job_id", "content_items", ["opusclip_job_id"])


def downgrade() -> None:
    op.drop_table("content_items")
