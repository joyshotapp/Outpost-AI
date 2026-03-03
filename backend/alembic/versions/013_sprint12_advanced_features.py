"""Sprint 12: Exhibitions, business_cards, remarketing_sequences, nurture_sequences

Revision ID: 013
Revises: 012
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── exhibitions ──────────────────────────────────────────────────────────
    op.create_table(
        "exhibitions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        # lifecycle: planning | active | post_show | completed
        sa.Column("status", sa.String(30), nullable=False, server_default="planning"),
        sa.Column("icp_criteria", sa.Text, nullable=True),       # JSON: ICP targeting for pre-show outreach
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("booth_number", sa.String(50), nullable=True),
        sa.Column("contacts_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # ── business_cards ───────────────────────────────────────────────────────
    op.create_table(
        "business_cards",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("exhibition_id", sa.Integer, sa.ForeignKey("exhibitions.id", ondelete="SET NULL"), nullable=True, index=True),
        # Source image
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("raw_ocr_text", sa.Text, nullable=True),
        # Parsed contact info (Claude Vision)
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("job_title", sa.String(200), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        # OCR processing status: pending | processing | completed | failed
        sa.Column("ocr_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("ocr_confidence", sa.Float, nullable=True),
        # CRM conversion
        sa.Column("converted_to_contact", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("contact_id", sa.Integer, nullable=True),      # FK to outbound_contacts if converted
        # Follow-up
        sa.Column("follow_up_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # ── remarketing_sequences ────────────────────────────────────────────────
    op.create_table(
        "remarketing_sequences",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rfq_id", sa.Integer, sa.ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("contact_email", sa.String(255), nullable=False, index=True),
        sa.Column("contact_name", sa.String(200), nullable=True),
        # Trigger: c_grade_90d | b_grade_30d | custom
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("original_lead_grade", sa.String(5), nullable=True),         # A | B | C
        sa.Column("rescored_lead_grade", sa.String(5), nullable=True),
        sa.Column("original_lead_score", sa.Integer, nullable=True),
        sa.Column("rescored_lead_score", sa.Integer, nullable=True),
        # Sequence status: scheduled | running | completed | paused | cancelled
        sa.Column("status", sa.String(30), nullable=False, server_default="scheduled"),
        sa.Column("sequence_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_steps", sa.Integer, nullable=False, server_default="3"),
        sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # ── nurture_sequences ────────────────────────────────────────────────────
    op.create_table(
        "nurture_sequences",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("contact_email", sa.String(255), nullable=False, index=True),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        # Monthly newsletter nurturing for C-grade leads
        sa.Column("sequence_type", sa.String(50), nullable=False, server_default="monthly_insight"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("emails_sent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_send_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unsubscribed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        # Generated email content cache
        sa.Column("last_email_subject", sa.String(500), nullable=True),
        sa.Column("last_email_body", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # ── indexes ──────────────────────────────────────────────────────────────
    op.create_index("ix_exhibitions_status", "exhibitions", ["status"])
    op.create_index("ix_exhibitions_start_date", "exhibitions", ["start_date"])
    op.create_index("ix_business_cards_ocr_status", "business_cards", ["ocr_status"])
    op.create_index("ix_remarketing_status", "remarketing_sequences", ["status"])
    op.create_index("ix_remarketing_next_action", "remarketing_sequences", ["next_action_at"])
    op.create_index("ix_nurture_next_send", "nurture_sequences", ["next_send_at"])


def downgrade() -> None:
    op.drop_index("ix_nurture_next_send", table_name="nurture_sequences")
    op.drop_index("ix_remarketing_next_action", table_name="remarketing_sequences")
    op.drop_index("ix_remarketing_status", table_name="remarketing_sequences")
    op.drop_index("ix_business_cards_ocr_status", table_name="business_cards")
    op.drop_index("ix_exhibitions_start_date", table_name="exhibitions")
    op.drop_index("ix_exhibitions_status", table_name="exhibitions")
    op.drop_table("nurture_sequences")
    op.drop_table("remarketing_sequences")
    op.drop_table("business_cards")
    op.drop_table("exhibitions")
