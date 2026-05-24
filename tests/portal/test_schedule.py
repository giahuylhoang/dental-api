"""Tests for /api/portal/clinics/{cid}/schedule (in-process v1 proxy)."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_schedule_returns_200_with_default_range(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get(
        "/api/portal/clinics/default/schedule"
        "?start=2026-05-23T09:00:00&end=2026-05-23T17:00:00"
    )
    assert r.status_code == 200
    body = r.json()
    # Underlying service returns a dict with "slots" key (per services/slots.py).
    # The proxy should return that dict directly OR wrap it under "slots".
    assert isinstance(body, dict)


def test_schedule_missing_params_400_or_422(override_portal_user):
    override_portal_user(clinic_ids=["default"])
    r = client.get("/api/portal/clinics/default/schedule")
    assert r.status_code in (400, 422)


def test_schedule_cross_clinic_403(override_portal_user):
    override_portal_user(clinic_ids=["clinic_a"])
    r = client.get(
        "/api/portal/clinics/clinic_b/schedule"
        "?start=2026-05-23T09:00:00&end=2026-05-23T17:00:00"
    )
    assert r.status_code == 403
