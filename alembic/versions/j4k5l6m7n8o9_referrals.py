"""referrals + referral_documents

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8, 493cc648b838
Create Date: 2026-06-19 00:00:00.000000

Phase 1 of the public referral form. Additive only:
- new `referrals` and `referral_documents` tables
The shared `documents` table is intentionally NOT touched. The clinic info@
recipient is configured via the CLINIC_INFO_EMAIL env var (no schema change).

This revision also MERGES the two pre-existing Alembic heads
(`i3j4k5l6m7n8` user_clinic_memberships and `493cc648b838` clinic_sms_from_number)
back into a single head so `alembic upgrade head` is unambiguous.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j4k5l6m7n8o9"
down_revision: Union[str, Sequence[str], None] = ("i3j4k5l6m7n8", "493cc648b838")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = sa.Enum(
    "NEW", "READY", "IN_REVIEW", "CONVERTED", "ARCHIVED", name="referralstatus"
)


def upgrade() -> None:
    op.create_table(
        "referrals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("patient_name", sa.String(), nullable=False),
        sa.Column("patient_phone", sa.String(), nullable=False),
        sa.Column("referred_by", sa.String(), nullable=False),
        sa.Column("referrer_contact", sa.String(), nullable=True),
        sa.Column("proposed_extraction_date", sa.Date(), nullable=True),
        sa.Column("tx_plan", sa.Text(), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("status", _STATUS, nullable=False, server_default="NEW"),
        sa.Column("patient_id", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="public-referral"),
        sa.Column("submit_ip", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_referrals_clinic_status_created",
        "referrals",
        ["clinic_id", "status", "created_at"],
    )

    op.create_table(
        "referral_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("referral_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False, server_default="xray"),
        sa.Column("storage_url", sa.Text(), nullable=False),
        sa.Column("storage_backend", sa.String(), nullable=False, server_default="gcs"),
        sa.Column("mime", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(), nullable=True),
        sa.Column("original_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["referral_id"], ["referrals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_referral_documents_referral",
        "referral_documents",
        ["clinic_id", "referral_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_referral_documents_referral", table_name="referral_documents")
    op.drop_table("referral_documents")
    op.drop_index("ix_referrals_clinic_status_created", table_name="referrals")
    op.drop_table("referrals")
    _STATUS.drop(op.get_bind(), checkfirst=True)
