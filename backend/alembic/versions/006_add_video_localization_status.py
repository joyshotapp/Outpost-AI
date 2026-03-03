"""Add localization status fields to video_language_versions

Revision ID: 006
Revises: 005
Create Date: 2026-03-01

Sprint 6 — creates video_language_versions table (missing from 002) and adds
status tracking, CDN URL, provider job ID, and compression ratio fields.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists (idempotent)
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    if "video_language_versions" not in existing_tables:
        # Create full table (was missing from migration 002)
        op.create_table(
            "video_language_versions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
            sa.Column("language_code", sa.String(10), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("subtitle_url", sa.String(500), nullable=True),
            sa.Column("voice_url", sa.String(500), nullable=True),
            # Sprint 6 fields included at creation
            sa.Column("localization_status", sa.String(30), server_default="pending", nullable=False),
            sa.Column("provider_job_id", sa.String(255), nullable=True),
            sa.Column("cdn_url", sa.String(500), nullable=True),
            sa.Column("compression_ratio", sa.Float(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_video_language_versions_video_id", "video_language_versions", ["video_id"])
        op.create_index("ix_video_language_versions_language_code", "video_language_versions", ["language_code"])
        op.create_index("ix_video_language_versions_localization_status", "video_language_versions", ["localization_status"])
        op.create_index("ix_video_language_versions_provider_job_id", "video_language_versions", ["provider_job_id"])
    else:
        # Table exists — add Sprint 6 columns if missing
        existing_cols = {c["name"] for c in inspector.get_columns("video_language_versions")}
        if "localization_status" not in existing_cols:
            op.add_column("video_language_versions", sa.Column("localization_status", sa.String(30), nullable=False, server_default="pending"))
            op.create_index("ix_video_language_versions_localization_status", "video_language_versions", ["localization_status"])
        if "provider_job_id" not in existing_cols:
            op.add_column("video_language_versions", sa.Column("provider_job_id", sa.String(255), nullable=True))
            op.create_index("ix_video_language_versions_provider_job_id", "video_language_versions", ["provider_job_id"])
        if "cdn_url" not in existing_cols:
            op.add_column("video_language_versions", sa.Column("cdn_url", sa.String(500), nullable=True))
        if "compression_ratio" not in existing_cols:
            op.add_column("video_language_versions", sa.Column("compression_ratio", sa.Float(), nullable=True))
        if "error_message" not in existing_cols:
            op.add_column("video_language_versions", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_table("video_language_versions")
