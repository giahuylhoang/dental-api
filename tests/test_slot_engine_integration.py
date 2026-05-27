"""End-to-end integration tests for the slot engine, mirroring the
Market Mall denture clinic schedule from the rewrite spec."""
from datetime import date, datetime, time

import pytest
import pytz

from database.models import (
    Appointment, AppointmentStatus,
    Clinic, Patient, Provider, ProviderAvailability,
)
from database.v1_1.models import ClinicOperatingHours, ProviderTimeOff
from services.slot_engine import get_available_slots


TZ = pytz.timezone("America/Edmonton")

# 2026-05-25 is a Monday in our test fixture.
MON = "2026-05-25T09:00:00-06:00"
SUN_END = "2026-05-31T23:59:00-06:00"
WED_START = "2026-05-27T09:00:00-06:00"
WED_END = "2026-05-27T18:00:00-06:00"
FRI_START = "2026-05-29T09:00:00-06:00"
FRI_END = "2026-05-29T19:00:00-06:00"


@pytest.fixture
def mm(db_session):
    """Seed Market Mall fixture: clinic + hours + 2 providers + availability."""
    c = Clinic(id="mm", name="Market Mall", timezone="America/Edmonton")
    db_session.add(c)
    db_session.flush()
    # Clinic hours: Mon-Thu 9-17, Fri 9-18:30, Sat/Sun closed.
    hours = [
        (0, time(9, 0), time(17, 0), False),
        (1, time(9, 0), time(17, 0), False),
        (2, time(9, 0), time(17, 0), False),
        (3, time(9, 0), time(17, 0), False),
        (4, time(9, 0), time(18, 30), False),
        (5, time(0, 0), time(0, 0), True),
        (6, time(0, 0), time(0, 0), True),
    ]
    for dow, o, cl, closed in hours:
        db_session.add(ClinicOperatingHours(
            clinic_id="mm", day_of_week=dow, open_at=o, close_at=cl, is_closed=closed,
        ))
    soheil = Provider(clinic_id="mm", name="Soheil", title="Denturist", is_active=True)
    nadeem = Provider(clinic_id="mm", name="Nadeem", title="Denturist", is_active=True)
    db_session.add_all([soheil, nadeem])
    # Patient needed for any appointment created in tests below.
    db_session.add(Patient(id="pat-mm", first_name="Test", last_name="Patient", clinic_id="mm"))
    db_session.flush()
    # Soheil: Tue 9-17, Wed 9-12, Fri 15-18:30
    db_session.add_all([
        ProviderAvailability(clinic_id="mm", provider_id=soheil.id, weekday=1,
                             start_hour=9, start_minute=0, end_hour=17, end_minute=0),
        ProviderAvailability(clinic_id="mm", provider_id=soheil.id, weekday=2,
                             start_hour=9, start_minute=0, end_hour=12, end_minute=0),
        ProviderAvailability(clinic_id="mm", provider_id=soheil.id, weekday=4,
                             start_hour=15, start_minute=0, end_hour=18, end_minute=30),
    ])
    # Nadeem: Mon-Thu 9-17, Fri 9-12
    for dow in (0, 1, 2, 3):
        db_session.add(ProviderAvailability(
            clinic_id="mm", provider_id=nadeem.id, weekday=dow,
            start_hour=9, start_minute=0, end_hour=17, end_minute=0,
        ))
    db_session.add(ProviderAvailability(
        clinic_id="mm", provider_id=nadeem.id, weekday=4,
        start_hour=9, start_minute=0, end_hour=12, end_minute=0,
    ))
    db_session.commit()
    return {"clinic_id": "mm", "soheil": soheil.id, "nadeem": nadeem.id}


def _slots(result, provider_id):
    """Find slots for a provider in the multi-provider response."""
    for p in result["providers"]:
        if p["provider_id"] == provider_id:
            return p["slots"]
    return []


def test_soheil_monday_falls_through_to_clinic_hours(db_session, mm):
    """Soheil has provider_availability rows for Tue/Wed/Fri but none for Mon.
    Per spec Decision C ('no rows for weekday = match clinic hours'), Soheil
    is treated as available during full clinic hours on Monday. The plan's
    original assertion that Mon was empty contradicted the helper contract;
    the helper-level test test_no_availability_rows_returns_daily_window_unchanged
    is the canonical statement of this rule."""
    out = get_available_slots(
        db_session, MON, SUN_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["soheil"],
    )
    mon_slots = [s for s in out["slots"] if s.startswith("2026-05-25")]
    # Clinic open Mon 9-17; Soheil falls through to clinic hours = 16 slots.
    assert len(mon_slots) == 16
    assert mon_slots[0] == "2026-05-25T09:00:00-06:00"
    assert mon_slots[-1] == "2026-05-25T16:30:00-06:00"


def test_soheil_wednesday_morning_only(db_session, mm):
    out = get_available_slots(
        db_session, WED_START, WED_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["soheil"],
    )
    # 9:00 through 11:30 inclusive = 6 slots (last is 11:30+30=12:00 = end).
    assert out["slots"] == [
        "2026-05-27T09:00:00-06:00",
        "2026-05-27T09:30:00-06:00",
        "2026-05-27T10:00:00-06:00",
        "2026-05-27T10:30:00-06:00",
        "2026-05-27T11:00:00-06:00",
        "2026-05-27T11:30:00-06:00",
    ]


def test_soheil_friday_evening_clipped_to_clinic_close(db_session, mm):
    out = get_available_slots(
        db_session, FRI_START, FRI_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["soheil"],
    )
    # Soheil 15:00-18:30, clinic closes 18:30 → 15:00, 15:30, 16:00, 16:30,
    # 17:00, 17:30, 18:00 (18:00+30=18:30 = end, included)
    assert out["slots"] == [
        "2026-05-29T15:00:00-06:00",
        "2026-05-29T15:30:00-06:00",
        "2026-05-29T16:00:00-06:00",
        "2026-05-29T16:30:00-06:00",
        "2026-05-29T17:00:00-06:00",
        "2026-05-29T17:30:00-06:00",
        "2026-05-29T18:00:00-06:00",
    ]


def test_nadeem_friday_morning_only(db_session, mm):
    out = get_available_slots(
        db_session, FRI_START, FRI_END, slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["nadeem"],
    )
    # 9:00 through 11:30 inclusive.
    assert out["slots"] == [
        "2026-05-29T09:00:00-06:00",
        "2026-05-29T09:30:00-06:00",
        "2026-05-29T10:00:00-06:00",
        "2026-05-29T10:30:00-06:00",
        "2026-05-29T11:00:00-06:00",
        "2026-05-29T11:30:00-06:00",
    ]


def test_saturday_and_sunday_return_no_slots_for_any_provider(db_session, mm):
    out = get_available_slots(
        db_session,
        "2026-05-30T00:00:00-06:00", "2026-06-01T00:00:00-06:00",
        slot_minutes=30, clinic_id=mm["clinic_id"],
    )
    for p in out["providers"]:
        assert p["slots"] == []


def test_existing_appointment_carves_out_those_slots(db_session, mm):
    # Postgres prod normalizes tz-aware writes to naive UTC. Mirror that on
    # SQLite so the test exercises the same read-side TZ conversion that
    # services/slot_engine/subtract.py performs.
    _s = TZ.localize(datetime(2026, 5, 25, 10, 0)).astimezone(pytz.utc).replace(tzinfo=None)
    _e = TZ.localize(datetime(2026, 5, 25, 11, 0)).astimezone(pytz.utc).replace(tzinfo=None)
    db_session.add(Appointment(
        clinic_id="mm", patient_id="pat-mm", provider_id=mm["nadeem"],
        start_time=_s, end_time=_e,
        status=AppointmentStatus.SCHEDULED, reason_note="t",
    ))
    db_session.commit()
    out = get_available_slots(
        db_session, MON, "2026-05-25T17:00:00-06:00", slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["nadeem"],
    )
    # 10:00 and 10:30 should be missing.
    assert "2026-05-25T10:00:00-06:00" not in out["slots"]
    assert "2026-05-25T10:30:00-06:00" not in out["slots"]
    # But 11:00 should be present.
    assert "2026-05-25T11:00:00-06:00" in out["slots"]


def test_multi_day_time_off_blocks_all_overlapping_days(db_session, mm):
    db_session.add(ProviderTimeOff(
        clinic_id="mm", provider_id=mm["nadeem"],
        start_at=TZ.localize(datetime(2026, 5, 25, 0, 0)),
        end_at=TZ.localize(datetime(2026, 5, 28, 0, 0)),  # off Mon-Wed inclusive
        reason="vacation",
    ))
    db_session.commit()
    out = get_available_slots(
        db_session, MON, "2026-05-28T17:00:00-06:00", slot_minutes=30,
        clinic_id=mm["clinic_id"], provider_id=mm["nadeem"],
    )
    # No slots Mon, Tue, Wed.
    for d in ("2026-05-25", "2026-05-26", "2026-05-27"):
        assert not any(s.startswith(d) for s in out["slots"]), f"slots leaked on {d}"
    # Thu slots should be present.
    assert any(s.startswith("2026-05-28") for s in out["slots"])


def test_no_clinic_operating_hours_returns_empty(db_session):
    c = Clinic(id="empty", name="Empty", timezone="America/Edmonton")
    db_session.add(c)
    db_session.flush()
    p = Provider(clinic_id="empty", name="X", title="Denturist", is_active=True)
    db_session.add(p)
    db_session.commit()
    out = get_available_slots(
        db_session, MON, SUN_END, slot_minutes=30,
        clinic_id="empty", provider_id=p.id,
    )
    assert out["slots"] == []


def test_no_providers_returns_empty_providers_list(db_session):
    c = Clinic(id="noprov", name="No Providers", timezone="America/Edmonton")
    db_session.add(c)
    db_session.commit()
    out = get_available_slots(
        db_session, MON, SUN_END, slot_minutes=30, clinic_id="noprov",
    )
    assert out == {"providers": []}
