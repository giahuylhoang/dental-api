"""Shared fixtures for track_auth tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import bcrypt as _bcrypt

from database.connection import Base, get_db
from database.models import Clinic, DEFAULT_CLINIC_ID
import database.models  # noqa: F401
import database.auth  # noqa: F401

from database.auth.models import User, Role, UserRole
from api.main import app

SQLITE_URL = "sqlite:///:memory:"
TEST_JWT_SECRET = "test-secret-key-that-is-long-enough-32chars"


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


@pytest.fixture(autouse=True)
def pin_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_JWT_SECRET)
    import api.v2.auth.dependencies as deps
    if hasattr(deps.get_jwt_secret, "_dev_secret"):
        del deps.get_jwt_secret._dev_secret


@pytest.fixture()
def db_engine():
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _seed_clinic_and_admin(session):
    """Create default clinic + admin role + admin user. Returns (user, role)."""
    if session.query(Clinic).filter(Clinic.id == DEFAULT_CLINIC_ID).first() is None:
        session.add(Clinic(
            id=DEFAULT_CLINIC_ID, name="Test Clinic",
            timezone="America/Edmonton", working_hour_start=9, working_hour_end=17,
        ))
        session.flush()

    role = session.query(Role).filter(Role.name == "admin").first()
    if role is None:
        role = Role(name="admin", clinic_id=None, permissions=["*.*"])
        session.add(role)
        session.flush()

    user = session.query(User).filter(User.email == "admin@test.com").first()
    if user is None:
        user = User(
            clinic_id=DEFAULT_CLINIC_ID,
            email="admin@test.com",
            password_hash=_hash_password("password123"),
            full_name="Test Admin",
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.add(UserRole(user_id=user.id, role_id=role.id))

    session.commit()
    return user, role


@pytest.fixture()
def auth_client(db_engine):
    """TestClient with admin user pre-seeded; returns (client, session)."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    _seed_clinic_and_admin(session)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            resp = c.post("/api/v2/auth/login", json={"email": "admin@test.com", "password": "password123"})
            assert resp.status_code == 200, resp.text
            token = resp.json()["access_token"]
            c.headers.update({"Authorization": f"Bearer {token}"})
            yield c, session
    finally:
        app.dependency_overrides.clear()
        session.close()
