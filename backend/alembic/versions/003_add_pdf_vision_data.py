"""Add pdf_vision_data field to RFQs table

Revision ID: 003
Revises: 002
Create Date: 2026-03-01 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pdf_vision_data column to rfqs table"""
    op.add_column(
        "rfqs",
        sa.Column("pdf_vision_data", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove pdf_vision_data column from rfqs table"""
    op.drop_column("rfqs", "pdf_vision_data")
