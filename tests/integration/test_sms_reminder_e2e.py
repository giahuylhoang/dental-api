"""End-to-end: scan endpoint -> SMS sent -> patient replies -> status update + handoff.

Unlike the per-component tests in tests/api/test_cron_reminders.py,
tests/api/test_telnyx_webhook.py, and tests/api/test_reschedule_link.py,
these chain multiple HTTP endpoints together against the FastAPI app via
TestClient and prove the full pipeline works as a single integrated flow.
"""

import base64
import json
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import nacl.signing

from database.models import (
    Appointment,
    AppointmentStatus,
    Clinic,
    Patient,
    Provider,
)
from database.ops.models import AppointmentReminder


MM_CLINIC_ID = "market-mall-denture"
MM_SMS_FROM = "+14035550000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _signed_webhook(signing_key, *, from_phone, to_phone, text):
    """Build (body, headers) for a signed Telnyx 'message.received' webhook POST."""
    body = json.dumps(
        {
            "data": {
                "event_type": "message.received",
                "payload": {
                    "from": {"phone_number": from_phone},
                    "to": [{"phone_number": to_phone}],
                    "text": text,
                    "id": f"msg_{text[:6]}_{uuid.uuid4().hex[:6]}",
                },
            }
        }
    ).encode()
    ts = str(int(time.time()))
    sig = base64.b64encode(
        signing_key.sign(ts.encode() + b"|" + body).signature
    ).decode()
    return body, {
        "Content-Type": "application/json",
        "Telnyx-Signature-ED25519": sig,
        "Telnyx-Timestamp": ts,
    }


def _setup_telnyx_env(monkeypatch, signing_key):
    """Common env setup. Forces SMS_PROVIDER=telnyx and seeds the public key.

    Also disables quiet-hours (start==end==0) so a 25h-out appointment isn't
    deferred regardless of wall-clock time when the suite runs, and patches
    INTERNAL_SECRET in place (require_internal_secret captures it at module
    load).
    """
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("MIN_LEAD_MINUTES", "30")
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")
    monkeypatch.setenv("TELNYX_API_KEY", "test-key")
    monkeypatch.setenv("TELNYX_MESSAGING_PROFILE_ID", "test-profile")
    monkeypatch.setenv("TELNYX_SMS_FROM_NUMBER", MM_SMS_FROM)
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY",
        base64.b64encode(bytes(signing_key.verify_key)).decode(),
    )
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "INT")
    # require_internal_secret captures INTERNAL_SECRET at module load — patch in place.
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "INT")


def _seed_market_mall_with_sms_number(db_session):
    """Set Clinic.sms_from_number on market-mall-denture for inbound lookups."""
    clinic = db_session.query(Clinic).filter_by(id=MM_CLINIC_ID).first()
    assert clinic is not None, "client_market_mall fixture should have seeded clinic"
    clinic.sms_from_number = MM_SMS_FROM
    db_session.commit()


def _seed_patient_and_appointment(
    db_session,
    *,
    phone: str,
    hours_out: float,
    clinic_id: str = MM_CLINIC_ID,
    provider_id: int = 101,
) -> tuple[str, str]:
    """Create a patient at the clinic + a SCHEDULED appointment N hours out.

    Mirrors tests/api/test_cron_reminders.py::_seed_appointment. Returns
    (patient_id, appointment_id). Adds 60 extra seconds so the appointment
    lands comfortably inside the scan's 5-minute window.
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
    db_session.commit()
    return patient.id, appt.id


# ---------------------------------------------------------------------------
# Test 1: YES flow
# ---------------------------------------------------------------------------


def test_yes_flow_end_to_end(client_market_mall, db_session, monkeypatch):
    """scan -> SMS sent -> reply YES -> CONFIRMED + ack."""
    signing_key = nacl.signing.SigningKey.generate()
    _setup_telnyx_env(monkeypatch, signing_key)
    _seed_market_mall_with_sms_number(db_session)
    patient_id, appt_id = _seed_patient_and_appointment(
        db_session, phone="+14035550001", hours_out=24
    )

    # 1. Cron scan should create + send a reminder
    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_out_1"
    ) as scan_send:
        scan_resp = client_market_mall.post(
            "/cron/reminders/scan",
            headers={"X-Internal-Secret": "INT"},
        )
    assert scan_resp.status_code == 200, scan_resp.text
    assert scan_resp.json()["sent_count"] == 1
    scan_send.assert_called_once()

    rem = (
        db_session.query(AppointmentReminder)
        .filter_by(appointment_id=appt_id)
        .first()
    )
    assert rem is not None
    assert rem.status == "sent"
    assert rem.outbound_message_id == "msg_out_1"
    assert rem.reschedule_token is not None

    # 2. Patient replies YES via webhook
    body, headers = _signed_webhook(
        signing_key,
        from_phone="+14035550001",
        to_phone=MM_SMS_FROM,
        text="yes",
    )
    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_ack_1"
    ) as ack_send:
        webhook_resp = client_market_mall.post(
            "/webhooks/telnyx/sms-inbound", content=body, headers=headers
        )
    assert webhook_resp.status_code == 200, webhook_resp.text
    data = webhook_resp.json()
    assert data["routed_to"] == "reminder_match"
    assert data["intent"] == "confirmed"

    # 3. Appointment is CONFIRMED, ack SMS was attempted
    db_session.expire_all()  # force reload from DB
    appt = db_session.query(Appointment).filter_by(id=appt_id).first()
    assert appt.status == AppointmentStatus.CONFIRMED
    ack_send.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: RESCHEDULE flow
# ---------------------------------------------------------------------------


def test_reschedule_flow_redirects_via_token(
    client_market_mall, db_session, monkeypatch
):
    """scan -> reply RESCHEDULE -> GET /p/reschedule/{token} -> 302 to market-mall."""
    signing_key = nacl.signing.SigningKey.generate()
    _setup_telnyx_env(monkeypatch, signing_key)
    monkeypatch.setenv(
        "MARKET_MALL_WEBSITE_BASE_URL", "https://marketmall.example.com"
    )
    monkeypatch.setenv(
        "RESCHEDULE_SESSION_SIGNING_KEY",
        base64.b64encode(b"\x00" * 32).decode(),
    )
    _seed_market_mall_with_sms_number(db_session)
    patient_id, appt_id = _seed_patient_and_appointment(
        db_session, phone="+14035550001", hours_out=24
    )

    # 1. Cron scan -> SMS sent
    with patch("clients.telnyx_messaging.send_message", return_value="msg_out"):
        scan_resp = client_market_mall.post(
            "/cron/reminders/scan",
            headers={"X-Internal-Secret": "INT"},
        )
    assert scan_resp.status_code == 200, scan_resp.text
    assert scan_resp.json()["sent_count"] == 1

    # 2. Reply "reschedule"
    body, headers = _signed_webhook(
        signing_key,
        from_phone="+14035550001",
        to_phone=MM_SMS_FROM,
        text="reschedule",
    )
    with patch("clients.telnyx_messaging.send_message", return_value="msg_ack"):
        webhook_resp = client_market_mall.post(
            "/webhooks/telnyx/sms-inbound", content=body, headers=headers
        )
    assert webhook_resp.status_code == 200, webhook_resp.text
    assert webhook_resp.json()["intent"] == "reschedule_requested"

    # 3. Appointment stays SCHEDULED (status doesn't flip for reschedule_requested)
    db_session.expire_all()
    appt = db_session.query(Appointment).filter_by(id=appt_id).first()
    assert appt.status == AppointmentStatus.SCHEDULED

    # 4. Read the reschedule_token from the reminder row
    rem = (
        db_session.query(AppointmentReminder)
        .filter_by(appointment_id=appt_id)
        .first()
    )
    assert rem.reschedule_token is not None
    token = rem.reschedule_token

    # 5. GET the public link -> 302 to market-mall
    link_resp = client_market_mall.get(
        f"/p/reschedule/{token}", follow_redirects=False
    )
    assert link_resp.status_code == 302, link_resp.text
    location = link_resp.headers["location"]
    assert location.startswith(
        "https://marketmall.example.com/reschedule?session="
    )
