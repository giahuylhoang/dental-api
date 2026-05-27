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
