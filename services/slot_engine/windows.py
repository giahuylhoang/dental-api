"""Window builders: clinic day window (operating hours + closures + lunch)
and provider day window (narrowed by per-provider availability)."""
from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Set, Tuple

import pytz
from sqlalchemy.orm import Session

from database.models import ProviderAvailability
from database.v1_1.models import ClinicClosure, ClinicOperatingHours
from services.slot_engine.intervals import IntervalSet


logger = logging.getLogger("slot_engine.windows")

# Dedupe per-process: each (clinic_id, day_of_week) warning fires at most once.
_warned_missing_hours: Set[Tuple[str, int]] = set()
_warned_malformed_lunch: Set[Tuple[str, int]] = set()


def _combine(d: date, t: time, tz: pytz.tzinfo.BaseTzInfo) -> datetime:
    """Build a tz-aware datetime from a naive (date, time) pair."""
    return tz.localize(datetime.combine(d, t))


def clinic_day_window(
    clinic_id: str, target_date: date, db: Session, tz: pytz.tzinfo.BaseTzInfo
) -> IntervalSet:
    """Return the intervals when the clinic is potentially open on target_date.

    Decision matrix (see spec 2026-05-26-slot-engine-rewrite-design.md):
      - clinic_closures overlapping target_date -> empty
      - no clinic_operating_hours row for the weekday -> empty (fail closed) + WARN
      - is_closed=True -> empty
      - lunch_start + lunch_end both set -> carve [lunch_start, lunch_end)
      - only one of lunch_* set -> ignore lunch + WARN (malformed config)
    """
    # 1. Closures take precedence.
    closure = (
        db.query(ClinicClosure)
        .filter(
            ClinicClosure.clinic_id == clinic_id,
            ClinicClosure.start_date <= target_date,
        )
        .all()
    )
    for c in closure:
        end = c.end_date if c.end_date is not None else c.start_date
        if c.start_date <= target_date <= end:
            return IntervalSet([])

    # 2. Look up the per-weekday hours.
    dow = target_date.weekday()
    row = (
        db.query(ClinicOperatingHours)
        .filter(
            ClinicOperatingHours.clinic_id == clinic_id,
            ClinicOperatingHours.day_of_week == dow,
        )
        .one_or_none()
    )
    if row is None:
        key = (clinic_id, dow)
        if key not in _warned_missing_hours:
            _warned_missing_hours.add(key)
            logger.warning(
                "No clinic_operating_hours row for clinic=%s dow=%s; treating as closed.",
                clinic_id, dow,
            )
        return IntervalSet([])

    if row.is_closed:
        return IntervalSet([])

    # 3. Build the day window.
    window = IntervalSet.from_window(
        _combine(target_date, row.open_at, tz),
        _combine(target_date, row.close_at, tz),
    )

    # 4. Carve out lunch if both columns set; warn on one-sided config.
    has_lunch_start = row.lunch_start is not None
    has_lunch_end = row.lunch_end is not None
    if has_lunch_start and has_lunch_end:
        lunch = IntervalSet.from_window(
            _combine(target_date, row.lunch_start, tz),
            _combine(target_date, row.lunch_end, tz),
        )
        window = window.subtract(lunch)
    elif has_lunch_start != has_lunch_end:
        key = (clinic_id, dow)
        if key not in _warned_malformed_lunch:
            _warned_malformed_lunch.add(key)
            logger.warning(
                "Malformed lunch config for clinic=%s dow=%s (only one of "
                "lunch_start/lunch_end set); ignoring lunch.",
                clinic_id, dow,
            )

    return window
