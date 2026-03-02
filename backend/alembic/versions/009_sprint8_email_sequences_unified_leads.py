"""Sprint 8 — Email sequences, unified leads, Instantly/HubSpot campaign fields

Revision ID: 009
Revises: 008
Create Date: 2026-03-03 08:00:00

Changes:
  - Create email_sequences table (Task 8.1/8.2: Instantly email sequence tracking)
  - Create unified_leads table (Task 8.5: all-source lead aggregation)
  - Add Instantly columns to outbound_campaigns (8.1)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── email_sequences ──────────────────────────────────────────────────────
    op.create_table(
        "email_sequences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Foreign keys
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        # Contact identity (denormalised)
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        # Instantly
        sa.Column("instantly_campaign_id", sa.String(length=100), nullable=True),
        sa.Column("instantly_lead_id", sa.String(length=100), nullable=True),
        # Sequence progress
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        # Engagement
        sa.Column("emails_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_opened", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_clicked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reply_received", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reply_text", sa.Text(), nullable=True),
        sa.Column("replied_at", sa.String(length=50), nullable=True),
        # Bounce
        sa.Column("is_bounced", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bounce_type", sa.String(length=20), nullable=True),
        sa.Column("bounced_at", sa.String(length=50), nullable=True),
        # Unsubscribe
        sa.Column("is_unsubscribed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("unsubscribed_at", sa.String(length=50), nullable=True),
        # Hot lead
        sa.Column("is_hot_lead", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("hot_lead_reason", sa.Text(), nullable=True),
        # AI opener
        sa.Column("email_opener", sa.Text(), nullable=True),
        # HubSpot
        sa.Column("hubspot_contact_id", sa.String(length=100), nullable=True),
        sa.Column("hubspot_deal_id", sa.String(length=100), nullable=True),
        sa.Column("hubspot_synced", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_sequences_contact_id", "email_sequences", ["contact_id"])
    op.create_index("ix_email_sequences_campaign_id", "email_sequences", ["campaign_id"])
    op.create_index("ix_email_sequences_supplier_id", "email_sequences", ["supplier_id"])
    op.create_index("ix_email_sequences_email", "email_sequences", ["email"])
    op.create_index("ix_email_sequences_status", "email_sequences", ["status"])
    op.create_index(
        "ix_email_sequences_instantly_campaign_id",
        "email_sequences",
        ["instantly_campaign_id"],
    )

    # ── unified_leads ────────────────────────────────────────────────────────
    op.create_table(
        "unified_leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        # Identity
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("company_domain", sa.String(length=255), nullable=True),
        sa.Column("job_title", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        # Source
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_ref_id", sa.String(length=100), nullable=True),
        # Scoring
        sa.Column("lead_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lead_grade", sa.String(length=1), nullable=True),
        sa.Column("score_breakdown", sa.Text(), nullable=True),
        # Status
        sa.Column("status", sa.String(length=50), nullable=False, server_default="new"),
        sa.Column("recommended_action", sa.String(length=100), nullable=True),
        # Auto reply (C-grade)
        sa.Column("auto_reply_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("auto_reply_sent_at", sa.String(length=50), nullable=True),
        sa.Column("auto_reply_type", sa.String(length=50), nullable=True),
        # Draft reply (B-grade)
        sa.Column("draft_reply_body", sa.Text(), nullable=True),
        sa.Column("draft_reply_generated_at", sa.String(length=50), nullable=True),
        sa.Column("draft_reply_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("draft_reply_sent_at", sa.String(length=50), nullable=True),
        # Hot lead
        sa.Column("is_hot_lead", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("hot_lead_reason", sa.Text(), nullable=True),
        sa.Column("slack_notified", sa.Boolean(), nullable=False, server_default="false"),
        # HubSpot
        sa.Column("hubspot_contact_id", sa.String(length=100), nullable=True),
        sa.Column("hubspot_deal_id", sa.String(length=100), nullable=True),
        sa.Column("hubspot_synced", sa.Boolean(), nullable=False, server_default="false"),
        # Raw
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_unified_leads_supplier_id", "unified_leads", ["supplier_id"])
    op.create_index("ix_unified_leads_email", "unified_leads", ["email"])
    op.create_index("ix_unified_leads_company_name", "unified_leads", ["company_name"])
    op.create_index("ix_unified_leads_source", "unified_leads", ["source"])
    op.create_index("ix_unified_leads_lead_grade", "unified_leads", ["lead_grade"])
    op.create_index("ix_unified_leads_status", "unified_leads", ["status"])
    op.create_index("ix_unified_leads_lead_score", "unified_leads", ["lead_score"])

    # ── outbound_campaigns — add Instantly + email safety columns ────────────
    op.add_column(
        "outbound_campaigns",
        sa.Column("instantly_campaign_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "outbound_campaigns",
        sa.Column("email_sent_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbound_campaigns",
        sa.Column("email_opened_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbound_campaigns",
        sa.Column("email_reply_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbound_campaigns",
        sa.Column("email_bounce_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbound_campaigns",
        sa.Column("email_unsubscribed_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbound_campaigns",
        sa.Column("bounce_rate", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "outbound_campaigns",
        sa.Column("email_safety_paused", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index(
        "ix_outbound_campaigns_instantly_campaign_id",
        "outbound_campaigns",
        ["instantly_campaign_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_outbound_campaigns_instantly_campaign_id", "outbound_campaigns")
    op.drop_column("outbound_campaigns", "email_safety_paused")
    op.drop_column("outbound_campaigns", "bounce_rate")
    op.drop_column("outbound_campaigns", "email_unsubscribed_count")
    op.drop_column("outbound_campaigns", "email_bounce_count")
    op.drop_column("outbound_campaigns", "email_reply_count")
    op.drop_column("outbound_campaigns", "email_opened_count")
    op.drop_column("outbound_campaigns", "email_sent_count")
    op.drop_column("outbound_campaigns", "instantly_campaign_id")

    op.drop_index("ix_unified_leads_lead_score", "unified_leads")
    op.drop_index("ix_unified_leads_status", "unified_leads")
    op.drop_index("ix_unified_leads_lead_grade", "unified_leads")
    op.drop_index("ix_unified_leads_source", "unified_leads")
    op.drop_index("ix_unified_leads_company_name", "unified_leads")
    op.drop_index("ix_unified_leads_email", "unified_leads")
    op.drop_index("ix_unified_leads_supplier_id", "unified_leads")
    op.drop_table("unified_leads")

    op.drop_index("ix_email_sequences_instantly_campaign_id", "email_sequences")
    op.drop_index("ix_email_sequences_status", "email_sequences")
    op.drop_index("ix_email_sequences_email", "email_sequences")
    op.drop_index("ix_email_sequences_supplier_id", "email_sequences")
    op.drop_index("ix_email_sequences_campaign_id", "email_sequences")
    op.drop_index("ix_email_sequences_contact_id", "email_sequences")
    op.drop_table("email_sequences")
