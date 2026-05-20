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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure all models are registered with Base before create_all
from database.connection import Base, get_db
from database.models import Clinic, DEFAULT_CLINIC_ID
import database.models  # noqa: F401

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


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh in-memory engine and tables per test."""
    engine = create_engine(
        SQLITE_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
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


@pytest.fixture(scope="function")
def client_market_mall(client, db_session):
    """Client with market-mall-denture clinic seeded (providers 101/102, busy blocks, service 700)."""
    seed_market_mall_denture(db_session)
    db_session.commit()
    yield client
