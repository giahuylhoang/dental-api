"""add hold fields to appointments

Revision ID: bf6bca8a4d1e
Revises: i3j4k5l6m7n8
Create Date: 2026-06-08 17:12:31.258421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf6bca8a4d1e'
down_revision: Union[str, Sequence[str], None] = 'i3j4k5l6m7n8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("hold_expiry_at", sa.DateTime(), nullable=True))
    op.add_column("appointments", sa.Column("patient_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("appointments", sa.Column("source", sa.String(), nullable=True))
    op.create_index("ix_appointments_clinic_hold_expiry", "appointments", ["clinic_id", "hold_expiry_at"])


def downgrade() -> None:
    op.drop_index("ix_appointments_clinic_hold_expiry", table_name="appointments")
    op.drop_column("appointments", "source")
    op.drop_column("appointments", "patient_confirmed")
    op.drop_column("appointments", "hold_expiry_at")
