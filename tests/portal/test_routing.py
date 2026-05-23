"""Tests for /api/portal/clinics/{cid}/routing."""

from fastapi.testclient import TestClient
import pytest

from api.main import app
from database.connection import get_db
from database.models import Clinic, DEFAULT_CLINIC_ID

client = TestClient(app)


@pytest.fixture(autouse=True)
def _seed_default_clinic(db_session):
    """Ensure a clinic exists for FK constraints AND route get_db to the in-memory session."""
    if not db_session.query(Clinic).filter_by(id=DEFAULT_CLINIC_ID).first():
        db_session.add(Clinic(id=DEFAULT_CLINIC_ID, name="Default"))
        db_session.commit()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


def test_get_routing_empty_returns_default(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get("/api/portal/clinics/default/routing")
    assert r.status_code == 200
    assert r.json() == {"rules": {}}


def test_put_routing_persists(override_portal_user):
    override_portal_user(clinic_ids=["default"], email="admin@x.com")
    body = {"rules": {"after_hours": "voicemail", "default_provider": "p1"}}
    r = client.put("/api/portal/clinics/default/routing", json=body)
    assert r.status_code == 200
    r2 = client.get("/api/portal/clinics/default/routing")
    assert r2.json()["rules"] == body["rules"]


def test_cross_clinic_blocked(override_portal_user):
    override_portal_user(clinic_ids=["clinic_a"])
    r = client.get("/api/portal/clinics/clinic_b/routing")
    assert r.status_code == 403


def test_preview_pure_function(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.post(
        "/api/portal/clinics/default/routing/preview",
        json={"rules": {"default_provider": "p1"}, "context": {"hour": 14}},
    )
    assert r.status_code == 200
    assert "decision" in r.json()
