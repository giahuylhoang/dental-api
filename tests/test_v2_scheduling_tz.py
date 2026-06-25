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


def test_v2_recurrence_cross_zone_aware_input_keeps_clinic_local_wall_clock(client, db_session):
    """Cross-zone aware input must anchor recurrence on the CLINIC-local wall
    clock, not the caller's submitted wall clock.

    Input 2026-07-15T14:00:00-05:00 == 19:00 UTC == 13:00 Edmonton/MDT. The
    parent stores 19:00 UTC (13:00 Edmonton). Children must also sit at 13:00
    Edmonton (19:00 UTC) on successive days — sharing the parent's clinic-local
    wall time. On the buggy code the children derive from naive 14:00 and land
    at 20:00 UTC (14:00 Edmonton), one hour off from the parent."""
    patient, provider = _seed(db_session)

    resp = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-07-15T14:00:00-05:00",
        "end_time": "2026-07-15T15:00:00-05:00",
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
    # 13:00 Edmonton/MDT (UTC-6) == 19:00 UTC on each day; parent + children
    # share the same clinic-local wall clock (13:00).
    expected = [
        datetime(2026, 7, 15, 19, 0, 0),
        datetime(2026, 7, 16, 19, 0, 0),
        datetime(2026, 7, 17, 19, 0, 0),
    ]
    assert [r.start_time for r in rows] == expected, [r.start_time for r in rows]
    assert [r.end_time for r in rows] == [e.replace(hour=20) for e in expected]


def test_v2_recurrence_keeps_wall_clock_across_dst_fall_back(client, db_session):
    """Weekly recurrence spanning the Nov 1, 2026 fall-back (MDT -6 -> MST -7)
    must keep a CONSTANT clinic-local wall time (09:00 Edmonton) while the stored
    naive-UTC shifts at the boundary (15:00 UTC before, 16:00 UTC after).

    Pins that per-occurrence conversion (not a single anchor offset) is applied,
    so DST transitions do not drag the wall clock."""
    from services.tz_utils import to_clinic_local
    from database.models import Clinic
    from database.models import DEFAULT_CLINIC_ID as _CID

    patient, provider = _seed(db_session)
    clinic = db_session.query(Clinic).filter(Clinic.id == _CID).first()

    resp = client.post("/api/v2/scheduling/appointments", json={
        "start_time": "2026-10-26T09:00:00",
        "end_time": "2026-10-26T10:00:00",
        "patient_id": patient.id,
        "provider_id": provider.id,
        "patient_name": "T",
        "service_name": "S",
        "recurrence_rule": "FREQ=WEEKLY;COUNT=3",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert resp.status_code == 201, resp.text
    assert resp.json()["generated_count"] == 3

    rows = db_session.query(Appointment).filter(
        Appointment.clinic_id == DEFAULT_CLINIC_ID,
        Appointment.patient_id == patient.id,
    ).order_by(Appointment.start_time).all()
    assert len(rows) == 3

    # Clinic-local wall clock stays 09:00 on all three occurrences.
    for r in rows:
        assert to_clinic_local(r.start_time, clinic).hour == 9, r.start_time

    # Stored naive-UTC shifts at the DST boundary:
    # 2026-10-26 09:00 MDT (-6) == 15:00 UTC
    # 2026-11-02 09:00 MST (-7) == 16:00 UTC
    # 2026-11-09 09:00 MST (-7) == 16:00 UTC
    expected = [
        datetime(2026, 10, 26, 15, 0, 0),
        datetime(2026, 11, 2, 16, 0, 0),
        datetime(2026, 11, 9, 16, 0, 0),
    ]
    assert [r.start_time for r in rows] == expected, [r.start_time for r in rows]


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


def test_v2_calendar_includes_late_evening_local_appt_and_serializes_local(client, db_session):
    """The v2 calendar read must (a) filter on UTC bounds so a late-evening local
    appointment (stored on the NEXT UTC day) still falls inside a clinic-local day
    window, and (b) serialize times back as clinic-local wall-clock.

    Seed an appt at 23:00 Edmonton/MDT on 2026-07-15 (== naive UTC
    2026-07-16T05:00). A clinic-local day window 2026-07-15T00:00 -> 2026-07-16T00:00
    must still return it (on the buggy code the stored UTC 16th falls outside the
    naive 15th window), and its start_time must serialize as the clinic-local
    23:00, not UTC 05:00."""
    patient, provider = _seed(db_session)

    # Create via v1 so start_time lands as naive UTC 2026-07-16T05:00.
    create = client.post("/api/appointments", json={
        "patient_id": patient.id,
        "provider_id": provider.id,
        "start_time": "2026-07-15T23:00:00",
        "end_time": "2026-07-15T23:30:00",
        "patient_name": "LateLocal",
        "service_name": "S",
        "reason": "",
    }, headers={"X-Clinic-Id": DEFAULT_CLINIC_ID})
    assert create.status_code in (200, 201), create.text

    # Confirm the storage contract: naive UTC 2026-07-16T05:00.
    row = db_session.query(Appointment).filter(
        Appointment.clinic_id == DEFAULT_CLINIC_ID,
        Appointment.patient_id == patient.id,
    ).one()
    assert row.start_time == datetime(2026, 7, 16, 5, 0, 0), row.start_time

    resp = client.get(
        "/api/v2/scheduling/calendar",
        params={"start": "2026-07-15T00:00:00", "end": "2026-07-16T00:00:00"},
        headers={"X-Clinic-Id": DEFAULT_CLINIC_ID},
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    matching = [r for r in rows if r["id"] == row.id]
    assert matching, "late-evening local appt was dropped from the clinic-local day window"
    apt = matching[0]
    # Clinic-local wall clock, not stored UTC.
    assert apt["start_time"].startswith("2026-07-15T23:00"), apt["start_time"]
    assert apt["end_time"].startswith("2026-07-15T23:30"), apt["end_time"]
    assert not apt["start_time"].startswith("2026-07-16T05:00"), apt["start_time"]


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
