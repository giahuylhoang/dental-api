"""Background reminder scheduler: wakes every 60s, dispatches due reminders."""

import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("dental-receptionist")

_scheduler_task = None


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
    from database.ops.models import AppointmentReminder
    from database.models import Appointment, Patient
    from clients.sms_client import _send_sms_sync

    now = datetime.utcnow()
    window_end = now + timedelta(seconds=60)

    db = next(get_db_factory())
    try:
        reminders = db.query(AppointmentReminder).filter(
            AppointmentReminder.status == "pending",
            AppointmentReminder.scheduled_at <= window_end,
            AppointmentReminder.scheduled_at >= now - timedelta(minutes=5),
        ).all()

        for reminder in reminders:
            # Idempotent: skip already sent
            if reminder.status == "sent":
                continue

            apt = db.query(Appointment).filter(Appointment.id == reminder.appointment_id).first()
            if not apt:
                reminder.status = "failed"
                reminder.failure_reason = "Appointment not found"
                db.commit()
                continue

            patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()

            try:
                if reminder.channel == "sms" and patient and patient.phone:
                    body = f"Reminder: appointment on {apt.start_time.strftime('%Y-%m-%d %H:%M')}"
                    ok = _send_sms_sync(patient.phone, body)
                    if ok:
                        reminder.status = "sent"
                        reminder.sent_at = datetime.utcnow()
                    else:
                        reminder.status = "failed"
                        reminder.failure_reason = "SMS send failed"
                elif reminder.channel == "email" and patient and patient.email:
                    logger.info("Email reminder stub: to=%s", patient.email)
                    reminder.status = "sent"
                    reminder.sent_at = datetime.utcnow()
                else:
                    reminder.status = "failed"
                    reminder.failure_reason = "No contact info"
            except Exception as e:
                reminder.status = "failed"
                reminder.failure_reason = str(e)

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
