"""Tests: Alembic migration up/down round-trip on SQLite."""
import os
import subprocess
import sys
import pytest


def _run(cmd, env):
    result = subprocess.run(
        cmd, env=env, capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    return result


@pytest.fixture()
def tmp_db(tmp_path):
    db_path = tmp_path / "test_migration.db"
    return f"sqlite:///{db_path}"


def test_alembic_upgrade_head(tmp_db):
    env = {**os.environ, "DATABASE_URL": tmp_db}
    result = _run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
    assert result.returncode == 0, f"upgrade failed:\n{result.stdout}\n{result.stderr}"


def test_alembic_downgrade_minus_one(tmp_db):
    env = {**os.environ, "DATABASE_URL": tmp_db}
    # First upgrade
    up = _run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
    assert up.returncode == 0, f"upgrade failed:\n{up.stdout}\n{up.stderr}"
    # Then downgrade one step
    down = _run([sys.executable, "-m", "alembic", "downgrade", "-1"], env)
    assert down.returncode == 0, f"downgrade failed:\n{down.stdout}\n{down.stderr}"


def test_alembic_full_round_trip(tmp_db):
    env = {**os.environ, "DATABASE_URL": tmp_db}
    up = _run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
    assert up.returncode == 0
    down = _run([sys.executable, "-m", "alembic", "downgrade", "base"], env)
    assert down.returncode == 0
    up2 = _run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
    assert up2.returncode == 0
