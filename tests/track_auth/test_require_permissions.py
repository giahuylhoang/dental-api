"""Tests: require_permissions — denies missing perm, admin permits all."""
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


def _make_user(session, email, perms, clinic_id=DEFAULT_CLINIC_ID):
    role = Role(name=f"role_{email}", clinic_id=None, permissions=perms)
    session.add(role)
    session.flush()
    user = User(
        clinic_id=clinic_id,
        email=email,
        password_hash=_hash("pw"),
        is_active=True,
    )
    session.add(user)
    session.flush()
    session.add(UserRole(user_id=user.id, role_id=role.id))
    session.commit()
    return user


@pytest.fixture()
def setup(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    session.add(Clinic(id=DEFAULT_CLINIC_ID, name="TC", timezone="UTC", working_hour_start=9, working_hour_end=17))
    session.flush()

    _make_user(session, "admin@t.com", ["*.*"])
    _make_user(session, "limited@t.com", ["patients.read"])

    def override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c, session
    app.dependency_overrides.clear()
    session.close()


def _token(c, email):
    resp = c.post("/api/v2/auth/login", json={"email": email, "password": "pw"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_admin_can_list_users(setup):
    c, session = setup
    token = _token(c, "admin@t.com")
    resp = c.get("/api/v2/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_limited_user_denied_users_list(setup):
    c, session = setup
    token = _token(c, "limited@t.com")
    resp = c.get("/api/v2/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_no_token_returns_401(setup):
    c, session = setup
    resp = c.get("/api/v2/admin/users")
    assert resp.status_code == 401


def test_admin_can_access_audit_log(setup):
    c, session = setup
    token = _token(c, "admin@t.com")
    resp = c.get("/api/v2/admin/audit-log", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
