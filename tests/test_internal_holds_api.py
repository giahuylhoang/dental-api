"""Tests for POST /api/internal/holds endpoint.

Tests run with ADMIN_AUTH_BYPASS=true and INTERNAL_SECRET=None (default in
tests/conftest.py), so the require_internal_secret dependency passes through
(the check is skipped when no secret is configured).
"""
from datetime import datetime, time
import pytz
from database.models import Clinic, Provider, Appointment, AppointmentStatus
from database.v1_1.models import ClinicOperatingHours

TZ = pytz.timezone("America/Edmonton")


def _seed_mm_internal(db):
    """Seed a minimal market-mall-denture clinic with provider 101 and Mon-Fri hours."""
    db.add(Clinic(
        id="mm-internal", name="Market Mall Internal Test",
        timezone="America/Edmonton", contact_phone="4032476222",
    ))
    for dow in range(5):
        db.add(ClinicOperatingHours(
            clinic_id="mm-internal", day_of_week=dow,
            open_at=time(9, 0), close_at=time(17, 0), is_closed=False,
        ))
    db.add(Provider(
        id=101, clinic_id="mm-internal", name="Soheil", title="Denturist", is_active=True,
    ))
    db.commit()


def _iso(y, mo, d, h):
    return TZ.localize(datetime(y, mo, d, h, 0)).isoformat()


def test_internal_hold_creates_pending_with_voice_hold_source(client, seed_clinic_via_session):
    """POST /api/internal/holds must create a PENDING appointment with source='voice-hold'."""
    seed_clinic_via_session(_seed_mm_internal)
    resp = client.post(
        "/api/internal/holds",
        headers={"X-Clinic-Id": "mm-internal"},
        json={
            "name": "Jane Doe",
            "phone": "4035551234",
            "new_patient": True,
            "provider_id": 101,
            "service_id": None,
            "service_name": "Consultation",
            "start_time": _iso(2026, 6, 15, 14),
            "end_time": _iso(2026, 6, 15, 15),
            "message": "New denture consultation",
        },
    )
    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["provider_id"] == 101
    assert body["source"] == "voice-hold"
    assert "appointment_id" in body


def test_internal_hold_source_is_always_voice_hold(client, seed_clinic_via_session, db_session):
    """Verify the DB row has source='voice-hold' (not anything the caller could forge)."""
    seed_clinic_via_session(_seed_mm_internal)
    resp = client.post(
        "/api/internal/holds",
        headers={"X-Clinic-Id": "mm-internal"},
        json={
            "name": "Bob Smith",
            "phone": "4035559999",
            "new_patient": False,
            "provider_id": 101,
            "service_name": "Reline",
            "start_time": _iso(2026, 6, 16, 10),
            "end_time": _iso(2026, 6, 16, 11),
        },
    )
    assert resp.status_code == 200, resp.json()
    appt_id = resp.json()["appointment_id"]
    appt = db_session.query(Appointment).filter(Appointment.id == appt_id).first()
    assert appt is not None, "Appointment row not found in DB"
    assert appt.source == "voice-hold"
    assert appt.status == AppointmentStatus.PENDING


def test_internal_hold_conflict_returns_409(client, seed_clinic_via_session):
    """Second booking for the same provider + time slot must return 409."""
    seed_clinic_via_session(_seed_mm_internal)
    payload = {
        "name": "Alice",
        "phone": "4035550001",
        "new_patient": True,
        "provider_id": 101,
        "service_name": "Consultation",
        "start_time": _iso(2026, 6, 17, 14),
        "end_time": _iso(2026, 6, 17, 15),
    }
    r1 = client.post("/api/internal/holds", headers={"X-Clinic-Id": "mm-internal"}, json=payload)
    assert r1.status_code == 200, r1.json()

    # Second caller tries the same slot
    payload["phone"] = "4035550002"
    payload["name"] = "Bob"
    r2 = client.post("/api/internal/holds", headers={"X-Clinic-Id": "mm-internal"}, json=payload)
    assert r2.status_code == 409
