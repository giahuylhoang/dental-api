"""Migration test for practice_types, clinic_routing, and clinics columns.

Runs the alembic upgrade against a fresh Postgres DB, asserts the expected
schema, runs the downgrade, asserts the schema is restored. Skips when
Postgres is unavailable (alembic + array/jsonb need a real PG).

Implementation note: ``alembic/env.py`` resolves ``sqlalchemy.url`` from
``database.connection.DATABASE_URL`` (computed at import time from env vars),
so we shell out to ``python -m alembic`` in a child process with
``DATABASE_URL`` set — the same pattern as ``tests/track_auth/test_alembic_migration.py``.
This keeps test isolation: we don't mutate the parent process's
``database.connection`` module, which would corrupt other tests' engines.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa


pytestmark = pytest.mark.postgres  # marker for "needs Postgres" (no pgvector required)


REPO_ROOT = Path(__file__).resolve().parents[1]
PG_TEST_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:dev@localhost:5433/dental_test",
)


def _pg_available(url: str) -> bool:
    eng = None
    try:
        eng = sa.create_engine(url, pool_pre_ping=True)
        with eng.connect() as c:
            c.execute(sa.text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        if eng is not None:
            eng.dispose()


def _alembic(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run ``python -m alembic <cmd>`` with ``DATABASE_URL`` pointed at the test PG."""
    env = {**os.environ, "DATABASE_URL": PG_TEST_URL}
    # Clear higher-precedence env vars from database/connection.py.
    for var in ("POSTGRES_URL", "POSTGRES_PRISMA_URL", "POSTGRES_URL_NON_POOLING"):
        env.pop(var, None)
    return subprocess.run(
        [sys.executable, "-m", "alembic", *cmd],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


@pytest.fixture
def pg_engine():
    if not _pg_available(PG_TEST_URL):
        pytest.skip(f"Postgres unavailable at {PG_TEST_URL}")
    eng = sa.create_engine(PG_TEST_URL)
    # Ensure we start each test at the previous revision so upgrade is a real op.
    with eng.connect() as conn:
        row = conn.execute(sa.text(
            "SELECT version_num FROM alembic_version LIMIT 1"
        )).fetchone()
        current = row[0] if row else None
    if current == "g1h2i3j4k5l6":
        down = _alembic(["downgrade", "-1"])
        assert down.returncode == 0, f"setup downgrade failed:\n{down.stdout}\n{down.stderr}"
    try:
        yield eng
    finally:
        eng.dispose()


def test_upgrade_creates_practice_types(pg_engine):
    up = _alembic(["upgrade", "g1h2i3j4k5l6"])
    assert up.returncode == 0, f"upgrade failed:\n{up.stdout}\n{up.stderr}"
    insp = sa.inspect(pg_engine)
    assert "practice_types" in insp.get_table_names()
    cols = {c["name"] for c in insp.get_columns("practice_types")}
    assert {"id", "assistant_name", "ai_disclosure_required",
            "ai_disclosure_phrase", "greeting_message", "pricing_preface",
            "pricing_dentures_range", "treatment_steps_guardrail",
            "triage_questions", "default_feature_flags"} <= cols


def test_upgrade_creates_clinic_routing(pg_engine):
    up = _alembic(["upgrade", "g1h2i3j4k5l6"])
    assert up.returncode == 0, f"upgrade failed:\n{up.stdout}\n{up.stderr}"
    insp = sa.inspect(pg_engine)
    assert "clinic_routing" in insp.get_table_names()
    indexes = {i["name"] for i in insp.get_indexes("clinic_routing")}
    assert "ix_clinic_routing_dids" in indexes

    # The whole rationale for this table being Postgres-only is the column
    # types (TEXT[], JSONB-with-GIN). Asserting presence alone would let a
    # future refactor silently downgrade them to TEXT/JSON.
    cols_by_name = {c["name"]: c for c in insp.get_columns("clinic_routing")}
    dids_type = repr(cols_by_name["dids"]["type"]).upper()
    assert "ARRAY" in dids_type, f"dids should be TEXT[], got {dids_type}"
    fdn_type = repr(cols_by_name["front_desk_numbers"]["type"]).upper()
    assert "ARRAY" in fdn_type, f"front_desk_numbers should be TEXT[], got {fdn_type}"
    hours_type = repr(cols_by_name["hours"]["type"]).upper()
    assert "JSONB" in hours_type, f"hours should be JSONB, got {hours_type}"


def test_upgrade_adds_clinics_columns(pg_engine):
    up = _alembic(["upgrade", "g1h2i3j4k5l6"])
    assert up.returncode == 0, f"upgrade failed:\n{up.stdout}\n{up.stderr}"
    insp = sa.inspect(pg_engine)
    cols = {c["name"] for c in insp.get_columns("clinics")}
    assert {"practice_type_id", "knowledge_base_path",
            "general_consultation_service_id",
            "feature_flags_overrides"} <= cols


def test_downgrade_restores_schema(pg_engine):
    up = _alembic(["upgrade", "g1h2i3j4k5l6"])
    assert up.returncode == 0, f"upgrade failed:\n{up.stdout}\n{up.stderr}"
    down = _alembic(["downgrade", "-1"])
    assert down.returncode == 0, f"downgrade failed:\n{down.stdout}\n{down.stderr}"
    insp = sa.inspect(pg_engine)
    assert "practice_types" not in insp.get_table_names()
    assert "clinic_routing" not in insp.get_table_names()
    cols = {c["name"] for c in insp.get_columns("clinics")}
    assert "practice_type_id" not in cols
    assert "feature_flags_overrides" not in cols


def test_upgrade_and_downgrade_lifecycle_for_fks(pg_engine):
    """FKs from clinics → practice_types and clinics → services are created on
    upgrade and dropped on downgrade. Without this, a future refactor could
    quietly stop creating the FKs and the columns-restored test would still
    pass (dropping the columns cascades the FK drop)."""
    up = _alembic(["upgrade", "g1h2i3j4k5l6"])
    assert up.returncode == 0, f"upgrade failed:\n{up.stdout}\n{up.stderr}"
    insp = sa.inspect(pg_engine)
    fk_names = {fk["name"] for fk in insp.get_foreign_keys("clinics")}
    assert "fk_clinics_practice_type_id" in fk_names
    assert "fk_clinics_general_consultation_service_id" in fk_names

    down = _alembic(["downgrade", "-1"])
    assert down.returncode == 0, f"downgrade failed:\n{down.stdout}\n{down.stderr}"
    insp = sa.inspect(pg_engine)
    fk_names = {fk["name"] for fk in insp.get_foreign_keys("clinics")}
    assert "fk_clinics_practice_type_id" not in fk_names
    assert "fk_clinics_general_consultation_service_id" not in fk_names


@pytest.fixture
def pg_session_at_head():
    """Per-test transactional session pinned to the current alembic head.

    The local ``pg_engine`` fixture above downgrades to the prior revision in
    setup so the migration-level tests get a real upgrade to assert on. That
    same shadowing means the conftest ``pg_db_session`` fixture (which depends
    on a ``pg_engine`` name) resolves to the *local* downgrading fixture in
    this file — leaving the schema without ``practice_types`` /
    ``clinic_routing`` for any ORM-level test. To keep model-level tests
    independent of migration ordering, build our own engine + session here
    and force an alembic upgrade first.
    """
    if not _pg_available(PG_TEST_URL):
        pytest.skip(f"Postgres unavailable at {PG_TEST_URL}")
    up = _alembic(["upgrade", "g1h2i3j4k5l6"])
    assert up.returncode == 0, f"setup upgrade failed:\n{up.stdout}\n{up.stderr}"

    from sqlalchemy.orm import sessionmaker
    from database.models import Clinic

    engine = sa.create_engine(PG_TEST_URL, pool_pre_ping=True)
    connection = engine.connect()
    try:
        trans = connection.begin()
        Session = sessionmaker(bind=connection, autoflush=False, autocommit=False)
        session = Session()
        # Seed the test clinic so the FK on clinic_routing.clinic_id is satisfied.
        if session.query(Clinic).filter(Clinic.id == "t_clinic").first() is None:
            session.add(Clinic(id="t_clinic", name="Test Clinic"))
            session.flush()
        try:
            yield session
        finally:
            session.close()
            trans.rollback()
    finally:
        connection.close()
        engine.dispose()


def test_models_can_insert_practice_type(pg_session_at_head):
    """Inserting via the ORM should round-trip all columns including JSON."""
    from database.models import PracticeType
    pt = PracticeType(
        id='denturist',
        assistant_name='Emma',
        ai_disclosure_required=True,
        ai_disclosure_phrase="I'm a virtual receptionist",
        greeting_message='hello',
        pricing_preface='preface',
        pricing_dentures_range='1700-2200',
        treatment_steps_guardrail='guardrail',
        triage_questions=['q1', 'q2', 'q3'],
        default_feature_flags={'sms_notifications': True},
    )
    pg_session_at_head.add(pt)
    pg_session_at_head.flush()
    fetched = pg_session_at_head.query(PracticeType).filter_by(id='denturist').one()
    assert fetched.triage_questions == ['q1', 'q2', 'q3']
    assert fetched.default_feature_flags == {'sms_notifications': True}


def test_models_can_insert_clinic_routing(pg_session_at_head):
    from database.models import ClinicRouting
    pg_session_at_head.add(ClinicRouting(
        clinic_id='t_clinic',
        ring_timeout_seconds=18,
        ai_after_hours=False,
        ai_in_hours_overflow=True,
        backup_number='+15871234567',
        ai_sip_uri='sip:test@example.com',
        dids=['+15871234567', '+15879999999'],
        front_desk_numbers=['+15871112222'],
        hours={'mon': {'open': '09:00', 'close': '17:00'}},
    ))
    pg_session_at_head.flush()
    fetched = pg_session_at_head.query(ClinicRouting).filter_by(clinic_id='t_clinic').one()
    assert fetched.dids == ['+15871234567', '+15879999999']
    assert fetched.hours == {'mon': {'open': '09:00', 'close': '17:00'}}
