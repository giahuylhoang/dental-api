"""Tests: refresh token rotation, old token rejection, expired token rejection."""
from datetime import datetime, timedelta
import hashlib

import pytest
import bcrypt as _bcrypt
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID
from database.auth.models import User, Role, UserRole, RefreshToken
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
        email="u@test.com",
        password_hash=_hash("pw"),
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


def _login(c):
    resp = c.post("/api/v2/auth/login", json={"email": "u@test.com", "password": "pw"})
    assert resp.status_code == 200
    return resp.json()["refresh_token"]


def test_refresh_rotates_token(setup):
    c, session, user = setup
    rt1 = _login(c)
    resp = c.post("/api/v2/auth/refresh", json={"refresh_token": rt1})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    rt2 = data["refresh_token"]
    assert rt2 != rt1


def test_old_refresh_rejected_after_rotation(setup):
    c, session, user = setup
    rt1 = _login(c)
    c.post("/api/v2/auth/refresh", json={"refresh_token": rt1})
    # Old token should now be revoked
    resp = c.post("/api/v2/auth/refresh", json={"refresh_token": rt1})
    assert resp.status_code == 401


def test_expired_refresh_rejected(setup):
    c, session, user = setup
    rt_str = _login(c)
    # Manually expire the token in DB
    token_hash = hashlib.sha256(rt_str.encode()).hexdigest()
    rt = session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    rt.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.commit()

    resp = c.post("/api/v2/auth/refresh", json={"refresh_token": rt_str})
    assert resp.status_code == 401
