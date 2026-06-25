"""Task 2.3 — GET day-list, DELETE-by-date, and conflict-check UTC consistency.

After Task 2.2 every appointment is stored as naive UTC. The read/filter
queries must therefore build their clinic-local day window and convert it to
UTC before comparing against the stored column. A late-evening Edmonton
appointment (21:00 local) is stored at 03:00 UTC the NEXT day, so a naive
day-window (treating the date as UTC midnight) would file it on the wrong day.

Conflict consistency: a 14:00 Edmonton booking must conflict with an existing
14:00 Edmonton booking. Both are stored as 20:00 UTC, so the conflict check
(operating on naive UTC) detects the overlap end-to-end.
"""
from datetime import datetime, time

import pytz

from database.models import Appointment, AppointmentStatus, Clinic, Patient, Provider
from database.v1_1.models import ClinicOperatingHours

TZ = pytz.timezone("America/Edmonton")
CID = "tzq"


def _seed(db):
    db.add(Clinic(id=CID, name="TZ Query Clinic", timezone="America/Edmonton",
                  contact_phone="4035550000", working_hour_start=0, working_hour_end=23))
    for dow in range(7):
        db.add(ClinicOperatingHours(clinic_id=CID, day_of_week=dow,
                                    open_at=time(0, 0), close_at=time(23, 59), is_closed=False))
    db.add(Provider(id=301, clinic_id=CID, name="Soheil", title="Denturist", is_active=True))
    db.add(Patient(id="pq-1", clinic_id=CID, first_name="Jane", last_name="Doe",
                   phone="+14035551234"))
    db.commit()


def _headers():
    return {"X-Clinic-Id": CID}


def _create_evening_appt(client):
    """Create a 21:00 Edmonton appointment on 2026-06-25 (stored 03:00 UTC 06-26)."""
    resp = client.post("/api/calendar/events", headers=_headers(), json={
        "start_time": "2026-06-25T21:00:00", "end_time": "2026-06-25T21:30:00",
        "patient_id": "pq-1", "provider_id": 301, "service_id": None,
        "patient_name": "Jane Doe", "service_name": "Consultation", "reason": "evening",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["appointment_id"]


def test_get_day_list_includes_late_evening_local_appt(client, seed_clinic_via_session, db_session):
    seed_clinic_via_session(_seed)
    appt_id = _create_evening_appt(client)
    # Sanity: stored as 03:00 UTC on the following day.
    assert db_session.query(Appointment).filter_by(id=appt_id).one().start_time == datetime(2026, 6, 26, 3, 0)

    resp = client.get("/api/appointments", headers=_headers(), params={"date": "2026-06-25"})
    assert resp.status_code == 200, resp.text
    ids = [a["id"] for a in resp.json()]
    assert appt_id in ids, "late-evening Edmonton appt must appear on its clinic-local day"


def test_get_day_list_excludes_appt_from_next_local_day(client, seed_clinic_via_session):
    seed_clinic_via_session(_seed)
    appt_id = _create_evening_appt(client)
    # It must NOT show up on 2026-06-26 (it's a 06-25 clinic-local appointment).
    resp = client.get("/api/appointments", headers=_headers(), params={"date": "2026-06-26"})
    assert resp.status_code == 200, resp.text
    ids = [a["id"] for a in resp.json()]
    assert appt_id not in ids


def test_delete_by_date_targets_clinic_local_day(client, seed_clinic_via_session):
    seed_clinic_via_session(_seed)
    appt_id = _create_evening_appt(client)
    # dry-run delete for the clinic-local day must find exactly this appointment.
    resp = client.delete("/api/appointments/bulk/date/2026-06-25",
                         headers=_headers(), params={"dry_run": True})
    assert resp.status_code == 200, resp.text
    assert resp.json()["appointments_found"] == 1
    # And the next day finds none.
    resp2 = client.delete("/api/appointments/bulk/date/2026-06-26",
                          headers=_headers(), params={"dry_run": True})
    assert resp2.json()["appointments_found"] == 0


def _book(client, start_local, end_local):
    return client.post("/api/calendar/events", headers=_headers(), json={
        "start_time": start_local, "end_time": end_local,
        "patient_id": "pq-1", "provider_id": 301, "service_id": None,
        "patient_name": "Jane Doe", "service_name": "Consultation", "reason": "x",
    })


def test_conflict_detected_for_same_local_time(client, seed_clinic_via_session):
    """Two 14:00 Edmonton bookings (both stored 20:00 UTC) must conflict."""
    seed_clinic_via_session(_seed)
    first = _book(client, "2026-06-25T14:00:00", "2026-06-25T15:00:00")
    assert first.status_code == 200, first.text
    second = _book(client, "2026-06-25T14:00:00", "2026-06-25T15:00:00")
    assert second.status_code == 409


def _seed_pg(pg_db_session):
    if pg_db_session.query(Clinic).filter(Clinic.id == CID).first() is None:
        pg_db_session.add(Clinic(id=CID, name="TZ Query Clinic", timezone="America/Edmonton",
                                 contact_phone="4035550000",
                                 working_hour_start=0, working_hour_end=23))
    pg_db_session.add(Provider(clinic_id=CID, name="Soheil", title="Denturist", is_active=True))
    pg_db_session.add(Patient(id="pq-pg", clinic_id=CID, first_name="Jane", last_name="Doe",
                              phone="+14035551234"))
    pg_db_session.flush()


def test_conflict_detected_for_same_local_time_postgres(pg_client, pg_db_session):
    """Conflict detection under Postgres timestamp-without-tz semantics."""
    _seed_pg(pg_db_session)
    pid = pg_db_session.query(Provider).filter_by(clinic_id=CID).first().id
    body = {
        "start_time": "2026-06-25T14:00:00", "end_time": "2026-06-25T15:00:00",
        "patient_id": "pq-pg", "provider_id": pid, "service_id": None,
        "patient_name": "Jane Doe", "service_name": "Consultation", "reason": "x",
    }
    first = pg_client.post("/api/calendar/events", headers=_headers(), json=body)
    assert first.status_code == 200, first.text
    second = pg_client.post("/api/calendar/events", headers=_headers(), json=body)
    assert second.status_code == 409
