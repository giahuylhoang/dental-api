"""
Pytest fixtures: in-memory SQLite DB and FastAPI TestClient.

Overrides get_db so all API calls use the test DB (no readonly file DB).
"""
import os

# Notification env hygiene MUST happen before importing api.main / clients.*,
# because SMS_DELAY_SECONDS and similar are captured into module-level constants
# at first import. Strip leaky values from .env.local that pollute test runs.
for _var in (
    "BOOKING_NOTIFICATION_TO",
    "SMS_DELAY_SECONDS",
    "SMTP_DEPLOY_VERIFY_TO",
):
    os.environ.pop(_var, None)
os.environ["SEND_BOOKING_SMS"] = "false"
os.environ["SEND_CLINIC_BOOKING_EMAIL"] = "false"

# All tests run with auth disabled by default. Tests that exercise the
# auth gate set ADMIN_AUTH_BYPASS=false via monkeypatch and provide a
# token or mock verify_id_token.
os.environ["ADMIN_AUTH_BYPASS"] = "true"

import sqlalchemy as _sa
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure all models are registered with Base before create_all
from database.connection import Base, get_db
from database.models import Clinic, DEFAULT_CLINIC_ID
import database.models  # noqa: F401
import database.auth  # noqa: F401  -- registers UserClinicMembership with Base

from api.main import app
from scripts.init_database import seed_market_mall_denture
import clients.sms_client as _sms_client
import clients.email_client as _email_client

# Belt-and-suspenders: even if .env.local was already loaded by an earlier
# import path (e.g. database.connection.load_dotenv), zero out the delay constants.
_sms_client.SMS_DELAY_SECONDS = 0
_sms_client.SEND_BOOKING_SMS = False
_email_client.SEND_CLINIC_BOOKING_EMAIL = False

SQLITE_TEST_URL = "sqlite:///:memory:"


# Strip env vars that leak from .env.local into the test process and break
# determinism — tests must control these themselves via monkeypatch.
_LEAKY_ENV_VARS = (
    "BOOKING_NOTIFICATION_TO",
    "SMS_DELAY_SECONDS",
    "SMTP_DEPLOY_VERIFY_TO",
)


@pytest.fixture(autouse=True)
def _isolate_notification_env(monkeypatch):
    for var in _LEAKY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SEND_BOOKING_SMS", "false")
    monkeypatch.setenv("SEND_CLINIC_BOOKING_EMAIL", "false")
    # Re-zero module constants in case a test mutated them.
    monkeypatch.setattr(_sms_client, "SMS_DELAY_SECONDS", 0)
    monkeypatch.setattr(_sms_client, "SEND_BOOKING_SMS", False)
    monkeypatch.setattr(_email_client, "SEND_CLINIC_BOOKING_EMAIL", False)
    monkeypatch.setenv("ADMIN_AUTH_BYPASS", "true")
    monkeypatch.setattr("api.dependencies.auth.ADMIN_AUTH_BYPASS", True)


# Tables whose column types (e.g. pgvector.Vector, PG JSONB) cannot compile on
# SQLite. RAG features are exercised by the `pg_engine`/`pg_db_session`/`pg_client`
# fixtures, which run against the real Postgres + pgvector. Keep this set tight.
_SQLITE_SKIP_TABLES = {"rag_docs", "clinic_routing"}


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh in-memory engine and tables per test."""
    engine = create_engine(
        SQLITE_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sqlite_tables = [
        t for t in Base.metadata.sorted_tables if t.name not in _SQLITE_SKIP_TABLES
    ]
    Base.metadata.create_all(bind=engine, tables=sqlite_tables)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a DB session for the test (for direct DB access in tests if needed)."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """FastAPI TestClient with get_db overridden to use in-memory SQLite."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()

    # Seed default clinic (required for tenant-scoped endpoints)
    if session.query(Clinic).filter(Clinic.id == DEFAULT_CLINIC_ID).first() is None:
        session.add(
            Clinic(
                id=DEFAULT_CLINIC_ID,
                name="Default Clinic",
                timezone="America/Edmonton",
                working_hour_start=9,
                working_hour_end=17,
            )
        )
        session.commit()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        session.close()


@pytest.fixture
def seed_clinic_via_session(db_engine):
    """Return a callable that seeds the test DB via a short-lived session.

    The client fixture overrides get_db with a session bound to the same
    StaticPool engine, so commits here are visible to subsequent client requests.
    """
    def _seed(fn):
        S = sessionmaker(bind=db_engine)
        s = S()
        fn(s)
        s.close()
    return _seed


@pytest.fixture(scope="function")
def client_market_mall(client, db_session):
    """Client with market-mall-denture clinic seeded (providers 101/102, busy blocks, service 700)."""
    seed_market_mall_denture(db_session)
    db_session.commit()
    yield client


def pytest_configure(config):
    config.addinivalue_line("markers", "pgvector: requires Postgres + pgvector running")
    config.addinivalue_line("markers", "postgres: requires Postgres running")


# ----- pgvector test fixtures -------------------------------------------------
# `import sqlalchemy as _sa` is at the top of this file.

PG_TEST_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:dev@localhost:5433/dental_test",
)


def _pg_available() -> bool:
    eng = None
    try:
        eng = _sa.create_engine(PG_TEST_URL, pool_pre_ping=True)
        with eng.connect() as c:
            c.execute(_sa.text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        if eng is not None:
            eng.dispose()


_PG_OK = _pg_available()


@pytest.fixture(scope="session")
def pg_engine():
    """Postgres + pgvector engine; tables created from Base.metadata at session start."""
    if not _PG_OK:
        pytest.skip(f"Postgres unavailable at {PG_TEST_URL}")
    engine = _sa.create_engine(PG_TEST_URL, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(_sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        import database.models  # noqa: F401
        import database.ops.rag  # noqa: F401
        Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="function")
def pg_db_session(pg_engine):
    """Per-test transactional session — rolled back at end so tests are hermetic."""
    from database.models import Clinic
    connection = pg_engine.connect()
    try:
        trans = connection.begin()
        Session = sessionmaker(bind=connection, autoflush=False, autocommit=False)
        session = Session()
        # Seed a test clinic so FK constraints on clinic_id="t_clinic" pass.
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


@pytest.fixture(scope="function")
def pg_client(pg_db_session):
    """FastAPI TestClient with get_db overridden to use the pg_db_session."""
    def _override():
        yield pg_db_session

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
