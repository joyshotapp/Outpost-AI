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
    bind = op.get_bind()
    from sqlalchemy.engine.reflection import Inspector
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    if "content_items" not in existing_tables:
        # Create full table (fresh install)
        op.create_table(
            "content_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("supplier_id", sa.Integer(), nullable=False),
            sa.Column("source_video_id", sa.Integer(), nullable=True),
            sa.Column("content_type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("keywords", sa.String(length=500), nullable=True),
            sa.Column("hashtags", sa.String(length=500), nullable=True),
            sa.Column("excerpt", sa.Text(), nullable=True),
            sa.Column("source_transcript_chunk", sa.Text(), nullable=True),
            sa.Column("opusclip_job_id", sa.String(length=100), nullable=True),
            sa.Column("short_video_url", sa.String(length=1000), nullable=True),
            sa.Column("short_video_duration_s", sa.Integer(), nullable=True),
            sa.Column("opusclip_highlights_score", sa.Integer(), nullable=True),
            sa.Column("repurpose_job_id", sa.String(length=100), nullable=True),
            sa.Column("platform", sa.String(length=50), nullable=True),
            sa.Column("platform_post_id", sa.String(length=200), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
            sa.Column("scheduled_publish_date", sa.String(length=50), nullable=True),
            sa.Column("published_at", sa.String(length=50), nullable=True),
            sa.Column("published_url", sa.String(length=1000), nullable=True),
            sa.Column("review_notes", sa.Text(), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("quality_checked", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("quality_score", sa.Integer(), nullable=True),
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
    else:
        # Table exists from migration 002 — add Sprint 9 columns only if missing
        existing_cols = {c["name"] for c in inspector.get_columns("content_items")}
        sprint9_cols = [
            ("hashtags", sa.Column("hashtags", sa.String(length=500), nullable=True)),
            ("excerpt", sa.Column("excerpt", sa.Text(), nullable=True)),
            ("source_transcript_chunk", sa.Column("source_transcript_chunk", sa.Text(), nullable=True)),
            ("opusclip_job_id", sa.Column("opusclip_job_id", sa.String(length=100), nullable=True)),
            ("short_video_url", sa.Column("short_video_url", sa.String(length=1000), nullable=True)),
            ("short_video_duration_s", sa.Column("short_video_duration_s", sa.Integer(), nullable=True)),
            ("opusclip_highlights_score", sa.Column("opusclip_highlights_score", sa.Integer(), nullable=True)),
            ("repurpose_job_id", sa.Column("repurpose_job_id", sa.String(length=100), nullable=True)),
            ("platform", sa.Column("platform", sa.String(length=50), nullable=True)),
            ("platform_post_id", sa.Column("platform_post_id", sa.String(length=200), nullable=True)),
            ("published_at", sa.Column("published_at", sa.String(length=50), nullable=True)),
            ("review_notes", sa.Column("review_notes", sa.Text(), nullable=True)),
            ("reviewed_by", sa.Column("reviewed_by", sa.Integer(), nullable=True)),
            ("quality_checked", sa.Column("quality_checked", sa.Boolean(), nullable=False, server_default="false")),
            ("quality_score", sa.Column("quality_score", sa.Integer(), nullable=True)),
            ("likes", sa.Column("likes", sa.Integer(), nullable=False, server_default="0")),
            ("shares", sa.Column("shares", sa.Integer(), nullable=False, server_default="0")),
            ("comments", sa.Column("comments", sa.Integer(), nullable=False, server_default="0")),
            ("last_analytics_sync", sa.Column("last_analytics_sync", sa.String(length=50), nullable=True)),
        ]
        for col_name, col_def in sprint9_cols:
            if col_name not in existing_cols:
                op.add_column("content_items", col_def)

        existing_indexes = {i["name"] for i in inspector.get_indexes("content_items")}
        if "ix_content_items_platform" not in existing_indexes:
            op.create_index("ix_content_items_platform", "content_items", ["platform"])
        if "ix_content_items_opusclip_job_id" not in existing_indexes:
            op.create_index("ix_content_items_opusclip_job_id", "content_items", ["opusclip_job_id"])


def downgrade() -> None:
    op.drop_table("content_items")
