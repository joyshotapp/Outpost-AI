"""Sprint 11: Subscriptions table + subscription_tier on suppliers

Revision ID: 012
Revises: 011
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── subscriptions ────────────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        # Plan tier: free | starter | professional | enterprise
        sa.Column("plan_tier", sa.String(30), nullable=False, server_default="free"),
        # Stripe IDs
        sa.Column("stripe_customer_id", sa.String(255), nullable=True, unique=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True, unique=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        # Status: active | past_due | canceled | trialing | incomplete
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        # Billing periods
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # ── subscription_tier column on suppliers ────────────────────────────────
    op.add_column(
        "suppliers",
        sa.Column("subscription_tier", sa.String(30), nullable=False, server_default="free"),
    )

    # ── api_usage_records ────────────────────────────────────────────────────
    op.create_table(
        "api_usage_records",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("supplier_id", sa.Integer, sa.ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True),
        # Service name: openai | anthropic | heygen | stripe | clay | heyreach | instantly | apollo | opusclip | repurpose
        sa.Column("service_name", sa.String(50), nullable=False, index=True),
        # Endpoint / operation label
        sa.Column("operation", sa.String(100), nullable=True),
        # Cost in USD (0 for free-tier operations)
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        # Units: tokens, minutes, requests, etc.
        sa.Column("units", sa.Integer, nullable=True),
        sa.Column("unit_type", sa.String(30), nullable=True),  # tokens | minutes | requests
        # Metadata JSON
        sa.Column("meta", sa.Text, nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # ── system_settings ──────────────────────────────────────────────────────
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    # ── content_review_queue ─────────────────────────────────────────────────
    op.add_column(
        "content_items",
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
    )
    op.add_column(
        "content_items",
        sa.Column("review_note", sa.Text, nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_items", "reviewed_at")
    op.drop_column("content_items", "review_note")
    op.drop_column("content_items", "review_status")
    op.drop_table("system_settings")
    op.drop_table("api_usage_records")
    op.drop_column("suppliers", "subscription_tier")
    op.drop_table("subscriptions")
