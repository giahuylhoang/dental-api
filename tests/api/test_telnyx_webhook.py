"""Tests for POST /webhooks/telnyx/sms-inbound."""

import base64
import json
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import nacl.signing

from database.models import Appointment, AppointmentStatus, Patient
from database.ops.models import AppointmentReminder


MM_CLINIC_ID = "market-mall-denture"


def _sign(signing_key, body_bytes, ts):
    msg = ts.encode() + b"|" + body_bytes
    return base64.b64encode(signing_key.sign(msg).signature).decode()


def _seed_reminder_for_appointment(
    test_client,
    db_session,
    *,
    hours_out: float = 24.0,
    clinic_id: str = MM_CLINIC_ID,
    provider_id: int = 101,
    phone: str = "+14035550001",
    with_token: bool = True,
) -> tuple[str, str]:
    """Seed a SCHEDULED appointment + a 'sent' AppointmentReminder for it.

    Returns (appointment_id, patient_phone). Mirrors the helper pattern in
    tests/api/test_cron_reminders.py::_seed_appointment, then adds a
    reminder row in the exact state the inbound webhook expects to match
    on (status=sent, sent_at < now, reply_received_at IS NULL).
    """
    patient = Patient(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        first_name="Asim",
        last_name="K",
        phone=phone,
    )
    db_session.add(patient)
    db_session.flush()

    # start_time stored naive UTC (matches existing DB convention)
    now_utc = datetime.utcnow()
    start = now_utc + timedelta(hours=hours_out, seconds=60)
    end = start + timedelta(minutes=30)

    appt = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        patient_id=patient.id,
        provider_id=provider_id,
        start_time=start,
        end_time=end,
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(appt)
    db_session.flush()

    reminder = AppointmentReminder(
        id=str(uuid.uuid4()),
        appointment_id=appt.id,
        channel="sms",
        offset_minutes=24 * 60,
        scheduled_at=(now_utc - timedelta(minutes=10)),
        sent_at=(now_utc - timedelta(minutes=5)),
        status="sent",
        provider="telnyx",
        outbound_message_id="msg_outbound_seed",
        reschedule_token=(str(uuid.uuid4()) if with_token else None),
        reschedule_token_expires_at=(start + timedelta(hours=48)),
    )
    db_session.add(reminder)
    db_session.commit()
    return appt.id, phone


def _full_signed_webhook_post(client, signing_key, *, from_phone, text):
    """Helper: build + send a signed Telnyx 'message.received' webhook."""
    body = json.dumps(
        {
            "data": {
                "event_type": "message.received",
                "payload": {
                    "from": {"phone_number": from_phone},
                    "to": [{"phone_number": "+14035550000"}],
                    "text": text,
                    "id": f"msg_in_{text[:4]}",
                },
            }
        }
    ).encode()
    ts = str(int(time.time()))
    sig = _sign(signing_key, body, ts)
    return client.post(
        "/webhooks/telnyx/sms-inbound",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        },
    )


def test_webhook_rejects_invalid_signature(client, monkeypatch):
    """Bad signature -> 401."""
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", base64.b64encode(b"\x00" * 32).decode())
    body = json.dumps({"data": {"event_type": "message.received", "payload": {}}}).encode()
    ts = str(int(time.time()))
    resp = client.post(
        "/webhooks/telnyx/sms-inbound",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": "bogus",
            "Telnyx-Timestamp": ts,
        },
    )
    assert resp.status_code == 401


def test_webhook_returns_200_on_unmatched_phone_falls_through(client, db_session, monkeypatch):
    """Valid signature + no matching reminder -> 200 fallthrough."""
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY",
        base64.b64encode(bytes(signing_key.verify_key)).decode(),
    )
    body_dict = {
        "data": {
            "event_type": "message.received",
            "payload": {
                "from": {"phone_number": "+19999999999"},  # no reminder for this number
                "to": [{"phone_number": "+14035550000"}],
                "text": "yes",
                "id": "msg_in_1",
            },
        }
    }
    body = json.dumps(body_dict).encode()
    ts = str(int(time.time()))
    sig = _sign(signing_key, body, ts)
    resp = client.post(
        "/webhooks/telnyx/sms-inbound",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["routed_to"] == "fallthrough"


def test_webhook_ignores_non_message_received_events(client, monkeypatch):
    """Telnyx also sends delivery-status events; only 'message.received' is acted on."""
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY",
        base64.b64encode(bytes(signing_key.verify_key)).decode(),
    )
    body = json.dumps({"data": {"event_type": "message.sent", "payload": {}}}).encode()
    ts = str(int(time.time()))
    sig = _sign(signing_key, body, ts)
    resp = client.post(
        "/webhooks/telnyx/sms-inbound",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["routed_to"] == "ignored_event"


# ---------------------------------------------------------------------------
# Task B8: action dispatch on reminder match
# ---------------------------------------------------------------------------


def test_webhook_confirmed_marks_appointment_and_sends_ack(
    client_market_mall, db_session, monkeypatch
):
    """YES -> status=CONFIRMED, ack sent, reply persisted."""
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode()
    )
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    appt_id, phone = _seed_reminder_for_appointment(
        client_market_mall, db_session, hours_out=24, phone="+14035550001"
    )
    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_ack_1"
    ) as ack_send:
        resp = _full_signed_webhook_post(
            client_market_mall, signing_key, from_phone=phone, text="yes"
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["routed_to"] == "reminder_match"
    assert body["intent"] == "confirmed"

    appt = db_session.query(Appointment).filter_by(id=appt_id).first()
    assert appt.status == AppointmentStatus.CONFIRMED

    rem = (
        db_session.query(AppointmentReminder)
        .filter_by(appointment_id=appt_id)
        .first()
    )
    assert rem.reply_parsed_intent == "confirmed"
    assert rem.reply_raw_text == "yes"
    assert rem.reply_received_at is not None
    ack_send.assert_called_once()


def test_webhook_cancelled_marks_appointment_and_sends_ack(
    client_market_mall, db_session, monkeypatch
):
    """NO -> status=CANCELLED, ack sent with reschedule link."""
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode()
    )
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    appt_id, phone = _seed_reminder_for_appointment(
        client_market_mall, db_session, hours_out=24, phone="+14035550002"
    )
    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_ack_2"
    ) as ack_send:
        resp = _full_signed_webhook_post(
            client_market_mall, signing_key, from_phone=phone, text="no"
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["intent"] == "cancelled"

    appt = db_session.query(Appointment).filter_by(id=appt_id).first()
    assert appt.status == AppointmentStatus.CANCELLED
    ack_send.assert_called_once()
    ack_body = ack_send.call_args.kwargs.get("body", "")
    # ack-cancelled template contains the reschedule link placeholder
    assert "/p/reschedule/" in ack_body


def test_webhook_reschedule_keeps_status_scheduled_and_sends_link(
    client_market_mall, db_session, monkeypatch
):
    """RESCHEDULE -> status stays SCHEDULED, ack contains reschedule link."""
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode()
    )
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    appt_id, phone = _seed_reminder_for_appointment(
        client_market_mall, db_session, hours_out=24, phone="+14035550003"
    )
    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_ack_3"
    ) as ack_send:
        resp = _full_signed_webhook_post(
            client_market_mall, signing_key, from_phone=phone, text="reschedule"
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["intent"] == "reschedule_requested"

    appt = db_session.query(Appointment).filter_by(id=appt_id).first()
    assert appt.status == AppointmentStatus.SCHEDULED
    ack_send.assert_called_once()
    ack_body = ack_send.call_args.kwargs.get("body", "")
    assert "/p/reschedule/" in ack_body


def test_webhook_ambiguous_first_time_sends_disambig_then_suppresses(
    client_market_mall, db_session, monkeypatch
):
    """First ambiguous reply -> ack sent + counter=1.
    Second ambiguous reply -> no ack + counter=2.
    """
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode()
    )
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    appt_id, phone = _seed_reminder_for_appointment(
        client_market_mall, db_session, hours_out=24, phone="+14035550004"
    )
    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_ack"
    ) as ack_send:
        # First freeform reply
        r1 = _full_signed_webhook_post(
            client_market_mall,
            signing_key,
            from_phone=phone,
            text="blah blah unclear text",
        )
        # Reset reply_received_at so the second post still matches the
        # AppointmentReminder.reply_received_at IS NULL filter on lookup.
        rem = (
            db_session.query(AppointmentReminder)
            .filter_by(appointment_id=appt_id)
            .first()
        )
        rem.reply_received_at = None
        db_session.commit()
        # Second freeform reply
        r2 = _full_signed_webhook_post(
            client_market_mall,
            signing_key,
            from_phone=phone,
            text="more unclear text",
        )
    assert r1.status_code == 200 and r1.json()["intent"] == "ambiguous"
    assert r2.status_code == 200 and r2.json()["intent"] == "ambiguous"
    # First reply triggers an ack; second does NOT.
    assert ack_send.call_count == 1

    rem = (
        db_session.query(AppointmentReminder)
        .filter_by(appointment_id=appt_id)
        .first()
    )
    assert rem.ambiguous_reply_count == 2
