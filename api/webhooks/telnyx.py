"""Telnyx inbound SMS webhook.

Verifies Ed25519 signature, extracts message, looks up a matching
AppointmentReminder (within last 7 days, no reply yet). If no match,
the payload is forwarded to the existing chat_api SMS path (stubbed
no-op in MVP).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from clients import telnyx_messaging
from database.connection import get_db
from database.models import Appointment, Patient
from database.ops.models import AppointmentReminder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/telnyx", tags=["webhooks"])


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

    # Action dispatch lands in B8.
    return {
        "routed_to": "reminder_match",
        "reminder_id": reminder.id,
        "text": text,
        "message_id": message_id,
    }
