"""Tests: login flow — happy path, bad password, nonexistent user, lockout, locked user."""
import pytest
import bcrypt as _bcrypt
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID
from database.auth.models import User, Role, UserRole
from api.main import app


def _hash(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()


@pytest.fixture()
def setup(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()

    session.add(Clinic(id=DEFAULT_CLINIC_ID, name="TC", timezone="UTC", working_hour_start=9, working_hour_end=17))
    role = Role(name="admin", clinic_id=None, permissions=["*.*"])
    session.add(role)
    session.flush()
    user = User(
        clinic_id=DEFAULT_CLINIC_ID,
        email="user@test.com",
        password_hash=_hash("correct"),
        full_name="Test",
        is_active=True,
    )
    session.add(user)
    session.flush()
    session.add(UserRole(user_id=user.id, role_id=role.id))
    session.commit()

    def override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c, session, user
    app.dependency_overrides.clear()
    session.close()


def test_login_happy_path(setup):
    c, session, user = setup
    resp = c.post("/api/v2/auth/login", json={"email": "user@test.com", "password": "correct"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "user@test.com"


def test_login_bad_password(setup):
    c, session, user = setup
    resp = c.post("/api/v2/auth/login", json={"email": "user@test.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_nonexistent_user(setup):
    c, session, user = setup
    resp = c.post("/api/v2/auth/login", json={"email": "nobody@test.com", "password": "x"})
    assert resp.status_code == 401


def test_lockout_after_5_fails(setup):
    c, session, user = setup
    for _ in range(5):
        resp = c.post("/api/v2/auth/login", json={"email": "user@test.com", "password": "wrong"})
        assert resp.status_code == 401

    # 6th attempt — account should be locked
    resp = c.post("/api/v2/auth/login", json={"email": "user@test.com", "password": "wrong"})
    assert resp.status_code == 403

    session.refresh(user)
    assert user.locked_at is not None


def test_locked_user_correct_password(setup):
    c, session, user = setup
    # Lock the user first
    for _ in range(5):
        c.post("/api/v2/auth/login", json={"email": "user@test.com", "password": "wrong"})

    # Even correct password returns 403
    resp = c.post("/api/v2/auth/login", json={"email": "user@test.com", "password": "correct"})
    assert resp.status_code == 403
