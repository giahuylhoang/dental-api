"""
DB-based slot availability logic.

Computes available appointment slots from the database instead of Google Calendar.
Supports generic providers (doctor, assistant, etc.).
"""

import datetime
import json
import os
from typing import Dict, List, Optional, Tuple

import pytz
from sqlalchemy.orm import Session

from database.models import Appointment, AppointmentStatus, Provider, ProviderBusyBlock


def _parse_block_weekdays(block: ProviderBusyBlock) -> List[int]:
    """Return the weekdays a recurring block applies to, normalized to a list.

    Reads the v2 JSON-encoded `weekdays` column and falls back to the legacy
    single-day `weekday` field for rows written before the schema upgrade.
    Returns an empty list when the block is a one-off (`specific_date` set).
    """
    raw = getattr(block, "weekdays", None)
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [int(x) for x in parsed]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    legacy = getattr(block, "weekday", None)
    if legacy is not None and getattr(block, "specific_date", None) is None:
        return [int(legacy)]
    return []


def _block_applies_on(block: ProviderBusyBlock, day: datetime.date) -> bool:
    """True if this busy block covers calendar day `day`.

    A block applies when either:
      - it's a one-off and `specific_date == day`, or
      - it's a recurring rule, `day.weekday()` is in its weekday set, and the
        recurrence has not expired (`recurrence_until` is None or >= day).
    """
    if getattr(block, "specific_date", None) is not None:
        return block.specific_date == day
    weekdays = _parse_block_weekdays(block)
    if not weekdays:
        return False
    if day.weekday() not in weekdays:
        return False
    end = getattr(block, "recurrence_until", None)
    if end is not None and end < day:
        return False
    return True

EDMONTON_TZ = pytz.timezone("America/Edmonton")


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
) -> Dict[str, object]:
    """
    Compute available appointment slots from the database.

    When `provider_id` is provided:
      - return {"provider": {"provider_id": ..., "title": ...}, "slots": [...]}
    When `provider_id` is omitted:
      - return {"providers": [{"provider_id": ..., "title": ..., "slots": [...]}, ...]}
    """

    # Parse datetimes
    try:
        start_dt = datetime.datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
        end_dt = datetime.datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return {"providers": []}

    # Timezone from clinic or env
    tz = pytz.timezone(timezone_str) if timezone_str else EDMONTON_TZ
    if start_dt.tzinfo is None:
        start_dt = tz.localize(start_dt)
    else:
        start_dt = start_dt.astimezone(tz)
    if end_dt.tzinfo is None:
        end_dt = tz.localize(end_dt)
    else:
        end_dt = end_dt.astimezone(tz)

    # Working hours from clinic or env
    h_start = hour_start if hour_start is not None else int(os.getenv("WORKING_HOUR_START", "9"))
    h_end = hour_end if hour_end is not None else int(os.getenv("WORKING_HOUR_END", "17"))

    active_statuses = [
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.PENDING_SYNC,
        AppointmentStatus.PENDING,
    ]

    def day_start(dt: datetime.datetime) -> datetime.datetime:
        d = dt.replace(hour=h_start, minute=0, second=0, microsecond=0)
        if d.tzinfo is None:
            return tz.localize(d)
        return d

    def day_end(dt: datetime.datetime) -> datetime.datetime:
        d = dt.replace(hour=h_end, minute=0, second=0, microsecond=0)
        if d.tzinfo is None:
            return tz.localize(d)
        return d

    slot_delta = datetime.timedelta(minutes=slot_minutes)

    def _iter_busy_intervals_for_dt(
        provider_blocks: List[ProviderBusyBlock], dt: datetime.datetime
    ) -> List[tuple]:
        """Return tz-aware (start, end) intervals for blocks that cover `dt.date()`."""
        day = dt.date()
        intervals: List[tuple] = []
        for b in provider_blocks:
            if not _block_applies_on(b, day):
                continue
            b_start = tz.localize(datetime.datetime.combine(
                day, datetime.time(int(b.start_hour), int(b.start_minute), 0)
            ))
            b_end = tz.localize(datetime.datetime.combine(
                day, datetime.time(int(b.end_hour), int(b.end_minute), 0)
            ))
            intervals.append((b_start, b_end))
        return intervals

    def compute_slots_for_busy(busy_intervals: List[tuple], provider_blocks: List[ProviderBusyBlock]) -> List[str]:
        available: List[str] = []
        current = max(start_dt, day_start(start_dt))

        while current < end_dt:
            day_e = day_end(current)
            if current >= day_e:
                next_date = current.date() + datetime.timedelta(days=1)
                current = tz.localize(datetime.datetime.combine(next_date, datetime.time(h_start, 0, 0)))
                continue

            slot_end = current + slot_delta
            if slot_end > day_e or slot_end > end_dt:
                next_date = current.date() + datetime.timedelta(days=1)
                current = tz.localize(datetime.datetime.combine(next_date, datetime.time(h_start, 0, 0)))
                continue

            is_free = True
            # Appointments-based busy intervals (absolute)
            for b_start, b_end in busy_intervals:
                if max(current, b_start) < min(slot_end, b_end):
                    is_free = False
                    break
            # Provider busy blocks (recurring weekday rules + specific-date one-offs)
            if is_free:
                for b_start, b_end in _iter_busy_intervals_for_dt(provider_blocks, current):
                    if max(current, b_start) < min(slot_end, b_end):
                        is_free = False
                        break
            if is_free:
                available.append(current.isoformat())

            current = current + slot_delta

        return available

    # Determine which providers to compute
    providers_q = db.query(Provider).filter(Provider.is_active == True)
    if clinic_id:
        providers_q = providers_q.filter(Provider.clinic_id == clinic_id)

    resolved_single_provider: Optional[Provider] = None
    if provider_id is not None:
        resolved_single_provider = providers_q.filter(Provider.id == provider_id).first()
    elif provider_name:
        resolved_single_provider = providers_q.filter(Provider.name.ilike(f"%{provider_name}%")).first()

    if resolved_single_provider is not None:
        providers = [resolved_single_provider]
    else:
        providers = providers_q.all()

    # If caller requested a specific provider and it doesn't exist, return empty for that provider.
    if provider_id is not None and resolved_single_provider is None and provider_name is None:
        return {"provider": {"provider_id": provider_id, "title": None}, "slots": []}

    results: List[Dict[str, object]] = []
    for provider in providers:
        # Build busy intervals for this provider.
        appointments = db.query(Appointment).filter(
            Appointment.status.in_(active_statuses),
            Appointment.start_time < end_dt,
            Appointment.end_time > start_dt,
        )
        if clinic_id:
            appointments = appointments.filter(Appointment.clinic_id == clinic_id)
        appointments = appointments.filter(Appointment.provider_id == provider.id).all()

        busy_intervals: List[tuple] = []
        for apt in appointments:
            apt_start = apt.start_time
            apt_end = apt.end_time
            if apt_start.tzinfo is None:
                apt_start = tz.localize(apt_start)
            else:
                apt_start = apt_start.astimezone(tz)
            if apt_end.tzinfo is None:
                apt_end = tz.localize(apt_end)
            else:
                apt_end = apt_end.astimezone(tz)
            busy_intervals.append((apt_start, apt_end))

        # Provider busy blocks (recurring + one-off)
        blocks_q = db.query(ProviderBusyBlock).filter(ProviderBusyBlock.provider_id == provider.id)
        if clinic_id:
            blocks_q = blocks_q.filter(ProviderBusyBlock.clinic_id == clinic_id)
        provider_blocks = blocks_q.all()

        slots = compute_slots_for_busy(busy_intervals, provider_blocks)
        results.append(
            {
                "provider_id": provider.id,
                "title": provider.title,
                "slots": slots,
            }
        )

    if provider_id is not None or provider_name is not None:
        # For name lookup we treat the single provider case similarly.
        single = results[0] if results else {"provider_id": provider_id, "title": None, "slots": []}
        return {"provider": {"provider_id": single["provider_id"], "title": single["title"]}, "slots": single["slots"]}

    return {"providers": results}


def find_busy_block_overlap(
    db: Session,
    clinic_id: str,
    provider_id: int,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    tz: pytz.tzinfo.BaseTzInfo,
) -> Optional[ProviderBusyBlock]:
    """Return the first ProviderBusyBlock that overlaps [start_dt, end_dt) for
    this provider in this clinic, or None if the window is free of busy blocks.

    Handles both recurring rules (`weekdays`, optional `recurrence_until`) and
    specific-date one-offs (`specific_date`). Cross-midnight requests are not
    supported by the schema — the lookup keys on `start_dt.date()`.
    """
    if start_dt.tzinfo is None:
        start_dt = tz.localize(start_dt)
    else:
        start_dt = start_dt.astimezone(tz)
    if end_dt.tzinfo is None:
        end_dt = tz.localize(end_dt)
    else:
        end_dt = end_dt.astimezone(tz)

    blocks = (
        db.query(ProviderBusyBlock)
        .filter(
            ProviderBusyBlock.clinic_id == clinic_id,
            ProviderBusyBlock.provider_id == provider_id,
        )
        .all()
    )
    if not blocks:
        return None
    day = start_dt.date()
    for b in blocks:
        if not _block_applies_on(b, day):
            continue
        b_start = tz.localize(
            datetime.datetime.combine(day, datetime.time(int(b.start_hour), int(b.start_minute), 0))
        )
        b_end = tz.localize(
            datetime.datetime.combine(day, datetime.time(int(b.end_hour), int(b.end_minute), 0))
        )
        if max(start_dt, b_start) < min(end_dt, b_end):
            return b
    return None
