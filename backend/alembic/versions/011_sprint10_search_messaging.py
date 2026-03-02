"""Sprint 10 — search & messaging schema.

New tables:
  saved_suppliers   — buyer bookmark list (buyer_id + supplier_id, unique pair)
  direct_messages   — buyer ↔ supplier real-time messages (linked to conversations)

Revision ID: 011
Revises: 010
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── saved_suppliers ───────────────────────────────────────────────────────
    op.create_table(
        "saved_suppliers",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("buyer_id", sa.Integer, nullable=False, index=True),
        sa.Column("supplier_id", sa.Integer, nullable=False, index=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("buyer_id", "supplier_id", name="uq_saved_buyer_supplier"),
    )
    op.create_index("ix_saved_suppliers_buyer_id", "saved_suppliers", ["buyer_id"])
    op.create_index("ix_saved_suppliers_supplier_id", "saved_suppliers", ["supplier_id"])

    # ── direct_messages ───────────────────────────────────────────────────────
    op.create_table(
        "direct_messages",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("conversation_id", sa.Integer, nullable=False, index=True),
        # 'buyer' | 'supplier' | 'system'
        sa.Column("sender_type", sa.String(20), nullable=False, index=True),
        sa.Column("sender_id", sa.Integer, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, default=False, nullable=False),
        sa.Column("read_at", sa.String(50), nullable=True),
        sa.Column("attachment_url", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_direct_messages_conversation_id", "direct_messages", ["conversation_id"])
    op.create_index("ix_direct_messages_sender_id", "direct_messages", ["sender_id"])

    # ── conversations: add direct-message support ─────────────────────────────
    op.add_column(
        "conversations",
        sa.Column("unread_buyer_count", sa.Integer, server_default="0", nullable=False),
    )
    op.add_column(
        "conversations",
        sa.Column("unread_supplier_count", sa.Integer, server_default="0", nullable=False),
    )
    op.add_column(
        "conversations",
        sa.Column("last_message_at", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "last_message_at")
    op.drop_column("conversations", "unread_supplier_count")
    op.drop_column("conversations", "unread_buyer_count")
    op.drop_index("ix_direct_messages_sender_id", table_name="direct_messages")
    op.drop_index("ix_direct_messages_conversation_id", table_name="direct_messages")
    op.drop_table("direct_messages")
    op.drop_index("ix_saved_suppliers_supplier_id", table_name="saved_suppliers")
    op.drop_index("ix_saved_suppliers_buyer_id", table_name="saved_suppliers")
    op.drop_table("saved_suppliers")
