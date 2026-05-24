"""Tests for /api/portal/clinics/{cid}/greeting."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_get_greeting_default_empty(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get("/api/portal/clinics/default/greeting")
    assert r.status_code == 200
    assert r.json() == {"greeting": {}}


def test_put_greeting_persists(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    body = {"greeting": {"text": "Hi from Market Mall", "voice_id": "v1"}}
    r = client.put("/api/portal/clinics/default/greeting", json=body)
    assert r.status_code == 200
    assert r.json()["greeting"]["text"] == "Hi from Market Mall"

    r2 = client.get("/api/portal/clinics/default/greeting")
    assert r2.json()["greeting"]["text"] == "Hi from Market Mall"


def test_get_greeting_404_for_unknown_clinic(override_portal_user):
    override_portal_user(clinic_ids=["unknown_clinic"])
    r = client.get("/api/portal/clinics/unknown_clinic/greeting")
    assert r.status_code == 404
