"""Telnyx inbound SMS webhook.

Verifies Ed25519 signature, extracts message, looks up a matching
AppointmentReminder (within last 7 days, no reply yet). If no match,
the payload is forwarded to the existing chat_api SMS path (stubbed
no-op in MVP).

On match, dispatches an action based on the parsed reply intent:
  * confirmed             -> appointment.status = CONFIRMED, ack SMS
  * cancelled             -> appointment.status = CANCELLED, ack SMS
  * reschedule_requested  -> status unchanged, ack SMS with link
  * ambiguous             -> increment counter; ack only on first hit
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from clients import telnyx_messaging
from database.connection import get_db
from database.models import Appointment, AppointmentStatus, Patient
from database.ops.models import AppointmentReminder
from services import sms as sms_service
from services import sms_templates
from services.reply_parser import ReplyIntent, parse as parse_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/telnyx", tags=["webhooks"])


def _when_human(ts: datetime, clinic) -> str:
    """Format an appointment ts into clinic-local 'YYYY-MM-DD at HH:MM AM/PM'."""
    from services.notifications import _format_local_date_time
    date_str, time_str = _format_local_date_time(ts, clinic)
    return f"{date_str} at {time_str}"


def _reschedule_link(token: str | None) -> str:
    base = os.getenv("DENTAL_API_PUBLIC_BASE_URL", "")
    return f"{base}/p/reschedule/{token or ''}"


@router.post("/sms-inbound")
async def sms_inbound(
    request: Request,
    db: Session = Depends(get_db),
    signature: str | None = Header(None, alias="Telnyx-Signature-ED25519"),
    timestamp: str | None = Header(None, alias="Telnyx-Timestamp"),
):
    raw = await request.body()
    if not (
        signature
        and timestamp
        and telnyx_messaging.verify_webhook_signature(raw, signature, timestamp)
    ):
        raise HTTPException(status_code=401, detail="invalid telnyx signature")

    payload = json.loads(raw)
    data = payload.get("data", {})
    if data.get("event_type") != "message.received":
        return {"routed_to": "ignored_event", "event_type": data.get("event_type")}

    msg = data.get("payload", {})
    from_phone = (msg.get("from") or {}).get("phone_number")
    text = msg.get("text") or ""
    message_id = msg.get("id")
    if not from_phone:
        return {"routed_to": "ignored_no_from"}

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    # AppointmentReminder.sent_at and Appointment.start_time are stored
    # tz-naive (UTC); strip tz on the cutoff for comparison consistency.
    cutoff_naive = cutoff.replace(tzinfo=None)
    reminder = (
        db.query(AppointmentReminder)
        .join(Appointment, AppointmentReminder.appointment_id == Appointment.id)
        .join(Patient, Appointment.patient_id == Patient.id)
        .filter(AppointmentReminder.reply_received_at.is_(None))
        .filter(AppointmentReminder.sent_at >= cutoff_naive)
        .filter(Patient.phone == from_phone)
        .order_by(AppointmentReminder.sent_at.desc())
        .first()
    )

    if reminder is None:
        return {"routed_to": "fallthrough"}

    # --- Action dispatch (Task B8) ---
    intent, source = parse_reply(text)

    reminder.reply_received_at = datetime.now(timezone.utc).replace(tzinfo=None)
    reminder.reply_parsed_intent = intent.value
    reminder.reply_raw_text = text

    appt = (
        reminder.appointment
        if hasattr(reminder, "appointment") and getattr(reminder, "appointment", None) is not None
        else db.query(Appointment).filter_by(id=reminder.appointment_id).first()
    )
    clinic = appt.clinic if (appt is not None and hasattr(appt, "clinic")) else None
    clinic_phone = (clinic.contact_phone if clinic else "") or ""
    reschedule_link = _reschedule_link(reminder.reschedule_token)

    ack_body: str | None = None
    if intent == ReplyIntent.CONFIRMED:
        if appt is not None:
            appt.status = AppointmentStatus.CONFIRMED
        ack_body = sms_templates.render(
            "ack_confirmed",
            "en",
            when_human=_when_human(appt.start_time, clinic) if appt is not None else "",
        )
    elif intent == ReplyIntent.CANCELLED:
        if appt is not None:
            appt.status = AppointmentStatus.CANCELLED
        ack_body = sms_templates.render(
            "ack_cancelled",
            "en",
            clinic_phone=clinic_phone,
            reschedule_link=reschedule_link,
        )
    elif intent == ReplyIntent.RESCHEDULE_REQUESTED:
        # Status stays SCHEDULED — staff/patient still own the reschedule.
        ack_body = sms_templates.render(
            "ack_reschedule",
            "en",
            clinic_phone=clinic_phone,
            reschedule_link=reschedule_link,
        )
    elif intent == ReplyIntent.AMBIGUOUS:
        reminder.ambiguous_reply_count = (reminder.ambiguous_reply_count or 0) + 1
        # Send a disambiguation prompt on the first ambiguous reply only.
        # On the second+, suppress the auto-reply — the escalation state is
        # derivable from (reply_parsed_intent='ambiguous' AND
        # ambiguous_reply_count >= 2) in queries.
        if reminder.ambiguous_reply_count < 2:
            ack_body = sms_templates.render("ack_ambiguous", "en")

    if ack_body:
        try:
            sms_service.send_sms_raw(to=from_phone, body=ack_body)
        except Exception as exc:
            logger.warning("Failed to send ack SMS to %s: %s", from_phone, exc)

    db.commit()

    return {
        "routed_to": "reminder_match",
        "intent": intent.value,
        "source": source,
    }
