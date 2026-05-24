"""Tests for /api/portal/clinics/{cid}/routing."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


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
