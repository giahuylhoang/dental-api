"""Tests for the background reminder scheduler (api/v2/scheduling/reminder_scheduler.py).

Focus of Task 1.1: the scheduler must NOT hold a SQLAlchemy session (and thus a
pooled DB connection) across the blocking Twilio/email send. The 2026-06-19
production incident was a pool exhaustion caused exactly by holding the session
across `_send_sms_sync`. These tests pin the three-phase contract:
collect (own session) -> send (no session) -> persist (own session).
"""

import asyncio
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

import clients.sms_client as _sms_client
from api.v2.scheduling import reminder_scheduler
from database.models import Appointment, AppointmentStatus, Clinic, Patient, Provider
from database.ops.models import AppointmentReminder


def _seed_due_sms_reminder(db_session):
    """Seed a clinic + patient + appointment + a pending SMS reminder due now."""
    clinic_id = "default"
    if db_session.query(Clinic).filter(Clinic.id == clinic_id).first() is None:
        db_session.add(Clinic(id=clinic_id, name="Default", timezone="America/Edmonton"))
        db_session.flush()

    provider = Provider(clinic_id=clinic_id, name="Soheil", title="Denturist", is_active=True)
    db_session.add(provider)
    db_session.flush()

    patient = Patient(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        first_name="Jane",
        last_name="Doe",
        phone="+14035551234",
    )
    db_session.add(patient)
    db_session.flush()

    now = datetime.utcnow()
    appt = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        patient_id=patient.id,
        provider_id=provider.id,
        start_time=now + timedelta(hours=24),
        end_time=now + timedelta(hours=24, minutes=30),
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(appt)
    db_session.flush()

    reminder = AppointmentReminder(
        id=str(uuid.uuid4()),
        appointment_id=appt.id,
        channel="sms",
        offset_minutes=24 * 60,
        scheduled_at=now + timedelta(seconds=10),  # inside the now..now+60s window
        status="pending",
        provider="telnyx",
    )
    db_session.add(reminder)
    db_session.commit()
    return reminder.id


def _tracking_factory(db_engine, checked_out):
    """A get_db-style factory bound to the test engine.

    Pool checkout/checkin events on the engine let us observe whether ANY
    DB connection is held at a given moment — the precise signal for "is a
    session open right now".
    """
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def factory():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    return factory


def test_dispatch_releases_session_before_blocking_send(db_session, db_engine, monkeypatch):
    reminder_id = _seed_due_sms_reminder(db_session)

    checked_out = {"n": 0, "max_during_send": -1}

    @event.listens_for(db_engine, "checkout")
    def _co(*a):  # noqa: ANN001
        checked_out["n"] += 1

    @event.listens_for(db_engine, "checkin")
    def _ci(*a):  # noqa: ANN001
        checked_out["n"] -= 1

    def slow_send(to_phone, body):
        # Capture how many DB connections are checked out at the moment of the
        # (blocking) send. After the fix this MUST be zero — the collect session
        # is released before we get here.
        checked_out["max_during_send"] = max(
            checked_out["max_during_send"], checked_out["n"]
        )
        return True

    monkeypatch.setattr(_sms_client, "_send_sms_sync", slow_send)

    factory = _tracking_factory(db_engine, checked_out)
    asyncio.run(reminder_scheduler._dispatch_due_reminders(factory))

    # 1) No session/connection was held across the blocking send.
    assert checked_out["max_during_send"] == 0, (
        "DB connection was held across the blocking SMS send "
        f"(observed {checked_out['max_during_send']} checked-out connection(s))"
    )

    # 2) The result was persisted afterward (in a separate session).
    row = db_session.query(AppointmentReminder).filter_by(id=reminder_id).one()
    assert row.status == "sent"
    assert row.sent_at is not None
