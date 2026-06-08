"""add clinic_holidays

Revision ID: 62ae0bb107ad
Revises: bf6bca8a4d1e
Create Date: 2026-06-08 17:14:45.752004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62ae0bb107ad'
down_revision: Union[str, Sequence[str], None] = 'bf6bca8a4d1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clinic_holidays",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("holiday_date", sa.Date(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.UniqueConstraint("clinic_id", "holiday_date", name="uq_clinic_holiday"),
    )


def downgrade() -> None:
    op.drop_table("clinic_holidays")
