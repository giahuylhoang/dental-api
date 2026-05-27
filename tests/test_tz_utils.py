"""Tests for clinic-timezone conversions.

Regression context: Postgres stores Appointment.start_time in a tz-naive
column. tz-aware writes are silently converted to UTC and the offset is
dropped, so reads come back naive-but-actually-UTC. The notification
renderer used to call ``tz.localize(naive_ts)`` which stamped the value AS
IF it were already clinic-local, producing SMS confirmations that were
~6 hours ahead of the real appointment time. These tests pin down the
correct behavior so the bug doesn't regress.
"""
from datetime import datetime, timezone

import pytest

from database.models import Clinic
from services.tz_utils import (
    format_clinic_local,
    to_clinic_local,
    to_clinic_local_iso,
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
