"""provider_busy_blocks v2 columns: weekdays, specific_date, recurrence_until, label

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-05-26 22:00:00.000000

The model (database/models.py::ProviderBusyBlock) already references these
columns but no prior migration creates them. Production was patched manually
via raw ALTER TABLE during diagnosis; this migration is idempotent against
that patch (ADD COLUMN IF NOT EXISTS) and brings the schema definition
under alembic's tracking.

Postgres-only. SQLite test conftest creates the full schema via models, so
no SQLite path is needed.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "h2i3j4k5l6m7"
down_revision: Union[str, None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return  # SQLite path is no-op; models create the columns directly.

    # Idempotent against prior raw-SQL patch on prod AND fresh DBs.
    # ADD COLUMN IF NOT EXISTS is Postgres 9.6+; we're on 15.
    op.execute("ALTER TABLE provider_busy_blocks ALTER COLUMN weekday DROP NOT NULL")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS weekdays VARCHAR")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS specific_date DATE")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS recurrence_until DATE")
    op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS label VARCHAR")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_provider_busy_blocks_specific_date "
        "ON provider_busy_blocks (clinic_id, provider_id, specific_date) "
        "WHERE specific_date IS NOT NULL"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS ix_provider_busy_blocks_specific_date")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS label")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS recurrence_until")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS specific_date")
    op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS weekdays")
    op.execute("ALTER TABLE provider_busy_blocks ALTER COLUMN weekday SET NOT NULL")
