"""crm patient attach: patient_notes + documents columns/constraint

Revision ID: k5l6m7n8o9p0
Revises: j4k5l6m7n8o9
Create Date: 2026-06-29 00:00:00.000000

Additive + one constraint swap:
- new `patient_notes` table (lightweight CRM notes)
- `documents` gains `storage_backend` + `original_name`
- `documents` unique constraint moves from (clinic_id, content_sha256)
  to (clinic_id, patient_id, content_sha256) — fixes a cross-patient
  row-reuse leak in dedup.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "k5l6m7n8o9p0"
down_revision: Union[str, Sequence[str], None] = "j4k5l6m7n8o9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_notes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("author_id", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patient_notes_clinic_patient_created",
        "patient_notes",
        ["clinic_id", "patient_id", "created_at"],
    )

    op.add_column(
        "documents",
        sa.Column("storage_backend", sa.String(), nullable=False, server_default="gcs"),
    )
    op.add_column("documents", sa.Column("original_name", sa.String(), nullable=True))
    with op.batch_alter_table("documents") as batch:
        batch.drop_constraint("uq_doc_clinic_sha", type_="unique")
        batch.create_unique_constraint(
            "uq_doc_clinic_patient_sha",
            ["clinic_id", "patient_id", "content_sha256"],
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.drop_constraint("uq_doc_clinic_patient_sha", type_="unique")
        batch.create_unique_constraint("uq_doc_clinic_sha", ["clinic_id", "content_sha256"])
    op.drop_column("documents", "original_name")
    op.drop_column("documents", "storage_backend")
    op.drop_index("ix_patient_notes_clinic_patient_created", table_name="patient_notes")
    op.drop_table("patient_notes")
