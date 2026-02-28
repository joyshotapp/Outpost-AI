"""Initial schema creation

Revision ID: 001
Revises: None
Create Date: 2026-02-28 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables"""
    # This will be populated by alembic autogenerate
    # For now, this is a placeholder
    pass


def downgrade() -> None:
    """Drop initial tables"""
    # This will be populated by alembic autogenerate
    # For now, this is a placeholder
    pass
