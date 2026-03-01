"""Add knowledge_documents table

Revision ID: 004
Revises: 003
Create Date: 2026-03-01 18:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_s3_key", sa.String(length=500), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("pinecone_namespace", sa.String(length=255), nullable=False),
        sa.Column("pinecone_document_id", sa.String(length=255), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_knowledge_documents_supplier_id"), "knowledge_documents", ["supplier_id"])
    op.create_index(op.f("ix_knowledge_documents_source_type"), "knowledge_documents", ["source_type"])
    op.create_index(op.f("ix_knowledge_documents_language"), "knowledge_documents", ["language"])
    op.create_index(op.f("ix_knowledge_documents_status"), "knowledge_documents", ["status"])
    op.create_index(op.f("ix_knowledge_documents_pinecone_namespace"), "knowledge_documents", ["pinecone_namespace"])
    op.create_index(op.f("ix_knowledge_documents_pinecone_document_id"), "knowledge_documents", ["pinecone_document_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_documents_pinecone_document_id"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_pinecone_namespace"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_status"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_language"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_source_type"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_supplier_id"), table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
