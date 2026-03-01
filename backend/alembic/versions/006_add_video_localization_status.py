"""Add localization status fields to video_language_versions

Revision ID: 006
Revises: 005
Create Date: 2026-03-01

Sprint 6 — adds status tracking, CDN URL, provider job ID, and compression ratio
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "video_language_versions",
        sa.Column(
            "localization_status",
            sa.String(30),
            nullable=False,
            server_default="pending",
        ),
    )
    op.create_index(
        "ix_video_language_versions_localization_status",
        "video_language_versions",
        ["localization_status"],
    )
    op.add_column(
        "video_language_versions",
        sa.Column("provider_job_id", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_video_language_versions_provider_job_id",
        "video_language_versions",
        ["provider_job_id"],
    )
    op.add_column(
        "video_language_versions",
        sa.Column("cdn_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "video_language_versions",
        sa.Column("compression_ratio", sa.Float(), nullable=True),
    )
    op.add_column(
        "video_language_versions",
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_index("ix_video_language_versions_provider_job_id", "video_language_versions")
    op.drop_index("ix_video_language_versions_localization_status", "video_language_versions")
    op.drop_column("video_language_versions", "error_message")
    op.drop_column("video_language_versions", "compression_ratio")
    op.drop_column("video_language_versions", "cdn_url")
    op.drop_column("video_language_versions", "provider_job_id")
    op.drop_column("video_language_versions", "localization_status")
