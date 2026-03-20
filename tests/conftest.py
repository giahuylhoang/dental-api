"""
Pytest fixtures: in-memory SQLite DB and FastAPI TestClient.

Overrides get_db so all API calls use the test DB (no readonly file DB).
"""
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

SQLITE_TEST_URL = "sqlite:///:memory:"


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
