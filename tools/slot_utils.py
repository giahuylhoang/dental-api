"""
DB-based slot availability logic.

Computes available appointment slots from the database instead of Google Calendar.
Supports generic providers (doctor, assistant, etc.).
"""

import datetime
import os
from typing import Dict, List, Optional

import pytz
from sqlalchemy.orm import Session

from database.models import Appointment, AppointmentStatus, Provider, ProviderBusyBlock

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

    def _iter_busy_blocks_for_dt(
        blocks_by_weekday: Dict[int, List[tuple]], dt: datetime.datetime
    ) -> List[tuple]:
        wd = int(dt.weekday())
        blocks = blocks_by_weekday.get(wd) or []
        if not blocks:
            return []
        day = dt.date()
        intervals: List[tuple] = []
        for sh, sm, eh, em in blocks:
            b_start = tz.localize(datetime.datetime.combine(day, datetime.time(sh, sm, 0)))
            b_end = tz.localize(datetime.datetime.combine(day, datetime.time(eh, em, 0)))
            intervals.append((b_start, b_end))
        return intervals

    def compute_slots_for_busy(busy_intervals: List[tuple], blocks_by_weekday: Dict[int, List[tuple]]) -> List[str]:
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
            # Recurring busy blocks (weekday/time)
            if is_free:
                for b_start, b_end in _iter_busy_blocks_for_dt(blocks_by_weekday, current):
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

        # Provider busy blocks (recurring)
        blocks_q = db.query(ProviderBusyBlock).filter(ProviderBusyBlock.provider_id == provider.id)
        if clinic_id:
            blocks_q = blocks_q.filter(ProviderBusyBlock.clinic_id == clinic_id)
        blocks = blocks_q.all()
        blocks_by_weekday: Dict[int, List[tuple]] = {}
        for b in blocks:
            blocks_by_weekday.setdefault(int(b.weekday), []).append(
                (int(b.start_hour), int(b.start_minute), int(b.end_hour), int(b.end_minute))
            )

        slots = compute_slots_for_busy(busy_intervals, blocks_by_weekday)
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
