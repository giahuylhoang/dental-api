"""Test reminder scheduler: dispatch, failure, idempotency."""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

from database.models import Patient, Provider, Appointment, AppointmentStatus, DEFAULT_CLINIC_ID
from database.ops.models import AppointmentReminder


def _make_appointment(db, start=None):
    patient = Patient(clinic_id=DEFAULT_CLINIC_ID, first_name="Rem", phone="5551234")
    db.add(patient)
    db.flush()
    provider = Provider(clinic_id=DEFAULT_CLINIC_ID, name="Dr Rem")
    db.add(provider)
    db.flush()
    if start is None:
        start = datetime.utcnow() + timedelta(hours=24)
    apt = Appointment(
        clinic_id=DEFAULT_CLINIC_ID,
        patient_id=patient.id,
        provider_id=provider.id,
        start_time=start,
        end_time=start + timedelta(hours=1),
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(apt)
    db.flush()
    return apt, patient


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_reminder_dispatched_when_due(db_session):
    """Reminder with scheduled_at in the past fires and is marked sent."""
    apt, patient = _make_appointment(db_session)
    reminder = AppointmentReminder(
        appointment_id=apt.id,
        channel="sms",
        offset_minutes=60,
        scheduled_at=datetime.utcnow() - timedelta(seconds=10),
        status="pending",
    )
    db_session.add(reminder)
    db_session.commit()
    reminder_id = reminder.id

    with patch("clients.sms_client._send_sms_sync", return_value=True):
        from api.v2.scheduling.reminder_scheduler import _dispatch_due_reminders

        def _get_db():
            yield db_session

        _run(_dispatch_due_reminders(_get_db))

    db_session.expire_all()
    updated = db_session.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
    assert updated.status == "sent"
    assert updated.sent_at is not None


def test_reminder_failure_marks_failed(db_session):
    """SMS failure → reminder marked failed with reason."""
    apt, patient = _make_appointment(db_session)
    reminder = AppointmentReminder(
        appointment_id=apt.id,
        channel="sms",
        offset_minutes=60,
        scheduled_at=datetime.utcnow() - timedelta(seconds=10),
        status="pending",
    )
    db_session.add(reminder)
    db_session.commit()
    reminder_id = reminder.id

    with patch("clients.sms_client._send_sms_sync", return_value=False):
        from api.v2.scheduling.reminder_scheduler import _dispatch_due_reminders

        def _get_db():
            yield db_session

        _run(_dispatch_due_reminders(_get_db))

    db_session.expire_all()
    updated = db_session.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
    assert updated.status == "failed"
    assert updated.failure_reason is not None


def test_reminder_not_resent_after_sent(db_session):
    """Already-sent reminder is not dispatched again (idempotent)."""
    apt, patient = _make_appointment(db_session)
    sent_at = datetime.utcnow() - timedelta(minutes=5)
    reminder = AppointmentReminder(
        appointment_id=apt.id,
        channel="sms",
        offset_minutes=60,
        scheduled_at=datetime.utcnow() - timedelta(seconds=10),
        status="sent",
        sent_at=sent_at,
    )
    db_session.add(reminder)
    db_session.commit()
    reminder_id = reminder.id

    with patch("clients.sms_client._send_sms_sync", return_value=True) as mock_sms:
        from api.v2.scheduling.reminder_scheduler import _dispatch_due_reminders

        def _get_db():
            yield db_session

        _run(_dispatch_due_reminders(_get_db))

    mock_sms.assert_not_called()
    db_session.expire_all()
    updated = db_session.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()
    # sent_at should be unchanged (same value)
    assert updated.status == "sent"
