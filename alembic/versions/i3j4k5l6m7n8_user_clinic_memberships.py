"""user_clinic_memberships

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2026-05-28 00:00:00.000000

Adds the user_clinic_memberships join table that powers Firebase-token
authorization. Additive only; no existing rows touched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i3j4k5l6m7n8"
down_revision: Union[str, Sequence[str], None] = "h2i3j4k5l6m7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_clinic_memberships",
        sa.Column("uid", sa.String(length=128), nullable=False),
        sa.Column("clinic_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"], ["clinics.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("uid", "clinic_id", name="pk_user_clinic_memberships"),
    )
    op.create_index(
        "idx_memberships_uid", "user_clinic_memberships", ["uid"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_memberships_uid", table_name="user_clinic_memberships")
    op.drop_table("user_clinic_memberships")
