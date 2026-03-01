"""Add conversation_messages and notifications tables

Revision ID: 005
Revises: 004
Create Date: 2026-03-01 19:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("sender_type", sa.String(length=20), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_conversation_messages_conversation_id"), "conversation_messages", ["conversation_id"])
    op.create_index(op.f("ix_conversation_messages_supplier_id"), "conversation_messages", ["supplier_id"])
    op.create_index(op.f("ix_conversation_messages_sender_type"), "conversation_messages", ["sender_type"])
    op.create_index(op.f("ix_conversation_messages_language"), "conversation_messages", ["language"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_notifications_supplier_id"), "notifications", ["supplier_id"])
    op.create_index(op.f("ix_notifications_conversation_id"), "notifications", ["conversation_id"])
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"])
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"])


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_notification_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_conversation_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_supplier_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_conversation_messages_language"), table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_sender_type"), table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_supplier_id"), table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_conversation_id"), table_name="conversation_messages")
    op.drop_table("conversation_messages")
