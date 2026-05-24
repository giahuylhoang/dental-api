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
