from datetime import datetime, time
import pytz
from database.models import Clinic, Provider
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


def _make_hold(client):
    return client.post("/api/public/holds", headers={"X-Clinic-Id": "mm"},
        json={"name": "Jane", "phone": "4035551234", "new_patient": True, "provider_id": 101,
              "service_name": "Consultation", "start_time": _iso(2026, 6, 10, 14),
              "end_time": _iso(2026, 6, 10, 15), "recaptcha_token": "test"}).json()["appointment_id"]


def test_list_pending_holds(client, seed_clinic_via_session):
    seed_clinic_via_session(_seed_mm)
    _make_hold(client)
    resp = client.get("/api/holds/pending", headers={"X-Clinic-Id": "mm"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["source"] == "booking-web-hold"


def test_confirm_hold_endpoint(client, seed_clinic_via_session):
    seed_clinic_via_session(_seed_mm)
    appt_id = _make_hold(client)
    resp = client.post(f"/api/holds/{appt_id}/confirm", headers={"X-Clinic-Id": "mm"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "SCHEDULED"


def test_decline_hold_endpoint(client, seed_clinic_via_session):
    seed_clinic_via_session(_seed_mm)
    appt_id = _make_hold(client)
    resp = client.post(f"/api/holds/{appt_id}/decline", headers={"X-Clinic-Id": "mm"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"
