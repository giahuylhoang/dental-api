"""Fixtures for track_clinical tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, get_db
from database.models import Clinic, Patient, DEFAULT_CLINIC_ID
import database.models  # noqa
import database.clinical.models  # noqa

from api.main import app


SQLITE_URL = "sqlite:///:memory:"


# Tables whose column types (e.g. pgvector.Vector, PG JSONB) cannot compile on
# SQLite. RAG features are exercised by the `pg_engine`/`pg_db_session`/`pg_client`
# fixtures, which run against the real Postgres + pgvector. Keep this set tight.
_SQLITE_SKIP_TABLES = {"rag_docs", "clinic_routing"}


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    sqlite_tables = [
        t for t in Base.metadata.sorted_tables if t.name not in _SQLITE_SKIP_TABLES
    ]
    Base.metadata.create_all(bind=engine, tables=sqlite_tables)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _make_client(db_engine, clinic_id=DEFAULT_CLINIC_ID, clinic_name="Test Clinic"):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    if session.query(Clinic).filter(Clinic.id == clinic_id).first() is None:
        session.add(Clinic(id=clinic_id, name=clinic_name, timezone="America/Edmonton",
                           working_hour_start=9, working_hour_end=17))
        session.commit()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, session


@pytest.fixture(scope="function")
def client_clinical(db_engine):
    c, session = _make_client(db_engine)
    yield c
    app.dependency_overrides.clear()
    session.close()


@pytest.fixture(scope="function")
def client_market_mall(db_engine):
    """Client with market-mall-denture clinic."""
    c, session = _make_client(db_engine, "market-mall-denture", "Market Mall Denture")
    yield c
    app.dependency_overrides.clear()
    session.close()


@pytest.fixture(scope="function")
def client_other_clinic(db_engine):
    """Client for a second clinic (clinic-other)."""
    c, session = _make_client(db_engine, "clinic-other", "Other Clinic")
    yield c
    app.dependency_overrides.clear()
    session.close()


def make_patient(client, clinic_id=DEFAULT_CLINIC_ID, name="Test Patient"):
    r = client.post("/api/patients", json={"first_name": name, "last_name": "User"},
                    headers={"X-Clinic-Id": clinic_id})
    assert r.status_code == 200, r.text
    return r.json()["id"]
