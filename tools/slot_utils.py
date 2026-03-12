"""
DB-based slot availability logic.

Computes available appointment slots from the database instead of Google Calendar.
Uses per-clinic config (timezone, working hours) when clinic is provided.
"""

import datetime
import os
from typing import List, Optional, Union

import pytz
from sqlalchemy.orm import Session

from database.models import Appointment, AppointmentStatus, Doctor

EDMONTON_TZ = pytz.timezone("America/Edmonton")


def get_available_slots(
    db: Session,
    start_datetime: str,
    end_datetime: str,
    doctor_id: Optional[int] = None,
    doctor_name: Optional[str] = None,
    slot_minutes: int = 30,
    clinic_id: Optional[str] = None,
    timezone_str: Optional[str] = None,
    hour_start: Optional[int] = None,
    hour_end: Optional[int] = None,
) -> List[str]:
    """
    Compute available appointment slots from the database.

    Args:
        db: Database session
        start_datetime: ISO datetime string for range start
        end_datetime: ISO datetime string for range end
        doctor_id: Optional doctor ID to filter availability
        doctor_name: Optional doctor name (resolved to doctor_id if doctor_id not set)
        slot_minutes: Slot duration in minutes (default 30)

    Returns:
        List of available slot start times as ISO strings
    """
    # Resolve doctor filter (scoped by clinic_id if provided)
    resolved_doctor_id = doctor_id
    doctor_query = db.query(Doctor)
    if clinic_id:
        doctor_query = doctor_query.filter(Doctor.clinic_id == clinic_id)
    if resolved_doctor_id is None and doctor_name:
        doctor = doctor_query.filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
        if doctor:
            resolved_doctor_id = doctor.id

    # Parse datetimes
    try:
        start_dt = datetime.datetime.fromisoformat(
            start_datetime.replace("Z", "+00:00")
        )
        end_dt = datetime.datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return []

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

    # Build busy intervals from DB (scoped by clinic_id if provided)
    active_statuses = [
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.PENDING_SYNC,
        AppointmentStatus.PENDING,
    ]
    query = db.query(Appointment).filter(
        Appointment.status.in_(active_statuses),
        Appointment.start_time < end_dt,
        Appointment.end_time > start_dt,
    )
    if clinic_id:
        query = query.filter(Appointment.clinic_id == clinic_id)
    if resolved_doctor_id is not None:
        query = query.filter(Appointment.doctor_id == resolved_doctor_id)
    appointments = query.all()

    busy_intervals = []
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

    # Generate candidate slots within working hours
    slot_delta = datetime.timedelta(minutes=slot_minutes)

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

    available = []
    current = max(start_dt, day_start(start_dt))

    while current < end_dt:
        day_e = day_end(current)
        if current >= day_e:
            next_date = current.date() + datetime.timedelta(days=1)
            current = tz.localize(
                datetime.datetime.combine(
                    next_date, datetime.time(h_start, 0, 0)
                )
            )
            continue

        slot_end = current + slot_delta
        if slot_end > day_e or slot_end > end_dt:
            next_date = current.date() + datetime.timedelta(days=1)
            current = tz.localize(
                datetime.datetime.combine(
                    next_date, datetime.time(h_start, 0, 0)
                )
            )
            continue

        is_free = True
        for b_start, b_end in busy_intervals:
            if max(current, b_start) < min(slot_end, b_end):
                is_free = False
                break
        if is_free:
            available.append(current.isoformat())

        current = current + slot_delta

    return available
