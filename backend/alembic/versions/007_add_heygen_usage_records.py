"""add_heygen_usage_records

Revision ID: 007
Revises: 006
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "heygen_usage_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("language_code", sa.String(10), nullable=False),
        sa.Column("provider_job_id", sa.String(128), nullable=True),
        sa.Column("job_status", sa.String(32), nullable=False, server_default="completed"),
        sa.Column("source_duration_seconds", sa.Float(), nullable=True),
        sa.Column("minutes_processed", sa.Float(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("error_message", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_heygen_usage_records_id", "heygen_usage_records", ["id"])
    op.create_index("ix_heygen_usage_records_video_id", "heygen_usage_records", ["video_id"])
    op.create_index("ix_heygen_usage_records_provider_job_id", "heygen_usage_records", ["provider_job_id"], unique=True)
    op.create_index("ix_heygen_usage_records_created_at", "heygen_usage_records", ["created_at"])
    op.create_index("ix_heygen_usage_video_lang", "heygen_usage_records", ["video_id", "language_code"])


def downgrade() -> None:
    op.drop_index("ix_heygen_usage_video_lang", table_name="heygen_usage_records")
    op.drop_index("ix_heygen_usage_records_created_at", table_name="heygen_usage_records")
    op.drop_index("ix_heygen_usage_records_provider_job_id", table_name="heygen_usage_records")
    op.drop_index("ix_heygen_usage_records_video_id", table_name="heygen_usage_records")
    op.drop_index("ix_heygen_usage_records_id", table_name="heygen_usage_records")
    op.drop_table("heygen_usage_records")
