"""Shared serializers used by multiple v1 routers.

Pure functions that transform ORM rows into Pydantic / dict shapes.
"""
from __future__ import annotations

import json as _json

from database.models import Appointment


def _busy_block_envelope(block) -> dict:
    """Build the 409 'Provider busy' detail.busy_block payload.

    Surfaces both the legacy single-day fields (`weekday`) and the v2 fields
    (`weekdays`, `specific_date`, `recurrence_until`) so consumers can pattern
    on either shape.
    """
    weekdays_list = None
    raw = getattr(block, "weekdays", None)
    if raw:
        try:
            parsed = _json.loads(raw)
            if isinstance(parsed, list):
                weekdays_list = [int(x) for x in parsed]
        except (ValueError, TypeError):
            weekdays_list = None
    return {
        "id": block.id,
        "weekday": block.weekday,
        "weekdays": weekdays_list,
        "specific_date": block.specific_date.isoformat() if getattr(block, "specific_date", None) else None,
        "recurrence_until": block.recurrence_until.isoformat() if getattr(block, "recurrence_until", None) else None,
        "start_hour": block.start_hour,
        "start_minute": block.start_minute,
        "end_hour": block.end_hour,
        "end_minute": block.end_minute,
        "label": block.label,
    }


def _to_appointment_detail(apt: Appointment) -> "AppointmentDetailResponse":
    """Build AppointmentDetailResponse with provider_name and service_name.

    Lazy-imports the Pydantic class to avoid an import cycle while v1 appointment
    schemas still live in api.main. Task 10 moves the schema to
    api/v1/appointments/schemas.py; at that point this lazy import flips to
    a top-level import.
    """
    from api.main import AppointmentDetailResponse  # noqa: WPS433 (lazy until Task 10)

    provider_name = None
    if apt.provider:
        provider_name = " ".join(filter(None, [apt.provider.title, apt.provider.name])).strip() or apt.provider.name
    service_name = apt.service.name if apt.service else None
    return AppointmentDetailResponse(
        id=apt.id,
        patient_id=apt.patient_id,
        provider_id=apt.provider_id,
        service_id=apt.service_id,
        provider_name=provider_name,
        service_name=service_name,
        start_time=apt.start_time,
        end_time=apt.end_time,
        reason_note=apt.reason_note,
        status=apt.status.value,
        calendar_event_id=apt.calendar_event_id,
    )


__all__ = ["_busy_block_envelope", "_to_appointment_detail"]
