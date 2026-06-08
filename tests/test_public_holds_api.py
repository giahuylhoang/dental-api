"""Tests for POST /api/public/holds endpoint."""
from datetime import datetime, time
import pytz
from database.models import Clinic, Provider, AppointmentStatus, Appointment
from database.v1_1.models import ClinicOperatingHours

TZ = pytz.timezone("America/Edmonton")


def _seed_mm(db):
    db.add(Clinic(id="mm", name="MM", timezone="America/Edmonton", contact_phone="4032476222"))
    for dow in range(5):
        db.add(ClinicOperatingHours(clinic_id="mm", day_of_week=dow,
                                    open_at=time(9, 0), close_at=time(17, 0), is_closed=False))
    db.add(Provider(id=101, clinic_id="mm", name="Soheil", title="Denturist", is_active=True))
    db.commit()


def _iso(y, mo, d, h):
    return TZ.localize(datetime(y, mo, d, h, 0)).isoformat()


def test_public_hold_creates_pending(client, seed_clinic_via_session):
    seed_clinic_via_session(_seed_mm)
    resp = client.post("/api/public/holds",
        headers={"X-Clinic-Id": "mm"},
        json={"name": "Jane Doe", "phone": "4035551234", "new_patient": True,
              "provider_id": 101, "service_id": None, "service_name": "Consultation",
              "start_time": _iso(2026, 6, 10, 14), "end_time": _iso(2026, 6, 10, 15),
              "insurance": "Canadian Dental Care Plan (CDCP)", "message": "",
              "recaptcha_token": "test"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["provider_id"] == 101


def test_public_hold_conflict_returns_409(client, seed_clinic_via_session):
    seed_clinic_via_session(_seed_mm)
    payload = {"name": "A", "phone": "4035550000", "new_patient": True,
               "provider_id": 101, "service_id": None, "service_name": "Consultation",
               "start_time": _iso(2026, 6, 10, 14), "end_time": _iso(2026, 6, 10, 15),
               "recaptcha_token": "test"}
    r1 = client.post("/api/public/holds", headers={"X-Clinic-Id": "mm"}, json=payload)
    assert r1.status_code == 200
    payload["phone"] = "4035551111"
    r2 = client.post("/api/public/holds", headers={"X-Clinic-Id": "mm"}, json=payload)
    assert r2.status_code == 409
