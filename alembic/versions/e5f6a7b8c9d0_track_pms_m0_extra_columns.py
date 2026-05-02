"""track_pms_m0_extra_columns

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('chief_complaint', sa.Text(), nullable=True))
    op.add_column('treatment_plan_items', sa.Column('tooth_number', sa.Integer(), nullable=True))
    op.add_column('treatment_plan_items', sa.Column('care_notes', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('owner_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('leads', 'owner_id')
    op.drop_column('treatment_plan_items', 'care_notes')
    op.drop_column('treatment_plan_items', 'tooth_number')
    op.drop_column('appointments', 'chief_complaint')
