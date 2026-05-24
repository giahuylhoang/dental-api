"""portal_schema

Revision ID: 09a9594d0261
Revises: f0a1b2c3d4e5
Create Date: 2026-05-23 15:58:57.517749

Portal/CRM schema delta:
- Adds CRM columns to ``patients`` (lead_status_crm, crm_tags, crm_notes,
  last_contact_at). All nullable / server-defaulted so the v1 agent contract
  (POST /api/patients) is unaffected.
- Adds ``greeting`` JSONB to ``clinics`` for per-clinic agent greeting config.
- Creates ``clinic_routing_rules`` (one row per clinic) for per-clinic agent
  routing config edited from the portal.
- Creates ``call_logs`` for per-call records written by the agent shutdown hook
  and read by the portal Calls/Dashboard pages.

JSON columns use ``sa.JSON`` so they apply cleanly on SQLite (tests) and
Postgres (prod). The ORM models map them to ``JSON().with_variant(JSONB,
"postgresql")`` so prod storage is JSONB.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09a9594d0261'
down_revision: Union[str, Sequence[str], None] = 'f0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # patients: CRM columns (additive, nullable / server-defaulted)
    op.add_column(
        "patients",
        sa.Column("lead_status_crm", sa.String(), nullable=True),
    )
    op.add_column(
        "patients",
        sa.Column("crm_tags", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "patients",
        sa.Column("crm_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "patients",
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
    )

    # clinics: greeting JSONB (default empty object)
    op.add_column(
        "clinics",
        sa.Column("greeting", sa.JSON(), nullable=False, server_default="{}"),
    )

    # clinic_routing_rules: one row per clinic
    op.create_table(
        "clinic_routing_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", name="uq_clinic_routing_rules_clinic_id"),
    )

    # call_logs: per-call records
    op.create_table(
        "call_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("caller_phone", sa.String(), nullable=True),
        sa.Column("patient_id", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("transcript", sa.JSON(), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("call_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "call_logs_clinic_started_idx",
        "call_logs",
        ["clinic_id", "started_at"],
    )
    op.create_index(
        "call_logs_caller_started_idx",
        "call_logs",
        ["caller_phone", "started_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("call_logs_caller_started_idx", table_name="call_logs")
    op.drop_index("call_logs_clinic_started_idx", table_name="call_logs")
    op.drop_table("call_logs")

    op.drop_table("clinic_routing_rules")

    op.drop_column("clinics", "greeting")

    op.drop_column("patients", "last_contact_at")
    op.drop_column("patients", "crm_notes")
    op.drop_column("patients", "crm_tags")
    op.drop_column("patients", "lead_status_crm")
