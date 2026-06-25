"""Tests for clinic-timezone conversions.

Regression context: Postgres stores Appointment.start_time in a tz-naive
column. tz-aware writes are silently converted to UTC and the offset is
dropped, so reads come back naive-but-actually-UTC. The notification
renderer used to call ``tz.localize(naive_ts)`` which stamped the value AS
IF it were already clinic-local, producing SMS confirmations that were
~6 hours ahead of the real appointment time. These tests pin down the
correct behavior so the bug doesn't regress.
"""
from datetime import datetime, timedelta, timezone

import pytest

from database.models import Clinic
from services.tz_utils import (
    format_clinic_local,
    to_clinic_local,
    to_clinic_local_iso,
    to_storage_utc_clinic,
)


@pytest.fixture
def edmonton_clinic():
    """A clinic configured for the canonical Calgary/Edmonton timezone."""
    return Clinic(id="x", name="Test", timezone="America/Edmonton")


def test_naive_datetime_is_treated_as_utc(edmonton_clinic):
    """The DB returns naive datetimes that are really UTC — convert as such."""
    # 15:30 UTC == 09:30 Calgary in summer (MDT, -06:00).
    stored = datetime(2026, 5, 27, 15, 30)  # naive
    local = to_clinic_local(stored, edmonton_clinic)
    assert local.hour == 9
    assert local.minute == 30
    assert local.strftime("%Z") == "MDT"


def test_aware_datetime_converted_to_clinic(edmonton_clinic):
    """Tz-aware inputs already carry their offset — just convert."""
    stored = datetime(2026, 5, 27, 15, 30, tzinfo=timezone.utc)
    local = to_clinic_local(stored, edmonton_clinic)
    assert local.hour == 9
    assert local.minute == 30


def test_format_returns_calgary_local_strings(edmonton_clinic):
    """SMS template needs (date_str, time_str) — both in clinic-local."""
    stored = datetime(2026, 5, 27, 15, 30)
    date_str, time_str = format_clinic_local(stored, edmonton_clinic)
    assert date_str == "2026-05-27"
    assert time_str == "09:30 AM"


def test_iso_has_clinic_offset(edmonton_clinic):
    """Wire-format ISO has the clinic offset attached so downstream parsers
    (v3 agent, CRM frontend) render local time correctly without a second
    conversion step."""
    stored = datetime(2026, 5, 27, 15, 30)
    iso = to_clinic_local_iso(stored, edmonton_clinic)
    assert iso == "2026-05-27T09:30:00-06:00"


def test_winter_offset_is_mst(edmonton_clinic):
    """DST sanity — January should be UTC-7 (MST), not -6."""
    stored = datetime(2026, 1, 15, 16, 30)  # 16:30 UTC == 09:30 MST
    local = to_clinic_local(stored, edmonton_clinic)
    assert local.hour == 9
    assert local.strftime("%Z") == "MST"


def test_default_tz_when_clinic_has_none(edmonton_clinic):
    """Clinic without a timezone field falls back to America/Edmonton."""
    c = Clinic(id="x", name="Test", timezone=None)
    local = to_clinic_local(datetime(2026, 5, 27, 15, 30), c)
    assert local.hour == 9


def test_none_iso_passthrough(edmonton_clinic):
    """None in → None out, never an exception."""
    assert to_clinic_local_iso(None, edmonton_clinic) is None


# ---------------------------------------------------------------------------
# to_storage_utc_clinic — the write-side inverse of to_clinic_local.
# Naive input is interpreted as clinic-local wall-clock; we localize to the
# clinic tz then convert to naive UTC for storage. DST-aware.
# ---------------------------------------------------------------------------


def test_storage_utc_clinic_summer_localizes_to_mdt(edmonton_clinic):
    """Naive 14:00 clinic-local in summer (MDT, -06:00) → 20:00 naive UTC."""
    result = to_storage_utc_clinic(datetime(2026, 6, 25, 14, 0), edmonton_clinic)
    assert result == datetime(2026, 6, 25, 20, 0)
    assert result.tzinfo is None


def test_storage_utc_clinic_winter_localizes_to_mst(edmonton_clinic):
    """Naive 09:00 clinic-local in winter (MST, -07:00) → 16:00 naive UTC."""
    result = to_storage_utc_clinic(datetime(2026, 12, 25, 9, 0), edmonton_clinic)
    assert result == datetime(2026, 12, 25, 16, 0)
    assert result.tzinfo is None


def test_storage_utc_clinic_aware_input_unchanged_semantics(edmonton_clinic):
    """Tz-aware input is converted from its own offset; clinic is irrelevant."""
    aware = datetime(2026, 6, 25, 14, 0, tzinfo=timezone(timedelta(hours=-6)))
    result = to_storage_utc_clinic(aware, edmonton_clinic)
    assert result == datetime(2026, 6, 25, 20, 0)
    assert result.tzinfo is None


def test_storage_utc_clinic_none_clinic_falls_back_to_default():
    """clinic=None uses DEFAULT_TZ (America/Edmonton)."""
    result = to_storage_utc_clinic(datetime(2026, 6, 25, 14, 0), None)
    assert result == datetime(2026, 6, 25, 20, 0)


def test_storage_utc_clinic_non_edmonton_zone():
    """A Vancouver clinic (same offset as Edmonton in summer here is -07:00 PDT)
    localizes to its own zone, not Edmonton."""
    vancouver = Clinic(id="v", name="V", timezone="America/Vancouver")
    # 14:00 Vancouver in summer is PDT (-07:00) → 21:00 UTC.
    result = to_storage_utc_clinic(datetime(2026, 6, 25, 14, 0), vancouver)
    assert result == datetime(2026, 6, 25, 21, 0)


def test_storage_utc_clinic_is_inverse_of_to_clinic_local(edmonton_clinic):
    """Round-trip: clinic-local wall-clock → storage UTC → clinic-local."""
    wall = datetime(2026, 6, 25, 14, 0)
    stored = to_storage_utc_clinic(wall, edmonton_clinic)
    back = to_clinic_local(stored, edmonton_clinic)
    assert (back.year, back.month, back.day, back.hour, back.minute) == (
        2026, 6, 25, 14, 0,
    )
