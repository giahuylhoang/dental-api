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
import os
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks

from clients.email_client import (
    build_email_message,
    resolve_booking_notification_recipient,
    resolve_clinic_recipients,
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

    # Clinic-side booking email — clinic-scoped recipients (booking email + info@).
    when_local = f"{date_str} at {time_str}"
    for _recipient in resolve_clinic_recipients(clinic, kind="booking"):
        try:
            background_tasks.add_task(
                send_clinic_booking_email_delayed,
                _recipient,
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

    when_local = f"{date_str} at {time_str}"
    for _recipient in resolve_clinic_recipients(clinic, kind="booking"):
        try:
            background_tasks.add_task(
                send_clinic_booking_email_delayed,
                _recipient,
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


# ---------------------------------------------------------------------------
# Referral notifications (Phase 1). Sync + primitive-only args so it is safe to
# run as a FastAPI BackgroundTask after the DB session has closed. The storage
# backend is stateless (no session), so reading files / signing URLs here is OK.
# ---------------------------------------------------------------------------
_REFERRAL_ATTACH_BUDGET = int(os.getenv("REFERRAL_EMAIL_ATTACH_MAX_MB", "12")) * 1024 * 1024
_REFERRAL_MAX_ENCODED = int(os.getenv("REFERRAL_EMAIL_MAX_ENCODED_MB", "23")) * 1024 * 1024
_REFERRAL_LINK_TTL = int(os.getenv("GCS_LINK_URL_TTL", str(7 * 24 * 3600)))


def _referral_body(clinic_name: str, referral: dict, files: list[dict], links=None) -> str:
    lines = [
        "A new patient referral was submitted.",
        "",
        f"Clinic:               {clinic_name}",
        f"Patient name:         {referral.get('patient_name', '')}",
        f"Patient phone:        {referral.get('patient_phone', '')}",
        f"Referred by:          {referral.get('referred_by', '')}",
        f"Referrer contact:     {referral.get('referrer_contact') or '—'}",
        f"Denturist requested:  {referral.get('provider_label') or 'Either / first available'}",
        f"Proposed extraction:  {referral.get('proposed_extraction_date') or '—'}",
        f"Submitted at:         {referral.get('submitted_at', '')}",
        "",
        "Treatment plan:",
        (referral.get("tx_plan") or "—"),
        "",
        f"Attachments ({len(files)}):",
    ]
    for f in files:
        size_kb = round((f.get("size") or 0) / 1024)
        lines.append(f"  - {f.get('original_name') or f.get('object_key')} ({size_kb} KB)")
    if links:
        lines += ["", "Files were too large to attach — secure download links (expire in ~7 days):"]
        lines += [f"  - {name}: {url}" for name, url in links]
    return "\n".join(lines)


def dispatch_referral_created(*, recipients, clinic_name, referral, files, storage) -> bool:
    """Build + send the referral notification email. Best-effort; never raises.

    Attaches the files when the *encoded* message stays under the safe SMTP cap;
    otherwise falls back to ~7-day signed download links.
    """
    from clients.email_client import SEND_CLINIC_BOOKING_EMAIL, _deliver_message

    recipients = [r for r in (recipients or []) if r]
    if not recipients:
        return True
    subject = (
        f"New referral: {clinic_name} — {referral.get('patient_name', '')} "
        f"(from {referral.get('referred_by', '')})"
    )

    if not SEND_CLINIC_BOOKING_EMAIL:
        logger.info("Clinic emails disabled — would send referral '%s' to %s", subject, recipients)
        return True

    raw_total = sum((f.get("size") or 0) for f in files)
    attachments = []
    if files and raw_total <= _REFERRAL_ATTACH_BUDGET:
        try:
            for f in files:
                attachments.append({
                    "filename": f.get("original_name") or f.get("object_key", "file"),
                    "content": storage.read_bytes(f["object_key"]),
                    "mime": f.get("mime"),
                })
        except Exception as e:
            logger.warning("Referral attach read failed (%s) — falling back to links", e)
            attachments = []

    if attachments:
        body = _referral_body(clinic_name, referral, files)
        msg = build_email_message(
            to_emails=recipients, subject=subject, body=body, attachments=attachments
        )
        if len(msg.as_bytes()) <= _REFERRAL_MAX_ENCODED:
            return _deliver_message(msg)
        logger.info("Referral email too large to attach (%d bytes) — using links", len(msg.as_bytes()))

    # Links mode (no attachments fit, or none provided).
    links = []
    for f in files:
        try:
            url = storage.signed_get_url(f["object_key"], ttl_seconds=_REFERRAL_LINK_TTL)
        except Exception:
            url = "(link unavailable)"
        links.append((f.get("original_name") or f.get("object_key"), url))
    body = _referral_body(clinic_name, referral, files, links=links)
    msg = build_email_message(to_emails=recipients, subject=subject, body=body)
    return _deliver_message(msg)
