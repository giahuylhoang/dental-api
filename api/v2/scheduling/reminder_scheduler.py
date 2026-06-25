"""Background reminder scheduler: wakes every 60s, dispatches due reminders.

Connection-pool safety (2026-06-19 incident): dispatch is split into three
phases, each in its own short-lived session, so we NEVER hold a SQLAlchemy
session (and therefore a pooled DB connection) across the blocking Twilio/email
send:

  1. collect  — open a session, read due reminders + the data needed to build
                each message, close the session.
  2. send     — pure I/O against Twilio/email with NO DB session held.
  3. persist  — open a fresh session, write sent/failed back, close.

Holding the session across `_send_sms_sync` is exactly what exhausted the pool
on 2026-06-19 (QueuePool limit reached, every DB endpoint timed out).
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("dental-receptionist")

_scheduler_task = None


@dataclass
class _DueReminder:
    """In-memory snapshot of a due reminder — carries everything the send phase
    needs so no DB session is required during the blocking send."""
    reminder_id: str
    channel: str
    phone: Optional[str] = None
    email: Optional[str] = None
    body: Optional[str] = None
    precheck_error: Optional[str] = None


@dataclass
class _ReminderResult:
    reminder_id: str
    status: str  # "sent" | "failed"
    sent_at: Optional[datetime] = None
    failure_reason: Optional[str] = None


async def _run_scheduler(get_db_factory):
    """Loop: every 60s find pending reminders due in next 60s and dispatch."""
    while True:
        try:
            await _dispatch_due_reminders(get_db_factory)
        except Exception as e:
            logger.error("Reminder scheduler error: %s", e, exc_info=True)
        try:
            db = next(get_db_factory())
            try:
                expire_pending_holds(db)
            finally:
                db.close()
        except Exception as e:
            logger.error("Hold expiry sweep failed: %s", e, exc_info=True)
        await asyncio.sleep(60)


async def _dispatch_due_reminders(get_db_factory):
    """Dispatch due reminders in three phases, releasing the DB session before
    the blocking send (see module docstring / 2026-06-19 incident)."""
    due = _collect_due_reminders(get_db_factory)
    if not due:
        return
    results = _send_reminders(due)
    _persist_reminder_results(get_db_factory, results)


def _collect_due_reminders(get_db_factory) -> list[_DueReminder]:
    """Phase 1 — open a session, read due reminders + the patient/appointment
    data needed to build each message, then close the session. No sends here."""
    from database.ops.models import AppointmentReminder
    from database.models import Appointment, Patient, Clinic
    from services.tz_utils import to_clinic_local

    now = datetime.utcnow()
    window_end = now + timedelta(seconds=60)

    due: list[_DueReminder] = []
    db = next(get_db_factory())
    try:
        reminders = db.query(AppointmentReminder).filter(
            AppointmentReminder.status == "pending",
            AppointmentReminder.scheduled_at <= window_end,
            AppointmentReminder.scheduled_at >= now - timedelta(minutes=5),
        ).all()

        # Cache clinic rows by id so we don't issue an N+1 query per reminder.
        clinic_cache: dict = {}

        def _clinic_for(apt):
            if apt.clinic_id not in clinic_cache:
                clinic_cache[apt.clinic_id] = db.query(Clinic).filter(Clinic.id == apt.clinic_id).first()
            return clinic_cache[apt.clinic_id]

        for reminder in reminders:
            apt = db.query(Appointment).filter(Appointment.id == reminder.appointment_id).first()
            if not apt:
                due.append(_DueReminder(
                    reminder_id=reminder.id, channel=reminder.channel,
                    precheck_error="Appointment not found",
                ))
                continue

            patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()

            if reminder.channel == "sms" and patient and patient.phone:
                # apt.start_time is stored as naive UTC (Postgres
                # `timestamp without time zone`); render the body in the
                # appointment's clinic-local tz so the patient sees their
                # wall-clock time, not UTC.
                local = to_clinic_local(apt.start_time, _clinic_for(apt))
                body = f"Reminder: appointment on {local.strftime('%Y-%m-%d %H:%M')}"
                due.append(_DueReminder(
                    reminder_id=reminder.id, channel="sms",
                    phone=patient.phone, body=body,
                ))
            elif reminder.channel == "email" and patient and patient.email:
                due.append(_DueReminder(
                    reminder_id=reminder.id, channel="email",
                    email=patient.email,
                ))
            else:
                due.append(_DueReminder(
                    reminder_id=reminder.id, channel=reminder.channel,
                    precheck_error="No contact info",
                ))
    finally:
        db.close()

    return due


def _send_reminders(due: list[_DueReminder]) -> list[_ReminderResult]:
    """Phase 2 — pure I/O. Call Twilio/email with NO DB session held."""
    from clients.sms_client import _send_sms_sync

    results: list[_ReminderResult] = []
    for item in due:
        if item.precheck_error:
            results.append(_ReminderResult(
                reminder_id=item.reminder_id, status="failed",
                failure_reason=item.precheck_error,
            ))
            continue

        try:
            if item.channel == "sms":
                ok = _send_sms_sync(item.phone, item.body)
                if ok:
                    results.append(_ReminderResult(
                        reminder_id=item.reminder_id, status="sent",
                        sent_at=datetime.utcnow(),
                    ))
                else:
                    results.append(_ReminderResult(
                        reminder_id=item.reminder_id, status="failed",
                        failure_reason="SMS send failed",
                    ))
            elif item.channel == "email":
                logger.info("Email reminder stub: to=%s", item.email)
                results.append(_ReminderResult(
                    reminder_id=item.reminder_id, status="sent",
                    sent_at=datetime.utcnow(),
                ))
            else:
                results.append(_ReminderResult(
                    reminder_id=item.reminder_id, status="failed",
                    failure_reason="No contact info",
                ))
        except Exception as e:
            results.append(_ReminderResult(
                reminder_id=item.reminder_id, status="failed",
                failure_reason=str(e),
            ))

    return results


def _persist_reminder_results(get_db_factory, results: list[_ReminderResult]) -> None:
    """Phase 3 — open a fresh session, write sent/failed back, commit, close."""
    from database.ops.models import AppointmentReminder

    if not results:
        return

    db = next(get_db_factory())
    try:
        for result in results:
            reminder = db.query(AppointmentReminder).filter(
                AppointmentReminder.id == result.reminder_id
            ).first()
            if reminder is None:
                continue
            reminder.status = result.status
            reminder.sent_at = result.sent_at
            reminder.failure_reason = result.failure_reason
        db.commit()
    finally:
        db.close()


def expire_pending_holds(db) -> int:
    """Cancel PENDING holds whose hold_expiry_at has passed. Returns count cancelled."""
    from datetime import datetime
    from database.models import Appointment, AppointmentStatus
    now = datetime.utcnow()
    expired = (db.query(Appointment)
               .filter(Appointment.status == AppointmentStatus.PENDING,
                       Appointment.hold_expiry_at.isnot(None),
                       Appointment.hold_expiry_at < now).all())
    for a in expired:
        a.status = AppointmentStatus.CANCELLED
    if expired:
        db.commit()
    return len(expired)


def start_reminder_scheduler(get_db_factory):
    """Launch the reminder scheduler as a background asyncio task."""
    global _scheduler_task
    _scheduler_task = asyncio.create_task(_run_scheduler(get_db_factory))
    logger.info("Reminder scheduler started")
    return _scheduler_task


def stop_reminder_scheduler():
    """Cancel the scheduler task on shutdown."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Reminder scheduler stopped")
