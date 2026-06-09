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


# ---------------------------------------------------------------------------
# POST /p/reschedule/{token}/commit
# ---------------------------------------------------------------------------


def _seed_hold(
    db_session,
    *,
    patient_id: str | None = None,
    clinic_id: str = MM_CLINIC_ID,
    provider_id: int = 101,
    hours_out: int = 72,
) -> str:
    """Create a PENDING hold-Appointment (the holds-foundation 'hold' shape).

    The holds system stores holds as Appointment rows with status=PENDING and
    hold_expiry_at set. Returns the appointment id (= the 'hold_id' that the
    market-mall BFF passes back to commit).

    If patient_id is None, a fresh patient row is seeded.
    """
    if patient_id is None:
        patient = Patient(
            id=str(uuid.uuid4()),
            clinic_id=clinic_id,
            first_name="Hold",
            last_name="Patient",
            phone="+14035550099",
        )
        db_session.add(patient)
        db_session.flush()
        patient_id = patient.id

    now_utc = datetime.utcnow()
    start = now_utc + timedelta(hours=hours_out)
    end = start + timedelta(minutes=30)
    hold = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        patient_id=patient_id,
        provider_id=provider_id,
        start_time=start,
        end_time=end,
        status=AppointmentStatus.PENDING,
        hold_expiry_at=now_utc + timedelta(hours=24),
        source="booking-web-hold",
    )
    db_session.add(hold)
    db_session.commit()
    return hold.id


def test_post_commit_swaps_appointment_and_marks_token_used(
    client_market_mall, db_session, monkeypatch
):
    """Happy path: valid token + valid hold → old RESCHEDULED, new SCHEDULED, token used."""
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "INT")
    monkeypatch.setenv(
        "RESCHEDULE_SESSION_SIGNING_KEY",
        base64.b64encode(b"\x00" * 32).decode(),
    )
    old_appt_id = _seed_reminder_with_token(db_session, token="tok_commit_ok")
    # Hold must belong to the same patient + clinic as the old appointment.
    old_appt = (
        db_session.query(Appointment).filter_by(id=old_appt_id).first()
    )
    hold_id = _seed_hold(
        db_session, patient_id=old_appt.patient_id, clinic_id=old_appt.clinic_id
    )

    resp = client_market_mall.post(
        "/p/reschedule/tok_commit_ok/commit",
        json={"hold_id": hold_id},
        headers={"X-Internal-Secret": "INT"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["appointment_id"] == hold_id
    assert "start_time" in body

    db_session.expire_all()
    old_after = (
        db_session.query(Appointment).filter_by(id=old_appt_id).first()
    )
    assert old_after.status == AppointmentStatus.RESCHEDULED
    new_after = db_session.query(Appointment).filter_by(id=hold_id).first()
    assert new_after.status == AppointmentStatus.SCHEDULED
    assert new_after.hold_expiry_at is None
    rem = (
        db_session.query(AppointmentReminder)
        .filter_by(reschedule_token="tok_commit_ok")
        .first()
    )
    assert rem.reschedule_token_used_at is not None


def test_post_commit_410_on_used_token(
    client_market_mall, db_session, monkeypatch
):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "INT")
    monkeypatch.setenv(
        "RESCHEDULE_SESSION_SIGNING_KEY",
        base64.b64encode(b"\x00" * 32).decode(),
    )
    _seed_reminder_with_token(
        db_session, token="tok_used2", used_at=datetime.utcnow()
    )
    resp = client_market_mall.post(
        "/p/reschedule/tok_used2/commit",
        json={"hold_id": "anything"},
        headers={"X-Internal-Secret": "INT"},
    )
    assert resp.status_code == 410


def test_post_commit_409_on_hold_mismatch(
    client_market_mall, db_session, monkeypatch
):
    """Hold belongs to a different patient → 409."""
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "INT")
    monkeypatch.setenv(
        "RESCHEDULE_SESSION_SIGNING_KEY",
        base64.b64encode(b"\x00" * 32).decode(),
    )
    _seed_reminder_with_token(db_session, token="tok_mismatch")
    # _seed_hold with no patient_id => fresh different patient.
    hold_id = _seed_hold(db_session, clinic_id=MM_CLINIC_ID)
    resp = client_market_mall.post(
        "/p/reschedule/tok_mismatch/commit",
        json={"hold_id": hold_id},
        headers={"X-Internal-Secret": "INT"},
    )
    assert resp.status_code == 409


def test_post_commit_401_without_internal_secret(
    client_market_mall, db_session, monkeypatch
):
    monkeypatch.setattr("api.dependencies.auth.INTERNAL_SECRET", "INT")
    _seed_reminder_with_token(db_session, token="tok_noauth")
    resp = client_market_mall.post(
        "/p/reschedule/tok_noauth/commit", json={"hold_id": "any"}
    )
    # require_internal_secret returns 401; accept 403 too if dep changes shape.
    assert resp.status_code in (401, 403)
