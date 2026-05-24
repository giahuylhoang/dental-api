"""add_rag_tables

Revision ID: aa11bb22cc33
Revises: 09a9594d0261
Create Date: 2026-05-23 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "aa11bb22cc33"
down_revision: Union[str, None] = "09a9594d0261"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "clinic_faqs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.String(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_clinic_faqs_by_clinic", "clinic_faqs", ["clinic_id", "ordering"])

    if is_pg:
        # rag_docs uses pg-only column types (pgvector Vector + JSONB). Skip on
        # other dialects so SQLite-based alembic round-trip tests stay green.
        # Production always uses Postgres.
        op.create_table(
            "rag_docs",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("clinic_id", sa.String(), sa.ForeignKey("clinics.id"), nullable=False),
            sa.Column("doc_title", sa.Text(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("voice_ready", sa.Text(), nullable=True),
            sa.Column("embedding", sa.Text(), nullable=True),  # placeholder, retyped below
            sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        )
        op.execute("ALTER TABLE rag_docs ALTER COLUMN embedding TYPE vector(768) USING NULL")
        op.create_index("ix_rag_docs_by_clinic", "rag_docs", ["clinic_id"])
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_rag_docs_hnsw "
            "ON rag_docs USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute("DROP INDEX IF EXISTS ix_rag_docs_hnsw")
        op.drop_index("ix_rag_docs_by_clinic", table_name="rag_docs")
        op.drop_table("rag_docs")
    op.drop_index("ix_clinic_faqs_by_clinic", table_name="clinic_faqs")
    op.drop_table("clinic_faqs")
    # vector extension left in place — other features may use it.
