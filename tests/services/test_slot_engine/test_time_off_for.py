"""Unit tests for subtract.time_off_for."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Clinic, Provider
from database.v1_1.models import ProviderTimeOff
from services.slot_engine.subtract import time_off_for


TZ = pytz.timezone("America/Edmonton")
MON = date(2026, 5, 25)
TUE = date(2026, 5, 26)
WED = date(2026, 5, 27)


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Nadeem", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    return c, p


def test_no_time_off_returns_empty(db_session, setup):
    _, p = setup
    assert time_off_for(p.id, "c1", MON, TZ, db_session).is_empty


def test_full_day_off(db_session, setup):
    _, p = setup
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 5, 25, 0, 0)),
        end_at=TZ.localize(datetime(2026, 5, 26, 0, 0)),
        reason="vacation",
    ))
    db_session.commit()
    result = time_off_for(p.id, "c1", MON, TZ, db_session)
    # Whole day Mon covered.
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 0, 0)),
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
    )]


def test_partial_afternoon_off(db_session, setup):
    _, p = setup
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 5, 25, 13, 0)),
        end_at=TZ.localize(datetime(2026, 5, 25, 17, 0)),
        reason="admin",
    ))
    db_session.commit()
    result = time_off_for(p.id, "c1", MON, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 13, 0)),
        TZ.localize(datetime(2026, 5, 25, 17, 0)),
    )]


def test_multi_day_pto_contributes_on_each_day(db_session, setup):
    _, p = setup
    # Mon morning through Wed end of day
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 5, 25, 10, 0)),
        end_at=TZ.localize(datetime(2026, 5, 27, 18, 0)),
        reason="vacation",
    ))
    db_session.commit()
    # Mon: from 10:00 to end of day
    mon_r = time_off_for(p.id, "c1", MON, TZ, db_session)
    assert mon_r.intervals == [(
        TZ.localize(datetime(2026, 5, 25, 10, 0)),
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
    )]
    # Tue: full day
    tue_r = time_off_for(p.id, "c1", TUE, TZ, db_session)
    assert tue_r.intervals == [(
        TZ.localize(datetime(2026, 5, 26, 0, 0)),
        TZ.localize(datetime(2026, 5, 27, 0, 0)),
    )]
    # Wed: start of day to 18:00
    wed_r = time_off_for(p.id, "c1", WED, TZ, db_session)
    assert wed_r.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 0, 0)),
        TZ.localize(datetime(2026, 5, 27, 18, 0)),
    )]


def test_pto_in_different_week_does_not_apply(db_session, setup):
    _, p = setup
    db_session.add(ProviderTimeOff(
        clinic_id="c1", provider_id=p.id,
        start_at=TZ.localize(datetime(2026, 6, 1, 0, 0)),
        end_at=TZ.localize(datetime(2026, 6, 8, 0, 0)),
        reason="vacation",
    ))
    db_session.commit()
    assert time_off_for(p.id, "c1", MON, TZ, db_session).is_empty
