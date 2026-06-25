"""Guard tests for database/connection.py engine pool configuration.

Pins the 2026-06-19 incident fix: Postgres engines must use pool_timeout=10 so a
stalled checkout fails fast (well under the ~120s request timeout that produced
the silent CRM spinner) instead of hanging on the 30s SQLAlchemy default.
"""

from database.connection import build_engine_kwargs


def test_postgres_engine_sets_pool_timeout_10():
    kwargs = build_engine_kwargs("postgresql://u:p@host/db")
    assert kwargs["pool_timeout"] == 10
    # Pool sizing deliberately small to respect Postgres max_connections during
    # a two-revision Cloud Run rollover — must not regress.
    assert kwargs["pool_size"] == 5
    assert kwargs["max_overflow"] == 10
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_recycle"] == 1800


def test_sqlite_engine_has_no_pool_timeout():
    kwargs = build_engine_kwargs("sqlite:////tmp/dental_clinic.db")
    assert "pool_timeout" not in kwargs
    assert kwargs["connect_args"] == {"check_same_thread": False}
