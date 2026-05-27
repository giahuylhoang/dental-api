"""Unit tests for subtract.appointments_for."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Appointment, AppointmentStatus, Clinic, Patient, Provider
from services.slot_engine.subtract import appointments_for


TZ = pytz.timezone("America/Edmonton")
MON = date(2026, 5, 25)


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    pat = Patient(id="pat-c1", first_name="T", last_name="P", clinic_id="c1")
    db_session.add_all([c, p, pat])
    db_session.commit()
    return c, p


def _apt(p_id, start, end, status=AppointmentStatus.SCHEDULED):
    return Appointment(
        clinic_id="c1", patient_id="pat-c1", provider_id=p_id,
        start_time=start, end_time=end, status=status,
        reason_note="t",
    )


def test_no_appointments_returns_empty(db_session, setup):
    _, p = setup
    assert appointments_for(p.id, "c1", MON, TZ, db_session).is_empty


def test_active_appointment_contributes_interval(db_session, setup):
    _, p = setup
    db_session.add(_apt(
        p.id,
        TZ.localize(datetime(2026, 5, 25, 10, 0)),
        TZ.localize(datetime(2026, 5, 25, 11, 0)),
    ))
    db_session.commit()
    result = appointments_for(p.id, "c1", MON, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 10, 0)),
        TZ.localize(datetime(2026, 5, 25, 11, 0)),
    )]


def test_cancelled_completed_no_show_excluded(db_session, setup):
    _, p = setup
    for st in (AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED,
               AppointmentStatus.NO_SHOW):
        db_session.add(_apt(
            p.id,
            TZ.localize(datetime(2026, 5, 25, 10, 0)),
            TZ.localize(datetime(2026, 5, 25, 11, 0)),
            status=st,
        ))
    db_session.commit()
    assert appointments_for(p.id, "c1", MON, TZ, db_session).is_empty


def test_confirmed_pending_pending_sync_all_count_as_busy(db_session, setup):
    _, p = setup
    statuses = [
        (AppointmentStatus.CONFIRMED,   9,  10),
        (AppointmentStatus.PENDING,    10,  11),
        (AppointmentStatus.PENDING_SYNC, 11, 12),
    ]
    for st, sh, eh in statuses:
        db_session.add(_apt(
            p.id,
            TZ.localize(datetime(2026, 5, 25, sh, 0)),
            TZ.localize(datetime(2026, 5, 25, eh, 0)),
            status=st,
        ))
    db_session.commit()
    result = appointments_for(p.id, "c1", MON, TZ, db_session)
    assert result.intervals == [
        (TZ.localize(datetime(2026, 5, 25,  9, 0)), TZ.localize(datetime(2026, 5, 25, 10, 0))),
        (TZ.localize(datetime(2026, 5, 25, 10, 0)), TZ.localize(datetime(2026, 5, 25, 11, 0))),
        (TZ.localize(datetime(2026, 5, 25, 11, 0)), TZ.localize(datetime(2026, 5, 25, 12, 0))),
    ]


def test_appointment_crossing_midnight_clips_per_day(db_session, setup):
    _, p = setup
    # 23:00 Mon to 02:00 Tue
    db_session.add(_apt(
        p.id,
        TZ.localize(datetime(2026, 5, 25, 23, 0)),
        TZ.localize(datetime(2026, 5, 26,  2, 0)),
    ))
    db_session.commit()
    mon_r = appointments_for(p.id, "c1", MON, TZ, db_session)
    assert mon_r.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 23, 0)),
        TZ.localize(datetime(2026, 5, 26,  0, 0)),
    )]
    tue_r = appointments_for(p.id, "c1", date(2026, 5, 26), TZ, db_session)
    assert tue_r.intervals == [(
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
        TZ.localize(datetime(2026, 5, 26, 2, 0)),
    )]
