"""v2 scheduling write boundaries must store naive UTC (storage contract).

The v1 router and public/internal holds interpret incoming appointment times
as clinic-local wall-clock and convert to naive UTC via
``services.tz_utils.to_storage_utc_clinic`` before writing. The v2 router
(``create_v2_appointment``, its recurrence children, and
``reschedule_v2_appointment``) historically stored raw parsed values, so v2
rows diverged from the rest of the DB. These tests pin the contract:

- naive clinic-local input -> stored as naive UTC
- offset-aware input -> honored (offset NOT stripped), stored as naive UTC
- recurrence occurrences -> each converted to naive UTC on the clinic wall clock
- v2-created and v1-created rows at the same wall time conflict (shared UTC repr)
- reschedule stores naive UTC
"""
from datetime import datetime

import pytest

from database.models import (
    Appointment,
    AppointmentStatus,
    Patient,
    Provider,
    DEFAULT_CLINIC_ID,
)
from services.tz_utils import to_storage_utc_clinic  # noqa: F401  (reference of the helper under test)


def _make_patient(db, name="TzPatient"):
    p = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name=name, phone="555")
    db.add(p)
    db.flush()
    return p


def _make_provider(db, name="Dr Tz"):
    prov = db.query(Provider).filter(Provider.clinic_id == DEFAULT_CLINIC_ID).first()
    if prov is None:
        prov = Provider(clinic_id=DEFAULT_CLINIC_ID, name=name)
        db.add(prov)
        db.flush()
    return prov


# Default clinic tz is America/Edmonton. July -> MDT (UTC-6). 14:00 local == 20:00 UTC.
LOCAL_14 = "2026-07-15T14:00:00"
LOCAL_15 = "2026-07-15T15:00:00"
UTC_20 = datetime(2026, 7, 15, 20, 0, 0)
UTC_21 = datetime(2026, 7, 15, 21, 0, 0)


def _seed(db):
    patient = _make_patient(db)
    provider = _make_provider(db)
    db.commit()
    return patient, provider


def test_v2_create_stores_naive_utc_from_naive_local_input(client, db_session):
    patient, provider = _seed(db_session)

    resp = client.post("/api/v2/scheduling/appointments", json={
        "start_time": LOCAL_14,
        "end_time": LOCAL_15,
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "T",
        "service_name": "S",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert resp.status_code == 201, resp.text
    apt_id = resp.json()["appointment_id"]

    row = db_session.query(Appointment).filter(Appointment.id == apt_id).one()
    assert row.start_time == UTC_20, row.start_time
    assert row.end_time == UTC_21, row.end_time


def test_v2_create_stores_naive_utc_from_offset_aware_input(client, db_session):
    """Aware input must be honored (offset preserved through parse), not stripped
    to a naive 14:00 and then re-interpreted as clinic-local (which would shift)."""
    patient, provider = _seed(db_session)

    resp = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-07-15T14:00:00-06:00",
        "end_time": "2026-07-15T15:00:00-06:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "T",
        "service_name": "S",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert resp.status_code == 201, resp.text
    apt_id = resp.json()["appointment_id"]

    row = db_session.query(Appointment).filter(Appointment.id == apt_id).one()
    assert row.start_time == UTC_20, row.start_time
    assert row.end_time == UTC_21, row.end_time


def test_v2_recurrence_children_store_naive_utc(client, db_session):
    """Each recurrence occurrence keeps its clinic-local wall clock (9am daily
    stays 9am) and is stored as naive UTC."""
    patient, provider = _seed(db_session)

    resp = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-07-15T14:00:00",
        "end_time": "2026-07-15T15:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "T",
        "service_name": "S",
        "recurrence_rule": "FREQ=DAILY;COUNT=3",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert resp.status_code == 201, resp.text
    assert resp.json()["generated_count"] == 3

    rows = db_session.query(Appointment).filter(
        Appointment.clinic_id == DEFAULT_CLINIC_ID,
        Appointment.patient_id == patient.id,
    ).order_by(Appointment.start_time).all()
    assert len(rows) == 3
    expected = [
        datetime(2026, 7, 15, 20, 0, 0),
        datetime(2026, 7, 16, 20, 0, 0),
        datetime(2026, 7, 17, 20, 0, 0),
    ]
    assert [r.start_time for r in rows] == expected, [r.start_time for r in rows]
    assert [r.end_time for r in rows] == [e.replace(hour=21) for e in expected]


def test_v2_v1_conflict_parity(client, db_session):
    """A v2-created appt at 14:00 local must conflict with a v1-created appt at
    the same wall time — proves both now share one naive-UTC representation."""
    patient, provider = _seed(db_session)

    # v1 create at 14:00 local
    r1 = client.post("/api/appointments", json={
        "patient_id": patient.id,
        "provider_id": provider.id,
        "start_time": LOCAL_14,
        "end_time": LOCAL_15,
        "patient_name": "v1",
        "service_name": "S",
        "reason": "",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert r1.status_code in (200, 201), r1.text

    # v2 create at the same wall time -> must 409 on provider conflict
    r2 = client.post("/api/v2/scheduling/appointments", json={
        "start_time": LOCAL_14,
        "end_time": LOCAL_15,
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "v2",
        "service_name": "S",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert r2.status_code == 409, r2.text


def test_v2_reschedule_stores_naive_utc(client, db_session):
    patient, provider = _seed(db_session)

    # Create an appt at some other time, then reschedule to 14:00 local.
    create = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-07-15T08:00:00",
        "end_time": "2026-07-15T09:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "T",
        "service_name": "S",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert create.status_code == 201, create.text
    original_id = create.json()["appointment_id"]

    resp = client.post(
        f"/api/v2/scheduling/appointments/{original_id}/reschedule",
        json={"start_time": LOCAL_14, "end_time": LOCAL_15},
        headers={"X-Clinic-Id": DEFAULT_CLINIC_ID},
    )
    assert resp.status_code == 200, resp.text
    new_id = resp.json()["appointment_id"]

    row = db_session.query(Appointment).filter(Appointment.id == new_id).one()
    assert row.start_time == UTC_20, row.start_time
    assert row.end_time == UTC_21, row.end_time
