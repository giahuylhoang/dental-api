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


def _seed_due_sms_reminder_with_start_time(db_session, start_time):
    """Seed the default clinic + patient + appointment with an explicit,
    naive-UTC ``start_time`` and a pending SMS reminder due now.

    Mirrors :func:`_seed_due_sms_reminder` but lets the caller pin the
    appointment time so the rendered SMS body can be asserted against the
    clinic-local (America/Edmonton) wall-clock time.
    """
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

    appt = Appointment(
        id=str(uuid.uuid4()),
        clinic_id=clinic_id,
        patient_id=patient.id,
        provider_id=provider.id,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(appt)
    db_session.flush()

    now = datetime.utcnow()
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


def test_reminder_sms_body_renders_clinic_local_not_utc(db_session, db_engine):
    """The SMS body must render the appointment in the clinic's local tz
    (America/Edmonton), not the stored naive-UTC value.

    A summer date (July) pins MDT = UTC-6 deterministically, so naive UTC
    20:00:00 must render as 14:00 local in the body. Before the fix the body
    emitted the raw stored UTC (``20:00``)."""
    # July 15, 14:00 Edmonton/MDT == 20:00 UTC. Stored naive UTC.
    start_time = datetime(2026, 7, 15, 20, 0, 0)
    _seed_due_sms_reminder_with_start_time(db_session, start_time)

    factory = _tracking_factory(db_engine, checked_out=None)
    due = reminder_scheduler._collect_due_reminders(factory)

    sms_items = [d for d in due if d.channel == "sms" and not d.precheck_error]
    assert sms_items, "expected at least one due SMS reminder with a body"
    body = sms_items[0].body

    assert "14:00" in body, f"expected clinic-local 14:00 in body, got: {body!r}"
    assert "20:00" not in body, f"UTC value 20:00 leaked into body: {body!r}"


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
