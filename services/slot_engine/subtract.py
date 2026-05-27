"""Subtractive layer: builds IntervalSets of unavailable time from
provider_busy_blocks, provider_time_off, and appointments."""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from typing import List, Tuple

import pytz
from sqlalchemy.orm import Session

from database.models import Appointment, AppointmentStatus, ProviderBusyBlock
from database.v1_1.models import ProviderTimeOff
from services.slot_engine.intervals import IntervalSet


_ACTIVE_STATUSES = [
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.PENDING_SYNC,
    AppointmentStatus.PENDING,
]


def _combine(d: date, t: time, tz: pytz.tzinfo.BaseTzInfo) -> datetime:
    return tz.localize(datetime.combine(d, t))


def _block_weekdays(block: ProviderBusyBlock) -> List[int]:
    """Read weekdays from the JSON column, falling back to legacy `weekday` int."""
    if block.weekdays:
        try:
            parsed = json.loads(block.weekdays)
            if isinstance(parsed, list):
                return [int(x) for x in parsed]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    if block.weekday is not None and block.specific_date is None:
        return [int(block.weekday)]
    return []


def busy_blocks_for(
    provider_id: int,
    clinic_id: str,
    target_date: date,
    tz: pytz.tzinfo.BaseTzInfo,
    db: Session,
) -> IntervalSet:
    """Return busy intervals from provider_busy_blocks that apply on target_date.

    Decision: when both a specific_date and a weekdays row would match
    target_date, the specific_date row wins (the recurring rule is suppressed
    for that day).
    """
    rows = (
        db.query(ProviderBusyBlock)
        .filter(
            ProviderBusyBlock.clinic_id == clinic_id,
            ProviderBusyBlock.provider_id == provider_id,
        )
        .all()
    )

    specific_pieces: List[Tuple[datetime, datetime]] = []
    recurring_pieces: List[Tuple[datetime, datetime]] = []

    for b in rows:
        if b.specific_date is not None:
            if b.specific_date == target_date:
                specific_pieces.append((
                    _combine(target_date, time(int(b.start_hour), int(b.start_minute)), tz),
                    _combine(target_date, time(int(b.end_hour), int(b.end_minute)), tz),
                ))
            continue
        # Recurring rule
        weekdays = _block_weekdays(b)
        if target_date.weekday() not in weekdays:
            continue
        if b.recurrence_until is not None and b.recurrence_until < target_date:
            continue
        recurring_pieces.append((
            _combine(target_date, time(int(b.start_hour), int(b.start_minute)), tz),
            _combine(target_date, time(int(b.end_hour), int(b.end_minute)), tz),
        ))

    pieces = specific_pieces if specific_pieces else recurring_pieces
    return IntervalSet(sorted(pieces))


def time_off_for(
    provider_id: int,
    clinic_id: str,
    target_date: date,
    tz: pytz.tzinfo.BaseTzInfo,
    db: Session,
) -> IntervalSet:
    """Return the intersection of provider_time_off rows with target_date.

    Multi-day PTO contributes [date 00:00, date 24:00) ∩ [start_at, end_at)
    per overlapping date.
    """
    day_start = _combine(target_date, time(0, 0), tz)
    day_end = day_start + timedelta(days=1)

    rows = (
        db.query(ProviderTimeOff)
        .filter(
            ProviderTimeOff.clinic_id == clinic_id,
            ProviderTimeOff.provider_id == provider_id,
            ProviderTimeOff.start_at < day_end,
            ProviderTimeOff.end_at > day_start,
        )
        .all()
    )

    pieces = []
    for r in rows:
        start_at = r.start_at if r.start_at.tzinfo else tz.localize(r.start_at)
        end_at = r.end_at if r.end_at.tzinfo else tz.localize(r.end_at)
        lo = max(day_start, start_at)
        hi = min(day_end, end_at)
        if lo < hi:
            pieces.append((lo, hi))
    return IntervalSet(sorted(pieces))


def appointments_for(
    provider_id: int,
    clinic_id: str,
    target_date: date,
    tz: pytz.tzinfo.BaseTzInfo,
    db: Session,
) -> IntervalSet:
    """Return busy intervals from active appointments overlapping target_date.

    Active = status in {SCHEDULED, CONFIRMED, PENDING_SYNC, PENDING}.
    Midnight-crossing appointments are clipped to [date 00:00, date 24:00).
    """
    day_start = _combine(target_date, time(0, 0), tz)
    day_end = day_start + timedelta(days=1)

    # Stored values are naive UTC (Postgres drops the offset on insert).
    # Convert the day-window bounds to naive UTC too so the SQL filter
    # compares apples to apples — comparing tz-aware bounds against a
    # naive column silently mis-matches and drops rows.
    from datetime import timezone as _tz
    day_start_utc = day_start.astimezone(_tz.utc).replace(tzinfo=None)
    day_end_utc = day_end.astimezone(_tz.utc).replace(tzinfo=None)

    rows = (
        db.query(Appointment)
        .filter(
            Appointment.clinic_id == clinic_id,
            Appointment.provider_id == provider_id,
            Appointment.status.in_(_ACTIVE_STATUSES),
            Appointment.start_time < day_end_utc,
            Appointment.end_time > day_start_utc,
        )
        .order_by(Appointment.start_time.asc())
        .all()
    )

    pieces = []
    for r in rows:
        # Naive values from the DB are really UTC — convert via UTC, not via
        # local-stamping which would shift bookings by the offset and break
        # conflict detection.
        st = r.start_time if r.start_time.tzinfo else r.start_time.replace(tzinfo=_tz.utc)
        et = r.end_time if r.end_time.tzinfo else r.end_time.replace(tzinfo=_tz.utc)
        lo = max(day_start, st.astimezone(tz))
        hi = min(day_end, et.astimezone(tz))
        if lo < hi:
            pieces.append((lo, hi))
    return IntervalSet(pieces)
