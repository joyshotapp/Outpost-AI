"""Add business tables (RFQ, Videos, Visitor Events, Outbound, Content, Conversations)

Revision ID: 002
Revises: 001
Create Date: 2026-02-28 01:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create business tables"""

    # RFQs table
    op.create_table(
        "rfqs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("buyer_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("specifications", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("required_delivery_date", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("lead_score", sa.Integer(), nullable=True),
        sa.Column("lead_grade", sa.String(length=1), nullable=True),
        sa.Column("parsed_data", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("draft_reply", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rfqs_buyer_id"), "rfqs", ["buyer_id"])
    op.create_index(op.f("ix_rfqs_lead_grade"), "rfqs", ["lead_grade"])
    op.create_index(op.f("ix_rfqs_status"), "rfqs", ["status"])
    op.create_index(op.f("ix_rfqs_supplier_id"), "rfqs", ["supplier_id"])

    # Videos table
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("video_url", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("video_type", sa.String(length=50), nullable=True),
        sa.Column("is_published", sa.Integer(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_videos_supplier_id"), "videos", ["supplier_id"])
    op.create_index(op.f("ix_videos_video_type"), "videos", ["video_type"])

    # Visitor Events table
    op.create_table(
        "visitor_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("visitor_session_id", sa.String(length=255), nullable=False),
        sa.Column("visitor_email", sa.String(length=255), nullable=True),
        sa.Column("visitor_company", sa.String(length=255), nullable=True),
        sa.Column("visitor_country", sa.String(length=2), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("page_url", sa.String(length=500), nullable=True),
        sa.Column("event_data", sa.Text(), nullable=True),
        sa.Column("session_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("intent_score", sa.Integer(), nullable=True),
        sa.Column("intent_level", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_visitor_events_event_type"), "visitor_events", ["event_type"])
    op.create_index(op.f("ix_visitor_events_intent_level"), "visitor_events", ["intent_level"])
    op.create_index(op.f("ix_visitor_events_supplier_id"), "visitor_events", ["supplier_id"])
    op.create_index(op.f("ix_visitor_events_visitor_country"), "visitor_events", ["visitor_country"])
    op.create_index(op.f("ix_visitor_events_visitor_email"), "visitor_events", ["visitor_email"])
    op.create_index(op.f("ix_visitor_events_visitor_session_id"), "visitor_events", ["visitor_session_id"])

    # Outbound Campaigns table
    op.create_table(
        "outbound_campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("campaign_name", sa.String(length=255), nullable=False),
        sa.Column("campaign_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("icp_criteria", sa.Text(), nullable=True),
        sa.Column("contacts_reached", sa.Integer(), nullable=False),
        sa.Column("responses_received", sa.Integer(), nullable=False),
        sa.Column("response_rate", sa.Integer(), nullable=True),
        sa.Column("hot_leads", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outbound_campaigns_campaign_type"), "outbound_campaigns", ["campaign_type"])
    op.create_index(op.f("ix_outbound_campaigns_status"), "outbound_campaigns", ["status"])
    op.create_index(op.f("ix_outbound_campaigns_supplier_id"), "outbound_campaigns", ["supplier_id"])

    # Content Items table
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
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("scheduled_publish_date", sa.String(length=50), nullable=True),
        sa.Column("published_url", sa.String(length=500), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("engagements", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_items_content_type"), "content_items", ["content_type"])
    op.create_index(op.f("ix_content_items_source_video_id"), "content_items", ["source_video_id"])
    op.create_index(op.f("ix_content_items_status"), "content_items", ["status"])
    op.create_index(op.f("ix_content_items_supplier_id"), "content_items", ["supplier_id"])

    # Conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("buyer_id", sa.Integer(), nullable=True),
        sa.Column("visitor_session_id", sa.String(length=255), nullable=True),
        sa.Column("conversation_type", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("is_escalated", sa.Integer(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("ai_confidence_score", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_buyer_id"), "conversations", ["buyer_id"])
    op.create_index(op.f("ix_conversations_is_escalated"), "conversations", ["is_escalated"])
    op.create_index(op.f("ix_conversations_status"), "conversations", ["status"])
    op.create_index(op.f("ix_conversations_supplier_id"), "conversations", ["supplier_id"])
    op.create_index(op.f("ix_conversations_visitor_session_id"), "conversations", ["visitor_session_id"])


def downgrade() -> None:
    """Drop business tables"""
    op.drop_index(op.f("ix_conversations_visitor_session_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_supplier_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_status"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_is_escalated"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_buyer_id"), table_name="conversations")
    op.drop_table("conversations")

    op.drop_index(op.f("ix_content_items_supplier_id"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_status"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_source_video_id"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_content_type"), table_name="content_items")
    op.drop_table("content_items")

    op.drop_index(op.f("ix_outbound_campaigns_supplier_id"), table_name="outbound_campaigns")
    op.drop_index(op.f("ix_outbound_campaigns_status"), table_name="outbound_campaigns")
    op.drop_index(op.f("ix_outbound_campaigns_campaign_type"), table_name="outbound_campaigns")
    op.drop_table("outbound_campaigns")

    op.drop_index(op.f("ix_visitor_events_visitor_session_id"), table_name="visitor_events")
    op.drop_index(op.f("ix_visitor_events_visitor_email"), table_name="visitor_events")
    op.drop_index(op.f("ix_visitor_events_visitor_country"), table_name="visitor_events")
    op.drop_index(op.f("ix_visitor_events_intent_level"), table_name="visitor_events")
    op.drop_index(op.f("ix_visitor_events_event_type"), table_name="visitor_events")
    op.drop_index(op.f("ix_visitor_events_supplier_id"), table_name="visitor_events")
    op.drop_table("visitor_events")

    op.drop_index(op.f("ix_videos_video_type"), table_name="videos")
    op.drop_index(op.f("ix_videos_supplier_id"), table_name="videos")
    op.drop_table("videos")

    op.drop_index(op.f("ix_rfqs_supplier_id"), table_name="rfqs")
    op.drop_index(op.f("ix_rfqs_status"), table_name="rfqs")
    op.drop_index(op.f("ix_rfqs_lead_grade"), table_name="rfqs")
    op.drop_index(op.f("ix_rfqs_buyer_id"), table_name="rfqs")
    op.drop_table("rfqs")
