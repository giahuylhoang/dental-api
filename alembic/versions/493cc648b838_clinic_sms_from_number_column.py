"""clinic sms from number column

Revision ID: 493cc648b838
Revises: ca70e6da68cd
Create Date: 2026-06-09 15:14:53.963333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '493cc648b838'
down_revision: Union[str, Sequence[str], None] = 'ca70e6da68cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("clinics") as batch:
        batch.add_column(sa.Column("sms_from_number", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("clinics") as batch:
        batch.drop_column("sms_from_number")
