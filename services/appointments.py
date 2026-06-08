"""Appointment conflict detection extracted from api/main.py.

Two public functions — check_conflicts_for_create and
check_conflicts_for_reschedule — share helpers and the ACTIVE_STATUSES
tuple but preserve the small differences between the create and reschedule
paths (self-exclusion, message text). Do not unify them without
intentionally changing behavior — the message text is part of the v1
wire contract for clients that pattern-match on it.

The "active statuses" set MUST stay aligned with the set used in
tools/slot_utils for slot computation. If you change one, change both.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pytz
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.serializers import _busy_block_envelope
from database.models import Appointment, AppointmentStatus, Clinic

logger = logging.getLogger("dental-receptionist")

ACTIVE_STATUSES: tuple[AppointmentStatus, ...] = (
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.PENDING_SYNC,
    AppointmentStatus.PENDING,
)


def _query_overlapping_appointments(
    db: Session,
    *,
    clinic_id: str,
    provider_id: int,
    start: datetime,
    end: datetime,
    excluding_appointment_id: Optional[str] = None,
) -> List[Appointment]:
    """Return appointments that overlap [start, end) for this provider+clinic.

    An appointment overlaps if its status is active and time ranges intersect:
        existing.start_time < end  AND  existing.end_time > start
    Optionally excludes a specific appointment id (used by the reschedule path
    so the appointment being moved doesn't conflict with itself).
    """
    # Appointment.start_time / end_time are stored naive UTC. Normalize the
    # filter values to the same representation so the SQL comparison doesn't
    # silently fall over when the caller passes a tz-aware bound.
    from services.tz_utils import to_storage_utc
    start_utc = to_storage_utc(start)
    end_utc = to_storage_utc(end)
    q = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.provider_id == provider_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.start_time < end_utc,
        Appointment.end_time > start_utc,
    )
    if excluding_appointment_id is not None:
        q = q.filter(Appointment.id != excluding_appointment_id)
    from services.holds import exclude_expired_holds_filter
    q = q.filter(exclude_expired_holds_filter(datetime.utcnow()))
    return q.all()


def _conflict_details(conflicting: List[Appointment]) -> list[dict]:
    return [
        {
            "appointment_id": apt.id,
            "start_time": apt.start_time.isoformat(),
            "end_time": apt.end_time.isoformat(),
            "patient_id": apt.patient_id,
            "status": apt.status.value,
        }
        for apt in conflicting
    ]


def _raise_if_busy_block_overlap(
    db: Session,
    *,
    clinic: Clinic,
    provider_id: int,
    start: datetime,
    end: datetime,
    message: str,
) -> None:
    """Reject if the window overlaps one of the provider's recurring busy blocks."""
    # Local import: find_busy_block_overlap is in tools/, and we keep the
    # original lazy-import style from api/main.py to match its boundaries.
    from tools.slot_utils import find_busy_block_overlap

    tz = pytz.timezone(clinic.timezone or "America/Edmonton")
    block = find_busy_block_overlap(db, clinic.id, provider_id, start, end, tz)
    if block is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Provider busy",
                "message": message,
                "requested_time": {
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                },
                "busy_block": _busy_block_envelope(block),
            },
        )


def check_conflicts_for_create(
    db: Session,
    *,
    clinic: Clinic,
    provider_id: int,
    start: datetime,
    end: datetime,
) -> None:
    """Raise 409 if the window conflicts with an active appointment or a busy block.

    Used by POST /api/calendar/events and POST /api/appointments.
    Source: api/main.py POST /api/calendar/events (currently ~line 268).
    """
    conflicting = _query_overlapping_appointments(
        db, clinic_id=clinic.id, provider_id=provider_id, start=start, end=end,
    )
    if conflicting:
        logger.warning(
            f"Appointment conflict detected for provider_id {provider_id} "
            f"at {start.isoformat()} - {end.isoformat()}. "
            f"Found {len(conflicting)} conflicting appointment(s)."
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Appointment conflict",
                "message": "Provider already has an appointment scheduled during this time slot.",
                "requested_time": {
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                },
                "conflicting_appointments": _conflict_details(conflicting),
            },
        )
    _raise_if_busy_block_overlap(
        db, clinic=clinic, provider_id=provider_id, start=start, end=end,
        message="Provider is on a busy block during this time slot.",
    )


def check_conflicts_for_reschedule(
    db: Session,
    *,
    clinic: Clinic,
    provider_id: int,
    start: datetime,
    end: datetime,
    excluding_appointment_id: str,
) -> None:
    """Same as check_conflicts_for_create but excludes the appointment being moved.

    Used by PUT /api/appointments/{id}/reschedule. The message text differs
    slightly from check_conflicts_for_create ('the requested' vs 'this') —
    this is preserved verbatim from the original main.py because it's part
    of the v1 wire contract.

    Source: api/main.py PUT /api/appointments/{id}/reschedule (currently ~line 776).
    """
    conflicting = _query_overlapping_appointments(
        db, clinic_id=clinic.id, provider_id=provider_id, start=start, end=end,
        excluding_appointment_id=excluding_appointment_id,
    )
    if conflicting:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Appointment conflict",
                "message": "Provider already has an appointment scheduled during the requested time slot.",
                "requested_time": {
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                },
                "conflicting_appointments": _conflict_details(conflicting),
            },
        )
    _raise_if_busy_block_overlap(
        db, clinic=clinic, provider_id=provider_id, start=start, end=end,
        message="Provider is on a busy block during the requested time slot.",
    )


__all__ = [
    "ACTIVE_STATUSES",
    "check_conflicts_for_create",
    "check_conflicts_for_reschedule",
]
