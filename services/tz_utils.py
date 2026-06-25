"""Single source of truth for clinic-timezone conversions.

We store appointment timestamps in Postgres as `timestamp without time zone`.
Postgres silently converts any tz-aware datetime to UTC on INSERT and drops
the offset. So every value we read back from the DB is naive-but-actually-UTC.

This module's job is to make sure every reader treats those values as UTC and
converts to the clinic's configured timezone (America/Edmonton by default)
before formatting or serializing them. Without this, SMS/email confirmations
and the v3 agent's "upcoming appointments" inject all rendered 6-7 hours
ahead of the actual local appointment time.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytz

from database.models import Clinic

DEFAULT_TZ = "America/Edmonton"


def _clinic_tz(clinic: Optional[Clinic]):
    name = (clinic.timezone if clinic else None) or DEFAULT_TZ
    return pytz.timezone(name)


def to_clinic_local(ts: datetime, clinic: Optional[Clinic]) -> datetime:
    """Return ts as a tz-aware datetime in the clinic's local timezone.

    Naive inputs are interpreted as UTC (matches how Postgres stores values
    written through SQLAlchemy's tz-naive DateTime column). Tz-aware inputs
    are converted to the clinic's tz."""
    tz = _clinic_tz(clinic)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(tz)


def to_clinic_local_iso(ts: Optional[datetime], clinic: Optional[Clinic]) -> Optional[str]:
    """ISO 8601 with clinic-local offset, e.g. '2026-05-27T09:30:00-06:00'.

    Use this for any datetime emitted over the wire — slot listings, the v3
    voice agent's appointment list, frontend payloads — so downstream
    consumers see the local wall-clock time in their parse step."""
    if ts is None:
        return None
    return to_clinic_local(ts, clinic).isoformat()


def to_storage_utc(ts: datetime) -> datetime:
    """Normalize a datetime to naive UTC for storage.

    Postgres `timestamp without time zone` columns silently do this on
    insert; SQLite (used in tests) does NOT, so writes that pass tz-aware
    values diverge between backends. Calling this on every write to
    Appointment.start_time / end_time pins both backends to the same
    representation and lets read-side TZ conversion be uniform."""
    if ts.tzinfo is None:
        return ts
    return ts.astimezone(timezone.utc).replace(tzinfo=None)


def to_storage_utc_clinic(ts: datetime, clinic: Optional[Clinic]) -> datetime:
    """Normalize a datetime to naive UTC for storage, interpreting any NAIVE
    input as clinic-local wall-clock time (the contract every CRM/web caller
    actually uses). Tz-aware inputs are converted from their own zone. This is
    the write-side inverse of to_clinic_local and the function all appointment
    write boundaries must call.

    pytz requires .localize() to attach a zone to a naive datetime (NOT
    replace(tzinfo=...), which picks the wrong historical offset)."""
    if ts.tzinfo is None:
        ts = _clinic_tz(clinic).localize(ts)
    return ts.astimezone(timezone.utc).replace(tzinfo=None)


def format_clinic_local(ts: datetime, clinic: Optional[Clinic]) -> tuple[str, str]:
    """Return (date_str, time_str) tuple ready for SMS/email templates."""
    local = to_clinic_local(ts, clinic)
    return local.strftime("%Y-%m-%d"), local.strftime("%I:%M %p")
