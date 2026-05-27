"""Slot engine orchestrator.

Public surface:
  - get_available_slots(...)  — same signature as the legacy tools.slot_utils.
  - find_busy_block_overlap(...) — same signature, called from services/appointments.py.
  - resolve_providers(...) — helper exposed for testability.

Internals:
  Compose clinic_day_window → provider_day_window → subtract busy_blocks_for
  + time_off_for + appointments_for → chunk.into_slots, iterating dates × providers.
"""
from __future__ import annotations

import datetime as _dt
import logging
import warnings
from typing import Any, Dict, List, Optional

import pytz
from sqlalchemy.orm import Session

from database.models import Provider, ProviderBusyBlock
from services.slot_engine.chunk import into_slots
from services.slot_engine.intervals import IntervalSet
from services.slot_engine.subtract import (
    appointments_for,
    busy_blocks_for,
    time_off_for,
)
from services.slot_engine.windows import clinic_day_window, provider_day_window


logger = logging.getLogger("slot_engine.engine")

EDMONTON_TZ = pytz.timezone("America/Edmonton")


def resolve_providers(
    clinic_id: Optional[str],
    provider_id: Optional[int],
    provider_name: Optional[str],
    db: Session,
) -> List[Provider]:
    """Return active providers matching the filters.

    Precedence: provider_id > provider_name > all active.
    """
    q = db.query(Provider).filter(Provider.is_active == True)  # noqa: E712
    if clinic_id:
        q = q.filter(Provider.clinic_id == clinic_id)

    if provider_id is not None:
        match = q.filter(Provider.id == provider_id).first()
        return [match] if match else []
    if provider_name:
        match = q.filter(Provider.name.ilike(f"%{provider_name}%")).first()
        return [match] if match else []
    return q.order_by(Provider.id.asc()).all()


def _parse_dt(s: str, tz: pytz.tzinfo.BaseTzInfo) -> Optional[_dt.datetime]:
    try:
        d = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return tz.localize(d) if d.tzinfo is None else d.astimezone(tz)


def _date_range(start_dt: _dt.datetime, end_dt: _dt.datetime) -> List[_dt.date]:
    days: List[_dt.date] = []
    cursor = start_dt.date()
    last = end_dt.date()
    while cursor <= last:
        days.append(cursor)
        cursor = cursor + _dt.timedelta(days=1)
    return days


def _clinic_tz(db: Session, clinic_id: Optional[str], explicit: Optional[str]) -> pytz.tzinfo.BaseTzInfo:
    if explicit:
        return pytz.timezone(explicit)
    if clinic_id:
        from database.models import Clinic
        c = db.get(Clinic, clinic_id)
        if c and c.timezone:
            return pytz.timezone(c.timezone)
    return EDMONTON_TZ


def get_available_slots(
    db: Session,
    start_datetime: str,
    end_datetime: str,
    provider_id: Optional[int] = None,
    provider_name: Optional[str] = None,
    slot_minutes: int = 30,
    clinic_id: Optional[str] = None,
    timezone_str: Optional[str] = None,
    hour_start: Optional[int] = None,
    hour_end: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute available slots across the request window.

    Output shape preserved from legacy tools.slot_utils:
      - If provider_id or provider_name is given:
          {"provider": {"provider_id": int|None, "title": str|None}, "slots": [iso, ...]}
      - Otherwise:
          {"providers": [{"provider_id": int, "title": str, "slots": [iso, ...]}, ...]}

    `hour_start` / `hour_end` are accepted for backwards-compat but silently
    ignored — the new engine reads from clinic_operating_hours instead.
    """
    if hour_start is not None or hour_end is not None:
        warnings.warn(
            "hour_start/hour_end are deprecated and ignored by the slot engine; "
            "configure clinic_operating_hours instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    tz = _clinic_tz(db, clinic_id, timezone_str)

    start_dt = _parse_dt(start_datetime, tz)
    end_dt = _parse_dt(end_datetime, tz)
    if start_dt is None or end_dt is None or end_dt <= start_dt:
        # Preserve legacy behavior on parse failure: empty providers list.
        if provider_id is not None or provider_name is not None:
            return {"provider": {"provider_id": provider_id, "title": None}, "slots": []}
        return {"providers": []}

    if (end_dt - start_dt).days > 90:
        logger.warning(
            "Slot request spans %d days (clinic=%s); no hard cap.",
            (end_dt - start_dt).days, clinic_id,
        )

    providers = resolve_providers(clinic_id, provider_id, provider_name, db)
    if not providers and (provider_id is not None or provider_name is not None):
        return {"provider": {"provider_id": provider_id, "title": None}, "slots": []}

    request_window = IntervalSet.from_window(start_dt, end_dt)
    results: Dict[int, List[_dt.datetime]] = {p.id: [] for p in providers}

    for d in _date_range(start_dt, end_dt):
        daily = clinic_day_window(clinic_id, d, db, tz) if clinic_id else IntervalSet([])
        if daily.is_empty:
            continue
        for p in providers:
            win = provider_day_window(p.id, clinic_id, d, daily, db, tz)
            win = win.subtract(busy_blocks_for(p.id, clinic_id, d, tz, db))
            win = win.subtract(time_off_for(p.id, clinic_id, d, tz, db))
            win = win.subtract(appointments_for(p.id, clinic_id, d, tz, db))
            win = win.intersect(request_window)
            results[p.id].extend(into_slots(win, slot_minutes))

    if provider_id is not None or provider_name is not None:
        # Single provider response shape.
        p = providers[0] if providers else None
        return {
            "provider": {
                "provider_id": p.id if p else provider_id,
                "title": p.title if p else None,
            },
            "slots": [s.isoformat() for s in results.get(p.id, [])] if p else [],
        }

    return {
        "providers": [
            {
                "provider_id": p.id,
                "title": p.title,
                "slots": [s.isoformat() for s in results[p.id]],
            }
            for p in providers
        ]
    }


def find_busy_block_overlap(
    db: Session,
    clinic_id: str,
    provider_id: int,
    start_dt: _dt.datetime,
    end_dt: _dt.datetime,
    tz: pytz.tzinfo.BaseTzInfo,
) -> Optional[ProviderBusyBlock]:
    """Return the first ProviderBusyBlock that overlaps [start_dt, end_dt).

    Caller (services/appointments.py) uses the returned ORM row to populate
    a 409 error response. Returning None means the window is free of blocks.
    """
    start_dt = start_dt if start_dt.tzinfo else tz.localize(start_dt)
    end_dt = end_dt if end_dt.tzinfo else tz.localize(end_dt)
    request = IntervalSet.from_window(start_dt, end_dt)

    rows = (
        db.query(ProviderBusyBlock)
        .filter(
            ProviderBusyBlock.clinic_id == clinic_id,
            ProviderBusyBlock.provider_id == provider_id,
        )
        .all()
    )
    # Reuse busy_blocks_for per day: walk dates in the request window,
    # and on the first overlapping day return the row that matched.
    cursor = start_dt.date()
    last = end_dt.date()
    while cursor <= last:
        # Re-query per day so the "specific_date wins" precedence applies.
        blocks_intervals = busy_blocks_for(provider_id, clinic_id, cursor, tz, db)
        if not request.intersect(blocks_intervals).is_empty:
            # Find the row corresponding to the first overlapping interval.
            for r in rows:
                # Reconstruct the same intervals busy_blocks_for would emit
                # and check if any overlap the request on this date.
                day_blocks = busy_blocks_for(provider_id, clinic_id, cursor, tz, db)
                # If this row's date applies and overlaps, return it.
                row_applies = (
                    (r.specific_date is not None and r.specific_date == cursor)
                    or (
                        r.specific_date is None
                        and cursor.weekday()
                        in _row_weekdays(r)
                        and (r.recurrence_until is None or r.recurrence_until >= cursor)
                    )
                )
                if not row_applies:
                    continue
                rs = tz.localize(_dt.datetime.combine(
                    cursor, _dt.time(int(r.start_hour), int(r.start_minute))
                ))
                re_ = tz.localize(_dt.datetime.combine(
                    cursor, _dt.time(int(r.end_hour), int(r.end_minute))
                ))
                if not IntervalSet.from_window(rs, re_).intersect(request).is_empty:
                    return r
        cursor = cursor + _dt.timedelta(days=1)
    return None


def _row_weekdays(b: ProviderBusyBlock) -> List[int]:
    """Local copy of subtract._block_weekdays (avoids importing private)."""
    import json as _json
    if b.weekdays:
        try:
            parsed = _json.loads(b.weekdays)
            if isinstance(parsed, list):
                return [int(x) for x in parsed]
        except (_json.JSONDecodeError, ValueError, TypeError):
            pass
    if b.weekday is not None and b.specific_date is None:
        return [int(b.weekday)]
    return []
