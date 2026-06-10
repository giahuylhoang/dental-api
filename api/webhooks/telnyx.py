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

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from clients import telnyx_messaging
from database.connection import get_db
from database.models import Appointment, AppointmentStatus, Clinic, Patient
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
    # Telnyx puts recipients in a list at data.payload.to[].phone_number.
    # Multi-clinic disambiguation hinges on the `to` number — same patient
    # at two clinics gets routed to the correct reminder by clinic DID.
    to_list = msg.get("to") or []
    to_phone = (to_list[0] or {}).get("phone_number") if to_list else None
    text = msg.get("text") or ""
    message_id = msg.get("id")
    if not from_phone:
        return {"routed_to": "ignored_no_from"}

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    # AppointmentReminder.sent_at and Appointment.start_time are stored
    # tz-naive (UTC); strip tz on the cutoff for comparison consistency.
    cutoff_naive = cutoff.replace(tzinfo=None)
    # Scope by Clinic.sms_from_number == to_phone so same-patient-at-two-
    # clinics replies disambiguate. If the matching clinic hasn't set
    # sms_from_number, the join fails and we fall through — correct
    # behavior: webhook can't route to a clinic that hasn't registered
    # its number.
    reminder = (
        db.query(AppointmentReminder)
        .join(Appointment, AppointmentReminder.appointment_id == Appointment.id)
        .join(Patient, Appointment.patient_id == Patient.id)
        .join(Clinic, Appointment.clinic_id == Clinic.id)
        .filter(AppointmentReminder.reply_received_at.is_(None))
        .filter(AppointmentReminder.sent_at >= cutoff_naive)
        .filter(Patient.phone == from_phone)
        .filter(Clinic.sms_from_number == to_phone)
        .order_by(AppointmentReminder.sent_at.desc())
        .first()
    )

    if reminder is None:
        return await _forward_to_chat_api(
            db=db,
            from_phone=from_phone,
            to_phone=to_phone,
            text=text,
        )

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
            sms_service.send_sms_raw(
                to=from_phone,
                body=ack_body,
                from_=(clinic.sms_from_number if clinic else None),
            )
        except Exception as exc:
            logger.warning("Failed to send ack SMS to %s: %s", from_phone, exc)

    db.commit()

    return {
        "routed_to": "reminder_match",
        "intent": intent.value,
        "source": source,
    }


def _chat_api_url() -> str:
    """chat_api base URL. Defaults to localhost:8092 for dev (matches the
    REPL default + the systemd unit's bind port)."""
    return os.environ.get("INTERNAL_CHAT_API_URL", "http://127.0.0.1:8092").rstrip("/")


def _chat_api_headers() -> dict[str, str]:
    """X-Internal-Secret if dental-api has one configured. chat_api's auth
    is no-op when the secret is unset on its side, so sending an extra
    header is harmless."""
    headers = {"Content-Type": "application/json"}
    secret = os.environ.get("DENTAL_API_INTERNAL_SECRET")
    if secret:
        headers["X-Internal-Secret"] = secret
    return headers


async def _forward_to_chat_api(
    *, db: Session, from_phone: str, to_phone: str | None, text: str,
) -> dict:
    """Forward a non-reminder-matched SMS to chat_api as general chat.

    Looks up clinic by `to_phone` (Clinic.sms_from_number) — that's how
    multi-clinic disambiguation works on the SMS side, same as the
    reminder branch. Optionally pre-resolves patient_id from
    Patient.phone (saves chat_api an HTTP round-trip). Posts the
    documented chat_api SMS contract and fires the reply back via
    services.sms.send_sms_raw.

    Returns a dispatch record indicating where the message went. On
    chat_api 5xx or send failure, raises HTTPException(502) so Telnyx
    retries the inbound (idempotency on the chat_api side is the
    consumer's responsibility — chat_api state advances per turn).
    """
    if not to_phone:
        logger.warning("sms_router decision=fallthrough_no_to from=%s", from_phone)
        return {"routed_to": "fallthrough_no_to"}

    clinic = (
        db.query(Clinic).filter(Clinic.sms_from_number == to_phone).first()
    )
    if clinic is None:
        logger.warning(
            "sms_router decision=fallthrough_no_clinic to=%s from=%s",
            to_phone, from_phone,
        )
        return {"routed_to": "fallthrough_no_clinic", "to": to_phone}

    patient = db.query(Patient).filter(Patient.phone == from_phone).first()
    patient_id = patient.id if patient else None

    payload = {
        "phone_number": from_phone,
        "channel": "sms",
        "message": text,
        "clinic_slug": clinic.id,
        "patient_id": patient_id,
        # pending_reminder is omitted here — we got here precisely because
        # NO reminder matched. The AMBIGUOUS-reminder chat-takeover path
        # is a separate feature (would live in the reminder branch above,
        # forwarding with pending_reminder context).
    }

    chat_url = f"{_chat_api_url()}/chat/message"
    logger.info(
        "sms_router decision=chat_no_reminder clinic=%s patient_id=%s phone=%s",
        clinic.id, patient_id, from_phone,
    )

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            chat_resp = await client.post(
                chat_url, headers=_chat_api_headers(), json=payload,
            )
            chat_resp.raise_for_status()
            chat_data = chat_resp.json()
    except httpx.HTTPError as exc:
        logger.error(
            "chat_api_forward_failed url=%s from=%s error=%s",
            chat_url, from_phone, exc,
        )
        raise HTTPException(status_code=502, detail=f"chat_api forward failed: {exc}")

    reply_body = (chat_data.get("reply") or "").strip()
    if not reply_body:
        logger.warning(
            "chat_api_empty_reply from=%s phase=%s",
            from_phone, chat_data.get("phase"),
        )
        return {
            "routed_to": "chat_no_reply",
            "phase": chat_data.get("phase"),
        }

    try:
        sms_service.send_sms_raw(
            to=from_phone,
            body=reply_body,
            from_=clinic.sms_from_number,
        )
    except Exception as exc:
        logger.error(
            "Failed to send chat reply SMS to %s via %s: %s",
            from_phone, clinic.sms_from_number, exc,
        )
        raise HTTPException(status_code=502, detail="failed to send reply SMS")

    return {
        "routed_to": "chat_no_reminder",
        "phase": chat_data.get("phase"),
        "patient_id": patient_id,
    }
