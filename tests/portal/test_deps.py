"""Tests for /api/portal/* auth dependencies."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_whoami_returns_401_without_token():
    r = client.get("/api/portal/whoami")
    assert r.status_code == 401


def test_whoami_returns_user_when_override_installed(override_portal_user):
    override_portal_user(uid="u1", email="a@b.com", clinic_ids=["default"], role="admin")
    r = client.get("/api/portal/whoami")
    assert r.status_code == 200
    body = r.json()
    assert body["uid"] == "u1"
    assert body["clinic_ids"] == ["default"]
    assert body["role"] == "admin"
