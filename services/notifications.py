"""Background-task scheduling for booking / cancel / reschedule notifications.

All entry points accept a FastAPI BackgroundTasks instance so the injection
point stays at the router boundary. None of these functions raise back to
the caller — SMS and email are best-effort and logged on failure
(preserves the v1 contract).

Argument order to the underlying `send_*_delayed` functions matches what
api/main.py currently passes inline; do not change those arg orders without
also updating clients/sms_client.py and clients/email_client.py.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks

from clients.email_client import (
    resolve_booking_notification_recipient,
    send_clinic_booking_email_delayed,
)
from clients.sms_client import (
    send_booking_sms_delayed,
    send_cancellation_sms_delayed,
    send_hold_reserved_sms_delayed,
    send_reschedule_sms_delayed,
)
from database.models import Appointment, Clinic, Patient, Provider
from services.tz_utils import format_clinic_local

logger = logging.getLogger("dental-receptionist")


def _provider_display_name(provider: Provider) -> str:
    return " ".join(filter(None, [provider.title, provider.name])).strip() or provider.name


def _patient_display_name(patient: Patient) -> str:
    return " ".join(filter(None, [patient.first_name, patient.last_name])) or "Patient"


def _format_local_date_time(ts: datetime, clinic: Clinic) -> tuple[str, str]:
    """Format an appointment timestamp into (date_str, time_str) in clinic-local time.

    Delegates to services.tz_utils so naive DB values (which are really UTC)
    are converted properly instead of being stamped as already-local."""
    return format_clinic_local(ts, clinic)


def schedule_booking_notifications(
    background_tasks: BackgroundTasks,
    *,
    patient: Patient,
    provider: Provider,
    appointment: Appointment,
    clinic: Clinic,
    service_name: Optional[str],
) -> None:
    """Schedule confirmation SMS to patient + booking email to clinic.

    Source: api/main.py POST /api/calendar/events (around line 360).
    """
    provider_display_name = _provider_display_name(provider)
    patient_name = _patient_display_name(patient)
    date_str, time_str = _format_local_date_time(appointment.start_time, clinic)

    # SMS confirmation
    if patient.phone:
        try:
            background_tasks.add_task(
                send_booking_sms_delayed,
                patient.phone,
                patient_name,
                date_str,
                time_str,
                provider_display_name,
                service_name,
                clinic.name,
                clinic.address,
                clinic.contact_phone,
            )
        except Exception as e:
            logger.warning("SMS confirmation skipped: %s", e)
    else:
        logger.info("No patient phone; skipping SMS confirmation")

    # Clinic-side booking email
    booking_notify_to = resolve_booking_notification_recipient(clinic.booking_notification_email)
    if booking_notify_to:
        try:
            when_local = f"{date_str} at {time_str}"
            background_tasks.add_task(
                send_clinic_booking_email_delayed,
                booking_notify_to,
                clinic.name,
                appointment.id,
                patient_name,
                patient.phone or "",
                patient.email or "",
                when_local,
                provider_display_name,
                service_name,
            )
        except Exception as e:
            logger.warning("Clinic booking email skipped: %s", e)


def schedule_cancellation_notification(
    background_tasks: BackgroundTasks,
    *,
    patient: Patient,
    provider: Provider,
    appointment: Appointment,
    clinic: Clinic,
) -> None:
    """Schedule cancellation SMS to patient (no email).

    Source: api/main.py PUT /api/appointments/{id}/cancel (around line 686).
    """
    if not patient.phone:
        return
    try:
        provider_display_name = _provider_display_name(provider)
        date_str, time_str = _format_local_date_time(appointment.start_time, clinic)
        patient_name = _patient_display_name(patient)
        background_tasks.add_task(
            send_cancellation_sms_delayed,
            patient.phone,
            patient_name,
            date_str,
            time_str,
            provider_display_name,
            clinic.name,
            clinic.address,
            clinic.contact_phone,
        )
    except Exception as e:
        logger.warning("Cancellation SMS skipped: %s", e)


def schedule_reschedule_notification(
    background_tasks: BackgroundTasks,
    *,
    patient: Patient,
    provider: Provider,
    new_start_time: datetime,
    clinic: Clinic,
    service_name: Optional[str],
) -> None:
    """Schedule reschedule SMS to patient (no email).

    Source: api/main.py PUT /api/appointments/{id}/reschedule (around line 852).
    """
    if not patient.phone:
        logger.info("No patient phone; skipping reschedule SMS")
        return
    try:
        date_str, time_str = _format_local_date_time(new_start_time, clinic)
        patient_name = _patient_display_name(patient)
        provider_display_name = _provider_display_name(provider)
        background_tasks.add_task(
            send_reschedule_sms_delayed,
            patient.phone,
            patient_name,
            date_str,
            time_str,
            provider_display_name,
            service_name,
            clinic.name,
            clinic.address,
            clinic.contact_phone,
        )
    except Exception as e:
        logger.warning("Reschedule SMS skipped: %s", e)


def schedule_hold_create_notifications(
    background_tasks: BackgroundTasks,
    *,
    patient: Patient,
    provider: Provider,
    appointment: Appointment,
    clinic: Clinic,
    service_name: Optional[str],
    source: str,
) -> None:
    """Schedule notifications on hold creation.

    - web (booking-web-hold): 'reserved, we'll call' SMS to patient + booking email to clinic.
    - voice (voice-hold): 'you're booked' SMS to patient + booking email to clinic.
    """
    provider_name = _provider_display_name(provider)
    patient_name = _patient_display_name(patient)
    date_str, time_str = _format_local_date_time(appointment.start_time, clinic)

    if patient.phone:
        try:
            if source == "voice-hold":
                background_tasks.add_task(
                    send_booking_sms_delayed,
                    patient.phone,
                    patient_name,
                    date_str,
                    time_str,
                    provider_name,
                    service_name,
                    clinic.name,
                    clinic.address,
                    clinic.contact_phone,
                )
            else:
                background_tasks.add_task(
                    send_hold_reserved_sms_delayed,
                    patient.phone,
                    patient_name,
                    date_str,
                    time_str,
                    provider_name,
                    clinic.name,
                    clinic.contact_phone,
                    clinic.address,
                )
        except Exception as e:
            logger.warning("Hold create SMS skipped: %s", e)

    booking_notify_to = resolve_booking_notification_recipient(clinic.booking_notification_email)
    if booking_notify_to:
        try:
            when_local = f"{date_str} at {time_str}"
            background_tasks.add_task(
                send_clinic_booking_email_delayed,
                booking_notify_to,
                clinic.name,
                appointment.id,
                patient_name,
                patient.phone or "",
                patient.email or "",
                when_local,
                provider_name,
                service_name,
            )
        except Exception as e:
            logger.warning("Hold create clinic email skipped: %s", e)


def schedule_hold_confirm_notifications(
    background_tasks: BackgroundTasks,
    *,
    patient: Patient,
    provider: Provider,
    appointment: Appointment,
    clinic: Clinic,
    service_name: Optional[str],
    source: str,
) -> None:
    """Schedule notifications on staff hold confirmation.

    - web (booking-web-hold): 'you're booked' SMS to patient.
    - voice (voice-hold): silent (patient was already told when the hold was created).
    """
    if source == "voice-hold":
        return
    if not patient.phone:
        return
    try:
        provider_name = _provider_display_name(provider)
        patient_name = _patient_display_name(patient)
        date_str, time_str = _format_local_date_time(appointment.start_time, clinic)
        background_tasks.add_task(
            send_booking_sms_delayed,
            patient.phone,
            patient_name,
            date_str,
            time_str,
            provider_name,
            service_name,
            clinic.name,
            clinic.address,
            clinic.contact_phone,
        )
    except Exception as e:
        logger.warning("Hold confirm SMS skipped: %s", e)


__all__ = [
    "schedule_booking_notifications",
    "schedule_cancellation_notification",
    "schedule_hold_confirm_notifications",
    "schedule_hold_create_notifications",
    "schedule_reschedule_notification",
]
