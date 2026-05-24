"""clinic_config_v2: practice_types + clinic_routing + clinics overrides

Revision ID: g1h2i3j4k5l6
Revises: aa11bb22cc33
Create Date: 2026-05-24 02:00:00.000000

Notes on dialect handling:
  - ``clinic_routing`` uses ``TEXT[]`` arrays and ``JSONB`` with a GIN index,
    none of which SQLite supports. The table is created only on Postgres,
    matching the pattern in ``aa11bb22cc33_add_rag_tables.py`` (rag_docs).
  - ``practice_types`` uses portable ``sa.JSON`` columns and skips
    ``::jsonb`` casts so it can also be created on SQLite (handy for the
    SQLite alembic round-trip test in ``tests/track_auth``).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, Sequence[str], None] = 'aa11bb22cc33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Server defaults differ: Postgres can cast '[]'::jsonb, SQLite cannot.
    triage_default = sa.text("'[]'::jsonb") if is_pg else sa.text("'[]'")
    flags_default = sa.text("'{}'::jsonb") if is_pg else sa.text("'{}'")

    op.create_table(
        'practice_types',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('assistant_name', sa.String(), nullable=False),
        sa.Column('ai_disclosure_required', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('ai_disclosure_phrase', sa.Text(), nullable=False),
        sa.Column('greeting_message', sa.Text(), nullable=False),
        sa.Column('pricing_preface', sa.Text(), nullable=False),
        sa.Column('pricing_dentures_range', sa.Text(), nullable=True),
        sa.Column('treatment_steps_guardrail', sa.Text(), nullable=False),
        # sa.JSON (not JSONB) keeps practice_types compatible with both backends; these fields are never queried by content
        sa.Column('triage_questions', sa.JSON(), nullable=False, server_default=triage_default),
        sa.Column('default_feature_flags', sa.JSON(), nullable=False, server_default=flags_default),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    if is_pg:
        # clinic_routing uses pg-only types (TEXT[], JSONB, GIN). Skip on
        # other dialects so SQLite-based alembic round-trip tests stay green.
        # Production always uses Postgres; YamlRoutingStore is the SQLite
        # fallback that this table replaces in PG environments.
        op.create_table(
            'clinic_routing',
            sa.Column('clinic_id', sa.String(), primary_key=True),
            sa.Column('ring_timeout_seconds', sa.Integer(), nullable=False, server_default='20'),
            sa.Column('ai_after_hours', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('ai_in_hours_overflow', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('backup_number', sa.String(), nullable=True),
            sa.Column('ai_sip_uri', sa.String(), nullable=True),
            sa.Column('dids', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
            sa.Column('front_desk_numbers', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
            sa.Column('hours', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
        )
        op.create_index(
            'ix_clinic_routing_dids',
            'clinic_routing',
            ['dids'],
            postgresql_using='gin',
        )

    op.add_column('clinics', sa.Column('practice_type_id', sa.String(), nullable=True))
    op.add_column('clinics', sa.Column('knowledge_base_path', sa.String(), nullable=True))
    op.add_column('clinics', sa.Column('general_consultation_service_id', sa.Integer(), nullable=True))
    op.add_column(
        'clinics',
        sa.Column(
            'feature_flags_overrides',
            sa.JSON(),
            nullable=False,
            server_default=flags_default,
        ),
    )

    # SQLite cannot ALTER TABLE to add FK constraints (would need batch mode);
    # the rest of the codebase relies on Postgres in any real environment, so
    # we limit FK creation to PG. Note: this matches existing behaviour in
    # other migrations (e.g. add_rag_tables) that gate PG-only constructs.
    if is_pg:
        op.create_foreign_key(
            'fk_clinics_practice_type_id',
            'clinics', 'practice_types',
            ['practice_type_id'], ['id'],
        )
        op.create_foreign_key(
            'fk_clinics_general_consultation_service_id',
            'clinics', 'services',
            ['general_consultation_service_id'], ['id'],
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.drop_constraint('fk_clinics_general_consultation_service_id', 'clinics', type_='foreignkey')
        op.drop_constraint('fk_clinics_practice_type_id', 'clinics', type_='foreignkey')
    op.drop_column('clinics', 'feature_flags_overrides')
    op.drop_column('clinics', 'general_consultation_service_id')
    op.drop_column('clinics', 'knowledge_base_path')
    op.drop_column('clinics', 'practice_type_id')
    if is_pg:
        op.drop_index('ix_clinic_routing_dids', table_name='clinic_routing')
        op.drop_table('clinic_routing')
    op.drop_table('practice_types')
