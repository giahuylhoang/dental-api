"""Integration tests for the appointment-write timezone boundary (Task 2.2).

The bug: CRM and Market-Mall web callers POST *naive clinic-local* wall-clock
times (e.g. "2026-06-25T14:00:00", no offset). The old write path called
to_storage_utc(), which returns naive input UNCHANGED, so a 2 PM Edmonton
booking was stored verbatim as 14:00 and rendered back 6-7 h early.

After the fix every write boundary calls to_storage_utc_clinic(ts, clinic),
which localizes naive input to the clinic tz before converting to UTC. A 14:00
Edmonton (MDT, -06:00) input must be stored as 20:00 naive UTC.

Per the test plan / repo convention (CLAUDE.md hard rule), the round-trip is
also exercised under the Postgres `pg_client` fixture because SQLite does not
normalize tz-aware -> UTC the way Postgres's `timestamp without time zone`
columns do.
"""
from datetime import datetime, time, timedelta, timezone

import pytz

from database.models import (
    Appointment,
    AppointmentStatus,
    Clinic,
    Patient,
    Provider,
)
from database.v1_1.models import ClinicOperatingHours

TZ = pytz.timezone("America/Edmonton")

# Naive clinic-local wall-clock (no offset) — what the CRM/web actually sends.
NAIVE_LOCAL_START = "2026-06-25T14:00:00"
NAIVE_LOCAL_END = "2026-06-25T15:00:00"
# Edmonton is MDT (-06:00) on 2026-06-25, so 14:00 local == 20:00 UTC.
EXPECTED_UTC_START = datetime(2026, 6, 25, 20, 0)
EXPECTED_UTC_END = datetime(2026, 6, 25, 21, 0)

CID = "tzc"


def _seed_clinic_provider_patient(db):
    db.add(Clinic(id=CID, name="TZ Clinic", timezone="America/Edmonton",
                  contact_phone="4035550000", working_hour_start=9, working_hour_end=17))
    for dow in range(5):
        db.add(ClinicOperatingHours(clinic_id=CID, day_of_week=dow,
                                    open_at=time(9, 0), close_at=time(17, 0), is_closed=False))
    db.add(Provider(id=201, clinic_id=CID, name="Soheil", title="Denturist", is_active=True))
    db.add(Patient(id="pat-1", clinic_id=CID, first_name="Jane", last_name="Doe",
                   phone="+14035551234"))
    db.commit()


def _headers():
    return {"X-Clinic-Id": CID}


# ---------------------------------------------------------------------------
# SQLite (default `client`) integration tests — one per write boundary.
# ---------------------------------------------------------------------------


def test_calendar_create_localizes_naive_input(client, seed_clinic_via_session, db_session):
    seed_clinic_via_session(_seed_clinic_provider_patient)
    resp = client.post("/api/calendar/events", headers=_headers(), json={
        "start_time": NAIVE_LOCAL_START, "end_time": NAIVE_LOCAL_END,
        "patient_id": "pat-1", "provider_id": 201, "service_id": None,
        "patient_name": "Jane Doe", "service_name": "Consultation", "reason": "x",
    })
    assert resp.status_code == 200, resp.text
    appt_id = resp.json()["appointment_id"]
    row = db_session.query(Appointment).filter_by(id=appt_id).one()
    assert row.start_time == EXPECTED_UTC_START
    assert row.end_time == EXPECTED_UTC_END


def test_appointment_update_localizes_naive_input(client, seed_clinic_via_session, db_session):
    seed_clinic_via_session(_seed_clinic_provider_patient)
    # Create with an aware time first (unaffected by the fix), then update with naive.
    create = client.post("/api/calendar/events", headers=_headers(), json={
        "start_time": TZ.localize(datetime(2026, 6, 26, 9, 0)).isoformat(),
        "end_time": TZ.localize(datetime(2026, 6, 26, 9, 30)).isoformat(),
        "patient_id": "pat-1", "provider_id": 201, "service_id": None,
        "patient_name": "Jane Doe", "service_name": "Consultation", "reason": "x",
    })
    appt_id = create.json()["appointment_id"]

    resp = client.put(f"/api/appointments/{appt_id}", headers=_headers(), json={
        "start_time": NAIVE_LOCAL_START, "end_time": NAIVE_LOCAL_END,
    })
    assert resp.status_code == 200, resp.text
    db_session.expire_all()
    row = db_session.query(Appointment).filter_by(id=appt_id).one()
    assert row.start_time == EXPECTED_UTC_START
    assert row.end_time == EXPECTED_UTC_END


def test_reschedule_localizes_naive_input(client, seed_clinic_via_session, db_session):
    seed_clinic_via_session(_seed_clinic_provider_patient)
    create = client.post("/api/calendar/events", headers=_headers(), json={
        "start_time": TZ.localize(datetime(2026, 6, 26, 9, 0)).isoformat(),
        "end_time": TZ.localize(datetime(2026, 6, 26, 9, 30)).isoformat(),
        "patient_id": "pat-1", "provider_id": 201, "service_id": None,
        "patient_name": "Jane Doe", "service_name": "Consultation", "reason": "x",
    })
    appt_id = create.json()["appointment_id"]

    resp = client.put(f"/api/appointments/{appt_id}/reschedule", headers=_headers(), json={
        "start_time": NAIVE_LOCAL_START, "end_time": NAIVE_LOCAL_END,
        "patient_id": "pat-1", "provider_id": 201, "service_id": None,
        "patient_name": "Jane Doe", "service_name": "Consultation", "reason": "moved",
    })
    assert resp.status_code == 200, resp.text
    # Reschedule creates a NEW SCHEDULED appointment; find it.
    db_session.expire_all()
    new_row = (
        db_session.query(Appointment)
        .filter(Appointment.clinic_id == CID,
                Appointment.status == AppointmentStatus.SCHEDULED)
        .one()
    )
    assert new_row.start_time == EXPECTED_UTC_START
    assert new_row.end_time == EXPECTED_UTC_END


def test_public_hold_localizes_naive_input(client, seed_clinic_via_session, db_session):
    seed_clinic_via_session(_seed_clinic_provider_patient)
    resp = client.post("/api/public/holds", headers=_headers(), json={
        "name": "Jane Doe", "phone": "4035559999", "new_patient": True,
        "provider_id": 201, "service_id": None, "service_name": "Consultation",
        "start_time": NAIVE_LOCAL_START, "end_time": NAIVE_LOCAL_END,
        "recaptcha_token": "test",
    })
    assert resp.status_code == 200, resp.text
    appt_id = resp.json()["appointment_id"]
    row = db_session.query(Appointment).filter_by(id=appt_id).one()
    assert row.start_time == EXPECTED_UTC_START
    assert row.end_time == EXPECTED_UTC_END


def test_internal_hold_aware_voice_input_unchanged(client, seed_clinic_via_session, db_session):
    """Voice agent (source='voice-hold') sends OFFSET-AWARE times. The switch to
    to_storage_utc_clinic must not change that behavior: aware input converts from
    its own offset, clinic irrelevant. 14:00-06:00 -> 20:00 UTC."""
    seed_clinic_via_session(_seed_clinic_provider_patient)
    aware_start = datetime(2026, 6, 25, 14, 0, tzinfo=timezone(timedelta(hours=-6))).isoformat()
    aware_end = datetime(2026, 6, 25, 15, 0, tzinfo=timezone(timedelta(hours=-6))).isoformat()
    resp = client.post("/api/internal/holds", headers=_headers(), json={
        "name": "Jane Doe", "phone": "4035558888", "new_patient": True,
        "provider_id": 201, "service_id": None, "service_name": "Consultation",
        "start_time": aware_start, "end_time": aware_end,
    })
    assert resp.status_code == 200, resp.text
    appt_id = resp.json()["appointment_id"]
    row = db_session.query(Appointment).filter_by(id=appt_id).one()
    assert row.source == "voice-hold"
    assert row.start_time == EXPECTED_UTC_START
    assert row.end_time == EXPECTED_UTC_END


# ---------------------------------------------------------------------------
# Postgres round-trip (pg_client) — confirms timestamp-without-tz behavior
# matches production, per CLAUDE.md hard rule.
# ---------------------------------------------------------------------------


def _seed_pg(pg_db_session):
    """Seed clinic CID + provider on the Postgres test DB."""
    if pg_db_session.query(Clinic).filter(Clinic.id == CID).first() is None:
        pg_db_session.add(Clinic(id=CID, name="TZ Clinic", timezone="America/Edmonton",
                                 contact_phone="4035550000",
                                 working_hour_start=9, working_hour_end=17))
    pg_db_session.add(Provider(clinic_id=CID, name="Soheil", title="Denturist", is_active=True))
    pg_db_session.flush()


def test_public_hold_localizes_naive_input_postgres(pg_client, pg_db_session):
    _seed_pg(pg_db_session)
    resp = pg_client.post("/api/public/holds", headers=_headers(), json={
        "name": "Jane Doe", "phone": "4035557777", "new_patient": True,
        "provider_id": pg_db_session.query(Provider).filter_by(clinic_id=CID).first().id,
        "service_id": None, "service_name": "Consultation",
        "start_time": NAIVE_LOCAL_START, "end_time": NAIVE_LOCAL_END,
        "recaptcha_token": "test",
    })
    assert resp.status_code == 200, resp.text
    appt_id = resp.json()["appointment_id"]
    row = pg_db_session.query(Appointment).filter_by(id=appt_id).one()
    assert row.start_time == EXPECTED_UTC_START
    assert row.end_time == EXPECTED_UTC_END
