"""Tests for GET /api/public/slots — internal-secret-gated availability endpoint.

Mirrors the query-param contract and response shape of GET /api/calendar/slots,
but authenticated via X-Internal-Secret instead of Firebase.
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
    db.add(Provider(id=201, clinic_id="mm", name="Soheil", title="Denturist", is_active=True))
    db.commit()


def _iso(y, mo, d, h):
    return TZ.localize(datetime(y, mo, d, h, 0)).isoformat()


# ---------------------------------------------------------------------------
# Happy-path: multi-provider response (no provider_id filter)
# ---------------------------------------------------------------------------

def test_public_slots_all_providers_returns_200(client, seed_clinic_via_session):
    """GET /api/public/slots → 200 with multi-provider shape on an open weekday."""
    seed_clinic_via_session(_seed_mm)

    # 2026-06-15 is a Monday; 09:00–12:00 Edmonton → expect 6 slots (half-hour)
    resp = client.get(
        "/api/public/slots",
        headers={"X-Clinic-Id": "mm"},
        params={
            "start_datetime": _iso(2026, 6, 15, 9),
            "end_datetime": _iso(2026, 6, 15, 12),
            "slot_minutes": 30,
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    # Multi-provider top-level shape
    assert "providers" in body, f"expected 'providers' key, got: {list(body.keys())}"
    assert isinstance(body["providers"], list)
    assert len(body["providers"]) >= 1

    # Per-provider entry shape mirrors GET /api/calendar/slots
    entry = body["providers"][0]
    assert "provider_id" in entry
    assert "slots" in entry
    assert isinstance(entry["slots"], list)

    # With one provider (id=201) and a 3-hour Mon window at 30 min: 6 slots expected
    assert len(entry["slots"]) == 6


# ---------------------------------------------------------------------------
# Happy-path: single-provider response (provider_id filter)
# ---------------------------------------------------------------------------

def test_public_slots_single_provider_returns_correct_shape(client, seed_clinic_via_session):
    """When provider_id is supplied the response is {provider: {...}, slots: [...]}."""
    seed_clinic_via_session(_seed_mm)

    resp = client.get(
        "/api/public/slots",
        headers={"X-Clinic-Id": "mm"},
        params={
            "start_datetime": _iso(2026, 6, 15, 9),
            "end_datetime": _iso(2026, 6, 15, 12),
            "provider_id": 201,
            "slot_minutes": 30,
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    # Single-provider shape
    assert "provider" in body, f"expected 'provider' key, got: {list(body.keys())}"
    assert "slots" in body
    assert isinstance(body["slots"], list)
    assert body["provider"]["provider_id"] == 201
    assert len(body["slots"]) == 6


# ---------------------------------------------------------------------------
# Auth: missing clinic header → 404 (clinic_not_found)
# ---------------------------------------------------------------------------

def test_public_slots_unknown_clinic_returns_404(client, seed_clinic_via_session):
    resp = client.get(
        "/api/public/slots",
        headers={"X-Clinic-Id": "does-not-exist"},
        params={
            "start_datetime": _iso(2026, 6, 15, 9),
            "end_datetime": _iso(2026, 6, 15, 12),
        },
    )
    assert resp.status_code == 404
