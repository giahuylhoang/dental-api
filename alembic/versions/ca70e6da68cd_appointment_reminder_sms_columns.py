"""appointment reminder sms columns

Revision ID: ca70e6da68cd
Revises: 62ae0bb107ad
Create Date: 2026-06-09 14:18:13.990208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca70e6da68cd'
down_revision: Union[str, Sequence[str], None] = '62ae0bb107ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("appointment_reminders") as batch:
        batch.add_column(sa.Column("provider", sa.String(), nullable=False, server_default="telnyx"))
        batch.add_column(sa.Column("outbound_message_id", sa.String(), nullable=True))
        batch.add_column(sa.Column("reply_received_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("reply_parsed_intent", sa.String(), nullable=True))
        batch.add_column(sa.Column("reply_raw_text", sa.Text(), nullable=True))
        batch.add_column(sa.Column("reschedule_token", sa.String(), nullable=True))
        batch.add_column(sa.Column("reschedule_token_used_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("reschedule_token_expires_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("ambiguous_reply_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_index(
        "ix_appointment_reminders_reschedule_token",
        "appointment_reminders",
        ["reschedule_token"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_appointment_reminders_reschedule_token", table_name="appointment_reminders")
    with op.batch_alter_table("appointment_reminders") as batch:
        for col in (
            "ambiguous_reply_count",
            "reschedule_token_expires_at",
            "reschedule_token_used_at",
            "reschedule_token",
            "reply_raw_text",
            "reply_parsed_intent",
            "reply_received_at",
            "outbound_message_id",
            "provider",
        ):
            batch.drop_column(col)
