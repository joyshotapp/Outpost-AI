"""Sprint 7 — Outbound contacts, LinkedIn sequences, campaign Clay/HeyReach fields

Revision ID: 008
Revises: 007
Create Date: 2026-03-01 08:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create outbound_contacts & linkedin_sequences tables;
    add Clay / HeyReach / safety columns to outbound_campaigns."""

    # ── outbound_contacts ────────────────────────────────────────────────────
    op.create_table(
        "outbound_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        # Identity
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        # Company
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("company_domain", sa.String(length=255), nullable=True),
        sa.Column("company_industry", sa.String(length=100), nullable=True),
        sa.Column("company_size", sa.String(length=50), nullable=True),
        sa.Column("company_country", sa.String(length=100), nullable=True),
        # Role
        sa.Column("job_title", sa.String(length=200), nullable=True),
        sa.Column("seniority", sa.String(length=50), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        # Clay enrichment
        sa.Column("clay_row_id", sa.String(length=100), nullable=True),
        sa.Column("enriched_data", sa.Text(), nullable=True),
        # AI personalisation
        sa.Column("linkedin_opener", sa.Text(), nullable=True),
        sa.Column("opener_generated_at", sa.String(length=50), nullable=True),
        # Status
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("is_hot_lead", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("hot_lead_reason", sa.Text(), nullable=True),
        # Safety
        sa.Column("connection_requests_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_sent", sa.Integer(), nullable=False, server_default="0"),
        # HeyReach
        sa.Column("heyreach_contact_id", sa.String(length=100), nullable=True),
        sa.Column("sequence_day", sa.Integer(), nullable=True),
        # Scoring
        sa.Column("lead_score", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbound_contacts_id", "outbound_contacts", ["id"])
    op.create_index("ix_outbound_contacts_campaign_id", "outbound_contacts", ["campaign_id"])
    op.create_index("ix_outbound_contacts_supplier_id", "outbound_contacts", ["supplier_id"])
    op.create_index("ix_outbound_contacts_full_name", "outbound_contacts", ["full_name"])
    op.create_index("ix_outbound_contacts_email", "outbound_contacts", ["email"])
    op.create_index("ix_outbound_contacts_company_name", "outbound_contacts", ["company_name"])
    op.create_index("ix_outbound_contacts_clay_row_id", "outbound_contacts", ["clay_row_id"], unique=True)
    op.create_index("ix_outbound_contacts_status", "outbound_contacts", ["status"])
    op.create_index("ix_outbound_contacts_is_hot_lead", "outbound_contacts", ["is_hot_lead"])
    op.create_index("ix_outbound_contacts_heyreach_contact_id", "outbound_contacts", ["heyreach_contact_id"])

    # ── linkedin_sequences ───────────────────────────────────────────────────
    op.create_table(
        "linkedin_sequences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        # HeyReach
        sa.Column("heyreach_campaign_id", sa.String(length=100), nullable=True),
        sa.Column("heyreach_contact_id", sa.String(length=100), nullable=True),
        # Progress
        sa.Column("sequence_status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("current_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_days", sa.Integer(), nullable=False, server_default="25"),
        # Events
        sa.Column("connection_sent_at", sa.String(length=50), nullable=True),
        sa.Column("connection_accepted_at", sa.String(length=50), nullable=True),
        sa.Column("first_message_sent_at", sa.String(length=50), nullable=True),
        sa.Column("replied_at", sa.String(length=50), nullable=True),
        sa.Column("reply_content", sa.Text(), nullable=True),
        # Hot lead
        sa.Column("is_hot_lead", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("hot_lead_flagged_at", sa.String(length=50), nullable=True),
        sa.Column("slack_notified", sa.Boolean(), nullable=False, server_default="false"),
        # Safety
        sa.Column("paused_reason", sa.String(length=200), nullable=True),
        # Stats
        sa.Column("open_rate", sa.Float(), nullable=True),
        sa.Column("reply_rate", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_linkedin_sequences_id", "linkedin_sequences", ["id"])
    op.create_index("ix_linkedin_sequences_campaign_id", "linkedin_sequences", ["campaign_id"])
    op.create_index("ix_linkedin_sequences_contact_id", "linkedin_sequences", ["contact_id"])
    op.create_index("ix_linkedin_sequences_supplier_id", "linkedin_sequences", ["supplier_id"])
    op.create_index("ix_linkedin_sequences_heyreach_campaign_id", "linkedin_sequences", ["heyreach_campaign_id"])
    op.create_index("ix_linkedin_sequences_heyreach_contact_id", "linkedin_sequences", ["heyreach_contact_id"])
    op.create_index("ix_linkedin_sequences_sequence_status", "linkedin_sequences", ["sequence_status"])
    op.create_index("ix_linkedin_sequences_is_hot_lead", "linkedin_sequences", ["is_hot_lead"])

    # ── outbound_campaigns — new columns ─────────────────────────────────────
    op.add_column("outbound_campaigns", sa.Column("clay_table_id", sa.String(length=100), nullable=True))
    op.add_column("outbound_campaigns", sa.Column(
        "clay_enrichment_status", sa.String(length=50), nullable=False, server_default="pending"
    ))
    op.add_column("outbound_campaigns", sa.Column("heyreach_campaign_id", sa.String(length=100), nullable=True))
    op.add_column("outbound_campaigns", sa.Column(
        "daily_connections_sent", sa.Integer(), nullable=False, server_default="0"
    ))
    op.add_column("outbound_campaigns", sa.Column(
        "daily_messages_sent", sa.Integer(), nullable=False, server_default="0"
    ))
    op.add_column("outbound_campaigns", sa.Column(
        "safety_paused", sa.Integer(), nullable=False, server_default="0"
    ))
    op.create_index(
        "ix_outbound_campaigns_heyreach_campaign_id",
        "outbound_campaigns",
        ["heyreach_campaign_id"],
    )


def downgrade() -> None:
    """Drop Sprint 7 tables and columns"""
    # outbound_campaigns new columns
    op.drop_index("ix_outbound_campaigns_heyreach_campaign_id", table_name="outbound_campaigns")
    op.drop_column("outbound_campaigns", "safety_paused")
    op.drop_column("outbound_campaigns", "daily_messages_sent")
    op.drop_column("outbound_campaigns", "daily_connections_sent")
    op.drop_column("outbound_campaigns", "heyreach_campaign_id")
    op.drop_column("outbound_campaigns", "clay_enrichment_status")
    op.drop_column("outbound_campaigns", "clay_table_id")

    # linkedin_sequences
    op.drop_index("ix_linkedin_sequences_is_hot_lead", table_name="linkedin_sequences")
    op.drop_index("ix_linkedin_sequences_sequence_status", table_name="linkedin_sequences")
    op.drop_index("ix_linkedin_sequences_heyreach_contact_id", table_name="linkedin_sequences")
    op.drop_index("ix_linkedin_sequences_heyreach_campaign_id", table_name="linkedin_sequences")
    op.drop_index("ix_linkedin_sequences_supplier_id", table_name="linkedin_sequences")
    op.drop_index("ix_linkedin_sequences_contact_id", table_name="linkedin_sequences")
    op.drop_index("ix_linkedin_sequences_campaign_id", table_name="linkedin_sequences")
    op.drop_index("ix_linkedin_sequences_id", table_name="linkedin_sequences")
    op.drop_table("linkedin_sequences")

    # outbound_contacts
    op.drop_index("ix_outbound_contacts_heyreach_contact_id", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_is_hot_lead", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_status", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_clay_row_id", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_company_name", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_email", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_full_name", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_supplier_id", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_campaign_id", table_name="outbound_contacts")
    op.drop_index("ix_outbound_contacts_id", table_name="outbound_contacts")
    op.drop_table("outbound_contacts")
