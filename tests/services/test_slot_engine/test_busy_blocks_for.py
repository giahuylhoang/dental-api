"""Unit tests for subtract.busy_blocks_for."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import Clinic, Provider, ProviderBusyBlock
from services.slot_engine.subtract import busy_blocks_for


TZ = pytz.timezone("America/Edmonton")
WED = date(2026, 5, 27)  # Wednesday, weekday=2
THU = date(2026, 5, 28)  # Thursday


@pytest.fixture
def setup(db_session):
    c = Clinic(id="c1", name="C1", timezone="America/Edmonton")
    p = Provider(clinic_id="c1", name="Soheil", title="Denturist", is_active=True)
    db_session.add_all([c, p])
    db_session.commit()
    return c, p


def test_no_blocks_returns_empty(db_session, setup):
    _, p = setup
    assert busy_blocks_for(p.id, "c1", WED, TZ, db_session).is_empty


def test_recurring_weekly_block_applies_on_matching_weekday(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekdays="[0,2]",
        start_hour=12, start_minute=0, end_hour=13, end_minute=0,
        label="Lunch",
    ))
    db_session.commit()
    # WED weekday=2 matches
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 12, 0)),
        TZ.localize(datetime(2026, 5, 27, 13, 0)),
    )]
    # THU weekday=3 does NOT match
    assert busy_blocks_for(p.id, "c1", THU, TZ, db_session).is_empty


def test_specific_date_one_off(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, specific_date=WED,
        start_hour=14, start_minute=0, end_hour=16, end_minute=0,
        label="Dental conference",
    ))
    db_session.commit()
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 14, 0)),
        TZ.localize(datetime(2026, 5, 27, 16, 0)),
    )]
    # Other dates unaffected
    assert busy_blocks_for(p.id, "c1", THU, TZ, db_session).is_empty


def test_legacy_weekday_field_treated_as_recurring(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekday=2,
        start_hour=15, start_minute=0, end_hour=16, end_minute=0,
    ))
    db_session.commit()
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 15, 0)),
        TZ.localize(datetime(2026, 5, 27, 16, 0)),
    )]


def test_expired_recurrence_until_does_not_apply(db_session, setup):
    _, p = setup
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekdays="[2]",
        start_hour=12, start_minute=0, end_hour=13, end_minute=0,
        recurrence_until=date(2026, 4, 1),  # past
    ))
    db_session.commit()
    assert busy_blocks_for(p.id, "c1", WED, TZ, db_session).is_empty


def test_specific_date_wins_over_weekdays_on_same_day(db_session, setup):
    """Per spec: when both specific_date and weekdays would match on the
    same day, the specific_date row contributes; the recurring row is
    suppressed for that day."""
    _, p = setup
    # Recurring Wed lunch
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, weekdays="[2]",
        start_hour=12, start_minute=0, end_hour=13, end_minute=0,
        label="Lunch",
    ))
    # One-off block on the same Wed (different time)
    db_session.add(ProviderBusyBlock(
        clinic_id="c1", provider_id=p.id, specific_date=WED,
        start_hour=10, start_minute=0, end_hour=11, end_minute=0,
        label="Conference",
    ))
    db_session.commit()
    result = busy_blocks_for(p.id, "c1", WED, TZ, db_session)
    # Only the specific_date row contributes.
    assert result.intervals == [(
        TZ.localize(datetime(2026, 5, 27, 10, 0)),
        TZ.localize(datetime(2026, 5, 27, 11, 0)),
    )]
