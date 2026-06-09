"""Security tests for public holds/slots endpoints.

Verifies that require_internal_secret enforces the shared secret
unconditionally — even when ADMIN_AUTH_BYPASS=true — while still allowing
open access when no secret is configured (dev/test mode).
"""
from datetime import datetime, time

import pytz

from database.models import Clinic, Provider
from database.v1_1.models import ClinicOperatingHours

TZ = pytz.timezone("America/Edmonton")


def _seed_mm(db):
    db.add(Clinic(id="mm", name="MM", timezone="America/Edmonton", contact_phone="4032476222"))
    for dow in range(5):  # Mon–Fri open 09:00–17:00
        db.add(
            ClinicOperatingHours(
                clinic_id="mm",
                day_of_week=dow,
                open_at=time(9, 0),
                close_at=time(17, 0),
                is_closed=False,
            )
        )
    db.add(Provider(id=101, clinic_id="mm", name="Soheil", title="Denturist", is_active=True))
    db.commit()


def _iso(y, mo, d, h):
    return TZ.localize(datetime(y, mo, d, h, 0)).isoformat()


_VALID_HOLD_BODY = {
    "name": "Jane Doe",
    "phone": "4035551234",
    "new_patient": True,
    "provider_id": 101,
    "service_id": None,
    "service_name": "Consultation",
    "start_time": _iso(2026, 6, 10, 14),   # Wednesday 14:00 Edmonton
    "end_time": _iso(2026, 6, 10, 15),     # Wednesday 15:00 Edmonton
    "insurance": "Canadian Dental Care Plan (CDCP)",
    "message": "",
    "recaptcha_token": "test",
}

_VALID_SLOT_PARAMS = {
    "start_datetime": _iso(2026, 6, 10, 9),    # Wednesday 09:00 Edmonton
    "end_datetime": _iso(2026, 6, 10, 17),     # Wednesday 17:00 Edmonton
    "slot_minutes": 30,
}


# ---------------------------------------------------------------------------
# POST /api/public/holds
# ---------------------------------------------------------------------------

def test_holds_requires_secret_even_under_bypass(client, seed_clinic_via_session, monkeypatch):
    """Without X-Internal-Secret → 401; with correct secret → 200."""
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "s3cret")
    seed_clinic_via_session(_seed_mm)

    # Missing secret → rejected even though ADMIN_AUTH_BYPASS=true
    resp_no_secret = client.post(
        "/api/public/holds",
        headers={"X-Clinic-Id": "mm"},
        json=_VALID_HOLD_BODY,
    )
    assert resp_no_secret.status_code == 401, resp_no_secret.text

    # Correct secret → accepted
    resp_ok = client.post(
        "/api/public/holds",
        headers={"X-Clinic-Id": "mm", "X-Internal-Secret": "s3cret"},
        json=_VALID_HOLD_BODY,
    )
    assert resp_ok.status_code == 200, resp_ok.text


def test_holds_rejects_wrong_secret(client, seed_clinic_via_session, monkeypatch):
    """Wrong secret value → 401."""
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "s3cret")
    seed_clinic_via_session(_seed_mm)

    resp = client.post(
        "/api/public/holds",
        headers={"X-Clinic-Id": "mm", "X-Internal-Secret": "wrong"},
        json=_VALID_HOLD_BODY,
    )
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# GET /api/public/slots
# ---------------------------------------------------------------------------

def test_slots_requires_secret_even_under_bypass(client, seed_clinic_via_session, monkeypatch):
    """Without X-Internal-Secret → 401; with correct secret → 200."""
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "s3cret")
    seed_clinic_via_session(_seed_mm)

    # Missing secret → rejected
    resp_no_secret = client.get(
        "/api/public/slots",
        headers={"X-Clinic-Id": "mm"},
        params=_VALID_SLOT_PARAMS,
    )
    assert resp_no_secret.status_code == 401, resp_no_secret.text

    # Correct secret → accepted
    resp_ok = client.get(
        "/api/public/slots",
        headers={"X-Clinic-Id": "mm", "X-Internal-Secret": "s3cret"},
        params=_VALID_SLOT_PARAMS,
    )
    assert resp_ok.status_code == 200, resp_ok.text


# ---------------------------------------------------------------------------
# Dev/test mode: INTERNAL_SECRET not configured → open access
# ---------------------------------------------------------------------------

def test_open_when_no_secret_configured(client, seed_clinic_via_session):
    """When INTERNAL_SECRET is None (default in tests) no header is required."""
    # INTERNAL_SECRET is None in the test environment — no monkeypatch needed
    seed_clinic_via_session(_seed_mm)

    resp = client.post(
        "/api/public/holds",
        headers={"X-Clinic-Id": "mm"},
        json=_VALID_HOLD_BODY,
    )
    assert resp.status_code == 200, resp.text
