"""Unit tests for windows.provider_day_window."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Clinic, Provider, ProviderAvailability
from services.slot_engine.intervals import IntervalSet
from services.slot_engine.windows import provider_day_window


TZ = pytz.timezone("America/Edmonton")
WED = date(2026, 5, 27)


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    return c, p


def _daily():
    """Clinic open Wed 9–17."""
    return IntervalSet.from_window(
        TZ.localize(datetime(2026, 5, 27, 9, 0)),
        TZ.localize(datetime(2026, 5, 27, 17, 0)),
    )


def test_no_availability_rows_returns_daily_window_unchanged(db_session, setup):
    _, p = setup
    daily = _daily()
    result = provider_day_window(p.id, "c1", WED, daily, db_session, TZ)
    assert result.intervals == daily.intervals


def test_availability_narrows_to_provider_window(db_session, setup):
    _, p = setup
    # Soheil Wed: 9–12 only (half day)
    db_session.add(ProviderAvailability(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=9, start_minute=0, end_hour=12, end_minute=0,
    ))
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, _daily(), db_session, TZ)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 9, 0)),
        TZ.localize(datetime(2026, 5, 27, 12, 0)),
    )]


def test_split_shift_unions_multiple_rows(db_session, setup):
    _, p = setup
    # Two windows same weekday: 9–11 and 14–17.
    db_session.add_all([
        ProviderAvailability(clinic_id="c1", provider_id=p.id, weekday=2,
                             start_hour=9, start_minute=0, end_hour=11, end_minute=0),
        ProviderAvailability(clinic_id="c1", provider_id=p.id, weekday=2,
                             start_hour=14, start_minute=0, end_hour=17, end_minute=0),
    ])
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, _daily(), db_session, TZ)
    assert result.intervals == [
        (TZ.localize(datetime(2026, 5, 27, 9, 0)),  TZ.localize(datetime(2026, 5, 27, 11, 0))),
        (TZ.localize(datetime(2026, 5, 27, 14, 0)), TZ.localize(datetime(2026, 5, 27, 17, 0))),
    ]


def test_availability_extending_past_clinic_hours_is_clipped(db_session, setup):
    _, p = setup
    # Provider says 8–19, clinic only open 9–17.
    db_session.add(ProviderAvailability(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=8, start_minute=0, end_hour=19, end_minute=0,
    ))
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, _daily(), db_session, TZ)
    # Clipped to clinic window.
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 9, 0)),
        TZ.localize(datetime(2026, 5, 27, 17, 0)),
    )]


def test_empty_daily_window_returns_empty(db_session, setup):
    _, p = setup
    db_session.add(ProviderAvailability(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=9, start_minute=0, end_hour=17, end_minute=0,
    ))
    db_session.commit()
    result = provider_day_window(p.id, "c1", WED, IntervalSet([]), db_session, TZ)
    assert result.is_empty
