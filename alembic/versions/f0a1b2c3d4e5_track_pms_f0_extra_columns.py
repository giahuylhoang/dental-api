"""track_pms_f0_extra_columns

Revision ID: f0a1b2c3d4e5
Revises: e5f6a7b8c9d0
Create Date: 2026-05-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f0a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # lab_cases additions
    op.add_column('lab_cases', sa.Column('case_number', sa.Text(), nullable=True))
    op.add_column('lab_cases', sa.Column('treatment_plan_id', sa.String(), nullable=True))
    try:
        op.create_unique_constraint('uq_lab_cases_case_number', 'lab_cases', ['case_number'])
    except Exception:
        pass  # SQLite may not support named constraints cleanly

    # communications additions
    op.add_column('communications', sa.Column('thread_key', sa.Text(), nullable=True))
    op.add_column('communications', sa.Column('read_at', sa.DateTime(), nullable=True))
    op.add_column('communications', sa.Column('attachments', sa.JSON(), nullable=True))
    try:
        op.create_index('ix_communications_thread_key', 'communications', ['thread_key'])
    except Exception:
        pass

    # clinics additions
    op.add_column('clinics', sa.Column('display_name', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('clinics', 'display_name')
    try:
        op.drop_index('ix_communications_thread_key', table_name='communications')
    except Exception:
        pass
    op.drop_column('communications', 'attachments')
    op.drop_column('communications', 'read_at')
    op.drop_column('communications', 'thread_key')
    try:
        op.drop_constraint('uq_lab_cases_case_number', 'lab_cases', type_='unique')
    except Exception:
        pass
    op.drop_column('lab_cases', 'treatment_plan_id')
    op.drop_column('lab_cases', 'case_number')
