"""Tests for POST /cron/reminders/scan."""

import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from database.models import (
    Appointment,
    AppointmentStatus,
    Patient,
    Provider,
)


MM_CLINIC_ID = "market-mall-denture"


def _internal_secret_headers():
    return {"X-Internal-Secret": os.getenv("DENTAL_API_INTERNAL_SECRET", "test_secret")}


def _seed_appointment(
    test_client,
    db_session,
    *,
    hours_out: float,
    clinic_id: str = MM_CLINIC_ID,
    provider_id: int = 101,
    phone: str = "+14035551234",
    status=AppointmentStatus.SCHEDULED,
    extra_seconds: int = 60,
) -> str:
    """Seed a SCHEDULED appointment N hours from now (naive UTC). Returns appt id.

    `extra_seconds` is added so the appointment lands comfortably inside the
    scan's 5-minute window even after small clock drift between test
    setup and scan execution.
    """
    # Patient
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
    start = now_utc + timedelta(hours=hours_out, seconds=extra_seconds)
    end = start + timedelta(minutes=30)

    appt = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        patient_id=patient.id,
        provider_id=provider_id,
        start_time=start,
        end_time=end,
        status=status,
    )
    db_session.add(appt)
    db_session.commit()
    return appt.id


def test_scan_creates_reminder_for_appointment_24h_out(
    client_market_mall, db_session, monkeypatch
):
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test_secret")
    # Quiet hours disabled (start==end) so the 24h-out appointment isn't deferred.
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")
    appt_id = _seed_appointment(client_market_mall, db_session, hours_out=24.0)

    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_42"
    ) as mock_send:
        resp = client_market_mall.post(
            "/cron/reminders/scan", headers=_internal_secret_headers()
        )

    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["sent_count"] == 1
    assert payload["candidates_total"] == 1

    from database.ops.models import AppointmentReminder

    row = (
        db_session.query(AppointmentReminder)
        .filter_by(appointment_id=appt_id)
        .first()
    )
    assert row is not None
    assert row.status == "sent"
    assert row.outbound_message_id == "msg_42"
    assert row.channel == "sms"
    assert row.offset_minutes == 24 * 60
    assert row.reschedule_token  # token generated
    mock_send.assert_called_once()


def test_scan_skips_appointment_outside_offset_window(
    client_market_mall, db_session, monkeypatch
):
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test_secret")
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")
    # Too far (72h) — falls outside the 5-min selection window.
    _seed_appointment(
        client_market_mall, db_session, hours_out=72.0, phone="+14035550001"
    )
    # Too close (2h) — within selection window only if offset were ~2h, so it
    # also falls outside the 24h offset window. Verifies pickup is strictly
    # gated by offset, not by appt proximity.
    _seed_appointment(
        client_market_mall, db_session, hours_out=2.0, phone="+14035550002"
    )

    with patch("clients.telnyx_messaging.send_message", return_value="msg") as mock_send:
        resp = client_market_mall.post(
            "/cron/reminders/scan", headers=_internal_secret_headers()
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["sent_count"] == 0
    assert body["candidates_total"] == 0
    mock_send.assert_not_called()


def test_scan_idempotent_under_overlapping_runs(
    client_market_mall, db_session, monkeypatch
):
    """Second scan over the same window finds nothing new — dedup on (appointment_id, channel)."""
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test_secret")
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")
    _seed_appointment(client_market_mall, db_session, hours_out=24.0)

    with patch("clients.telnyx_messaging.send_message", return_value="msg"):
        r1 = client_market_mall.post(
            "/cron/reminders/scan", headers=_internal_secret_headers()
        )
        r2 = client_market_mall.post(
            "/cron/reminders/scan", headers=_internal_secret_headers()
        )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["sent_count"] == 1
    assert r2.json()["sent_count"] == 0


def test_scan_skip_too_late_when_min_lead_violated(
    client_market_mall, db_session, monkeypatch
):
    """If REMINDER_OFFSET is small and the appointment falls within MIN_LEAD_MINUTES,
    record a skipped_too_late row and do not send."""
    # Offset 1h → target_send = appt - 1h. For an appt 1h out, target_send = now,
    # and (appt - MIN_LEAD_MINUTES) = appt - 30min, so target_send (now) >= appt - 30min
    # → skip-too-late triggers.
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "1")
    monkeypatch.setenv("MIN_LEAD_MINUTES", "120")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test_secret")
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")
    appt_id = _seed_appointment(client_market_mall, db_session, hours_out=1.0)

    with patch("clients.telnyx_messaging.send_message", return_value="msg") as mock_send:
        resp = client_market_mall.post(
            "/cron/reminders/scan", headers=_internal_secret_headers()
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["skipped_too_late"] == 1
    assert body["sent_count"] == 0
    mock_send.assert_not_called()

    from database.ops.models import AppointmentReminder

    row = (
        db_session.query(AppointmentReminder)
        .filter_by(appointment_id=appt_id)
        .first()
    )
    assert row is not None
    assert row.status == "skipped_too_late"


def test_scan_records_failed_when_provider_returns_none(
    client_market_mall, db_session, monkeypatch
):
    """If send_sms_raw returns None (provider failed), status='failed' row is recorded."""
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test_secret")
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")
    appt_id = _seed_appointment(client_market_mall, db_session, hours_out=24.0)

    with patch("clients.telnyx_messaging.send_message", return_value=None):
        resp = client_market_mall.post(
            "/cron/reminders/scan", headers=_internal_secret_headers()
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["sent_count"] == 0

    from database.ops.models import AppointmentReminder

    row = (
        db_session.query(AppointmentReminder)
        .filter_by(appointment_id=appt_id)
        .first()
    )
    assert row is not None
    assert row.status == "failed"
    assert row.outbound_message_id is None


def test_scan_forwards_clinic_sms_from_number_to_send(
    client_market_mall, db_session, monkeypatch
):
    """Cron picks up clinic.sms_from_number and forwards it to send_sms_raw
    so the reminder is sent from the clinic's own DID (not the env default)."""
    from database.models import Clinic

    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test_secret")
    monkeypatch.setenv("QUIET_HOURS_START", "0")
    monkeypatch.setenv("QUIET_HOURS_END", "0")

    clinic = db_session.query(Clinic).filter(Clinic.id == MM_CLINIC_ID).first()
    clinic.sms_from_number = "+14035550000"
    db_session.commit()

    _seed_appointment(client_market_mall, db_session, hours_out=24.0)

    with patch(
        "clients.telnyx_messaging.send_message", return_value="msg_clinic_did"
    ) as mock_send:
        resp = client_market_mall.post(
            "/cron/reminders/scan", headers=_internal_secret_headers()
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["sent_count"] == 1
    mock_send.assert_called_once()
    assert mock_send.call_args.kwargs.get("from_") == "+14035550000"
