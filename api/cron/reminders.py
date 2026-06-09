"""Cron endpoint hit by Cloud Scheduler every ~5 minutes.

Picks SCHEDULED appointments whose target send time falls in the next
5-minute window (with quiet-hours deferment and skip-too-late guards)
and inserts + sends an AppointmentReminder row for each.

Auth: X-Internal-Secret header (same DENTAL_API_INTERNAL_SECRET used
by /api/public/* endpoints).
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies.auth import require_internal_secret
from database.connection import get_db
from database.models import Appointment, AppointmentStatus
from database.ops.models import AppointmentReminder
from services import sms as sms_service
from services import sms_templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron", tags=["cron"])


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _within_quiet_hours(t: datetime, *, start_h: int, end_h: int) -> bool:
    """True if t falls in the daily quiet window [start_h, end_h).

    Window straddles midnight when end_h < start_h.
    """
    h = t.hour
    if start_h < end_h:
        return start_h <= h < end_h
    return h >= start_h or h < end_h


def _next_morning(t: datetime, *, open_h: int) -> datetime:
    """Bump t forward to the next open_h:00, same day or next day."""
    candidate = t.replace(hour=open_h, minute=0, second=0, microsecond=0)
    if candidate <= t:
        candidate += timedelta(days=1)
    return candidate


def _human_readable_when(ts: datetime, clinic) -> str:
    """Format start_time in clinic-local TZ as 'YYYY-MM-DD at HH:MM AM/PM'."""
    from services.notifications import _format_local_date_time
    date_str, time_str = _format_local_date_time(ts, clinic)
    return f"{date_str} at {time_str}"


def _reschedule_link(token: str) -> str:
    base = os.getenv("DENTAL_API_PUBLIC_BASE_URL", "")
    return f"{base}/p/reschedule/{token}"


def _ensure_aware(ts: datetime) -> datetime:
    """Stamp naive datetimes as UTC so comparisons are well-defined."""
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


@router.post("/reminders/scan", dependencies=[Depends(require_internal_secret)])
def scan(db: Session = Depends(get_db)):
    """Pick due appointments and send reminders.

    Returns a JSON summary:
      {"sent_count": int, "skipped_too_late": int, "candidates_total": int}
    """
    offset_hours = _env_int("REMINDER_OFFSET_HOURS", 24)
    quiet_start = _env_int("QUIET_HOURS_START", 21)
    quiet_end = _env_int("QUIET_HOURS_END", 8)
    min_lead_minutes = _env_int("MIN_LEAD_MINUTES", 30)

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(minutes=5)

    # target_send_time = appointment.start_time - offset_hours, so we want
    # appointment.start_time in (now + offset_hours, window_end + offset_hours].
    range_start = now + timedelta(hours=offset_hours)
    range_end = window_end + timedelta(hours=offset_hours)

    # Appointment.start_time is stored naive (UTC). Strip tz when comparing.
    candidates = (
        db.query(Appointment)
        .filter(Appointment.start_time >= range_start.replace(tzinfo=None))
        .filter(Appointment.start_time <= range_end.replace(tzinfo=None))
        .filter(Appointment.status == AppointmentStatus.SCHEDULED)
        .all()
    )

    sent_count = 0
    skipped_too_late = 0
    provider_env = os.getenv("SMS_PROVIDER", "twilio")

    for appt in candidates:
        # Dedup: only one reminder per (appointment, channel).
        existing = (
            db.query(AppointmentReminder)
            .filter_by(appointment_id=appt.id, channel="sms")
            .first()
        )
        if existing is not None:
            continue

        appt_start = _ensure_aware(appt.start_time)
        target_send = appt_start - timedelta(hours=offset_hours)

        # Quiet-hours deferment.
        if _within_quiet_hours(target_send, start_h=quiet_start, end_h=quiet_end):
            target_send = _next_morning(target_send, open_h=quiet_end)

        # Skip if too late (within MIN_LEAD_MINUTES of appointment).
        if target_send >= appt_start - timedelta(minutes=min_lead_minutes):
            db.add(AppointmentReminder(
                id=str(uuid.uuid4()),
                appointment_id=appt.id,
                channel="sms",
                offset_minutes=offset_hours * 60,
                scheduled_at=target_send.replace(tzinfo=None),
                status="skipped_too_late",
                provider=provider_env,
            ))
            db.commit()
            skipped_too_late += 1
            continue

        # Build reminder body.
        reschedule_token = str(uuid.uuid4())
        try:
            patient = appt.patient
            provider = appt.provider
            clinic = appt.clinic
            body = sms_templates.render(
                "reminder", "en",
                first_name=(patient.first_name or "") if patient else "",
                clinic_name=clinic.name if clinic else "",
                when_human=_human_readable_when(appt.start_time, clinic),
                provider_first_name=(provider.name or "") if provider else "",
                reschedule_link=_reschedule_link(reschedule_token),
            )
        except Exception as exc:
            logger.exception("Failed to render reminder for appt %s: %s", appt.id, exc)
            continue

        to_phone = patient.phone if patient else None
        if not to_phone:
            logger.warning("Skipping reminder for appt %s: no patient phone", appt.id)
            continue

        # Send. Per-clinic FROM number — falls back to TELNYX_SMS_FROM_NUMBER
        # / TWILIO_PHONE_NUMBER env in the client when clinic.sms_from_number
        # is unset (legacy single-DID deployments).
        message_id = sms_service.send_sms_raw(
            to=to_phone,
            body=body,
            from_=clinic.sms_from_number if clinic else None,
        )

        reminder = AppointmentReminder(
            id=str(uuid.uuid4()),
            appointment_id=appt.id,
            channel="sms",
            offset_minutes=offset_hours * 60,
            scheduled_at=target_send.replace(tzinfo=None),
            sent_at=datetime.utcnow() if message_id else None,
            status="sent" if message_id else "failed",
            failure_reason=None if message_id else "send returned None",
            provider=provider_env,
            outbound_message_id=message_id,
            reschedule_token=reschedule_token,
            reschedule_token_expires_at=(appt_start + timedelta(hours=48)).replace(tzinfo=None),
        )
        db.add(reminder)
        db.commit()
        if message_id:
            sent_count += 1

    return {
        "sent_count": sent_count,
        "skipped_too_late": skipped_too_late,
        "candidates_total": len(candidates),
    }
