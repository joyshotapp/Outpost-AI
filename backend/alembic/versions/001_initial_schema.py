"""Initial schema with core tables (users, suppliers, buyers)

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

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column(
            "role",
            sa.Enum("buyer", "supplier", "admin", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"])
    op.create_index(op.f("ix_users_role"), "users", ["role"])

    # Suppliers table
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("company_slug", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("company_description", sa.Text(), nullable=True),
        sa.Column("number_of_employees", sa.Integer(), nullable=True),
        sa.Column("established_year", sa.Integer(), nullable=True),
        sa.Column("certifications", sa.String(length=500), nullable=True),
        sa.Column("main_products", sa.String(length=500), nullable=True),
        sa.Column("manufacturing_capacity", sa.String(length=255), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suppliers_company_name"), "suppliers", ["company_name"])
    op.create_index(op.f("ix_suppliers_company_slug"), "suppliers", ["company_slug"], unique=True)
    op.create_index(op.f("ix_suppliers_country"), "suppliers", ["country"])
    op.create_index(op.f("ix_suppliers_industry"), "suppliers", ["industry"])
    op.create_index(op.f("ix_suppliers_is_active"), "suppliers", ["is_active"])
    op.create_index(op.f("ix_suppliers_is_verified"), "suppliers", ["is_verified"])
    op.create_index(op.f("ix_suppliers_user_id"), "suppliers", ["user_id"])

    # Buyers table
    op.create_table(
        "buyers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("company_description", sa.Text(), nullable=True),
        sa.Column("number_of_employees", sa.Integer(), nullable=True),
        sa.Column("primary_sourcing_needs", sa.String(length=500), nullable=True),
        sa.Column("annual_sourcing_budget", sa.Integer(), nullable=True),
        sa.Column("preferred_payment_terms", sa.String(length=100), nullable=True),
        sa.Column("preferred_shipping_method", sa.String(length=100), nullable=True),
        sa.Column("import_experience", sa.String(length=50), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_buyers_company_name"), "buyers", ["company_name"])
    op.create_index(op.f("ix_buyers_country"), "buyers", ["country"])
    op.create_index(op.f("ix_buyers_industry"), "buyers", ["industry"])
    op.create_index(op.f("ix_buyers_is_active"), "buyers", ["is_active"])
    op.create_index(op.f("ix_buyers_is_verified"), "buyers", ["is_verified"])
    op.create_index(op.f("ix_buyers_user_id"), "buyers", ["user_id"])


def downgrade() -> None:
    """Drop initial tables"""
    op.drop_index(op.f("ix_buyers_user_id"), table_name="buyers")
    op.drop_index(op.f("ix_buyers_is_verified"), table_name="buyers")
    op.drop_index(op.f("ix_buyers_is_active"), table_name="buyers")
    op.drop_index(op.f("ix_buyers_industry"), table_name="buyers")
    op.drop_index(op.f("ix_buyers_country"), table_name="buyers")
    op.drop_index(op.f("ix_buyers_company_name"), table_name="buyers")
    op.drop_table("buyers")

    op.drop_index(op.f("ix_suppliers_user_id"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_is_verified"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_is_active"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_industry"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_country"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_company_slug"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_company_name"), table_name="suppliers")
    op.drop_table("suppliers")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
