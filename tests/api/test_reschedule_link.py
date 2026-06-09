"""Tests for GET /p/reschedule/{token}."""

import base64
import uuid
from datetime import datetime, timedelta

from database.models import Appointment, AppointmentStatus, Clinic, Patient
from database.ops.models import AppointmentReminder


MM_CLINIC_ID = "market-mall-denture"


def _seed_reminder_with_token(
    db_session,
    *,
    token: str,
    expires_at=None,
    used_at=None,
    clinic_id: str = MM_CLINIC_ID,
    provider_id: int = 101,
) -> str:
    """Create a SCHEDULED appointment + matching reminder row with the given token.

    Mirrors the helper pattern in tests/api/test_telnyx_webhook.py::
    _seed_reminder_for_appointment — patient + appointment + reminder against
    the in-memory SQLite test DB. Returns the appointment id.
    """
    patient = Patient(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        first_name="Asim",
        last_name="K",
        phone="+14035550042",
    )
    db_session.add(patient)
    db_session.flush()

    now_utc = datetime.utcnow()
    start = now_utc + timedelta(hours=24, seconds=60)
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

    if expires_at is None:
        expires_at = start + timedelta(hours=48)

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
        reschedule_token=token,
        reschedule_token_expires_at=expires_at,
        reschedule_token_used_at=used_at,
    )
    db_session.add(reminder)
    db_session.commit()
    return appt.id


def test_get_reschedule_valid_token_returns_302_to_market_mall(
    client_market_mall, db_session, monkeypatch
):
    """Valid token + valid market-mall URL env -> 302 with session query."""
    monkeypatch.setenv(
        "MARKET_MALL_WEBSITE_BASE_URL", "https://marketmall.example.com"
    )
    monkeypatch.setenv(
        "RESCHEDULE_SESSION_SIGNING_KEY",
        base64.b64encode(b"\x00" * 32).decode(),
    )
    _seed_reminder_with_token(db_session, token="tok_valid")

    resp = client_market_mall.get(
        "/p/reschedule/tok_valid", follow_redirects=False
    )
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert location.startswith(
        "https://marketmall.example.com/reschedule?session="
    )
    # The session blob should be non-empty base64-ish
    assert len(location.split("?session=")[1]) > 20


def test_get_reschedule_expired_token_returns_410(
    client_market_mall, db_session, monkeypatch
):
    monkeypatch.setenv(
        "RESCHEDULE_SESSION_SIGNING_KEY",
        base64.b64encode(b"\x00" * 32).decode(),
    )
    _seed_reminder_with_token(
        db_session,
        token="tok_expired",
        expires_at=datetime.utcnow() - timedelta(hours=1),
    )
    resp = client_market_mall.get("/p/reschedule/tok_expired")
    assert resp.status_code == 410


def test_get_reschedule_used_token_returns_410(
    client_market_mall, db_session, monkeypatch
):
    monkeypatch.setenv(
        "RESCHEDULE_SESSION_SIGNING_KEY",
        base64.b64encode(b"\x00" * 32).decode(),
    )
    _seed_reminder_with_token(
        db_session,
        token="tok_used",
        used_at=datetime.utcnow(),
    )
    resp = client_market_mall.get("/p/reschedule/tok_used")
    assert resp.status_code == 410


def test_get_reschedule_unknown_token_returns_404(client_market_mall):
    resp = client_market_mall.get("/p/reschedule/never_existed")
    assert resp.status_code == 404
