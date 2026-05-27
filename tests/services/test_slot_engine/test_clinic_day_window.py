"""Unit tests for windows.clinic_day_window."""
from datetime import date, datetime, time, timedelta
import logging

import pytest
import pytz

from database.models import Clinic, DEFAULT_CLINIC_ID
from database.v1_1.models import ClinicOperatingHours, ClinicClosure
from services.slot_engine.windows import clinic_day_window


TZ = pytz.timezone("America/Edmonton")
MON = date(2026, 5, 25)   # Monday
SAT = date(2026, 5, 23)   # Saturday


@pytest.fixture
def clinic(db_session):
    c = Clinic(id="test-clinic", name="Test Clinic", timezone="America/Edmonton")
    db_session.add(c)
    db_session.commit()
    return c


def _hours(clinic_id, dow, open_at, close_at, lunch_start=None, lunch_end=None, closed=False):
    return ClinicOperatingHours(
        clinic_id=clinic_id, day_of_week=dow,
        open_at=open_at, close_at=close_at,
        lunch_start=lunch_start, lunch_end=lunch_end, is_closed=closed,
    )


def test_returns_single_interval_when_no_lunch(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0)))
    db_session.commit()
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert len(result.intervals) == 1
    start, end = result.intervals[0]
    assert start == TZ.localize(datetime(2026, 5, 25, 9, 0))
    assert end == TZ.localize(datetime(2026, 5, 25, 17, 0))


def test_carves_lunch_when_both_columns_set(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0),
                          lunch_start=time(12, 0), lunch_end=time(13, 0)))
    db_session.commit()
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert len(result.intervals) == 2
    assert result.intervals[0] == (
        TZ.localize(datetime(2026, 5, 25, 9, 0)),
        TZ.localize(datetime(2026, 5, 25, 12, 0)),
    )
    assert result.intervals[1] == (
        TZ.localize(datetime(2026, 5, 25, 13, 0)),
        TZ.localize(datetime(2026, 5, 25, 17, 0)),
    )


def test_ignores_lunch_when_only_one_column_set(db_session, clinic, caplog):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0),
                          lunch_start=time(12, 0), lunch_end=None))
    db_session.commit()
    caplog.set_level(logging.WARNING)
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert len(result.intervals) == 1  # no lunch carved
    assert "malformed lunch" in caplog.text.lower()


def test_returns_empty_when_no_operating_hours_row(db_session, clinic, caplog):
    # No ClinicOperatingHours rows for this weekday.
    caplog.set_level(logging.WARNING)
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert result.is_empty
    assert "no clinic_operating_hours" in caplog.text.lower()


def test_returns_empty_when_is_closed_true(db_session, clinic):
    db_session.add(_hours(clinic.id, 5, time(0, 0), time(0, 0), closed=True))
    db_session.commit()
    result = clinic_day_window(clinic.id, SAT, db_session, TZ)
    assert result.is_empty


def test_clinic_closure_overrides_operating_hours(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0)))
    db_session.add(ClinicClosure(
        clinic_id=clinic.id, start_date=MON, end_date=MON,
        kind="holiday", reason="Victoria Day",
    ))
    db_session.commit()
    result = clinic_day_window(clinic.id, MON, db_session, TZ)
    assert result.is_empty


def test_multi_day_closure_covers_all_days(db_session, clinic):
    db_session.add(_hours(clinic.id, 0, time(9, 0), time(17, 0)))  # Mon
    db_session.add(_hours(clinic.id, 1, time(9, 0), time(17, 0)))  # Tue
    db_session.add(ClinicClosure(
        clinic_id=clinic.id,
        start_date=date(2026, 5, 25), end_date=date(2026, 5, 26),
        kind="training", reason="staff training",
    ))
    db_session.commit()
    assert clinic_day_window(clinic.id, date(2026, 5, 25), db_session, TZ).is_empty
    assert clinic_day_window(clinic.id, date(2026, 5, 26), db_session, TZ).is_empty
    # Wednesday outside the closure range is still open (need hours row).
    db_session.add(_hours(clinic.id, 2, time(9, 0), time(17, 0)))
    db_session.commit()
    assert not clinic_day_window(clinic.id, date(2026, 5, 27), db_session, TZ).is_empty
