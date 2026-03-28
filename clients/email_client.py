"""
SMTP email to clinic when a new appointment is booked.

Env: SEND_CLINIC_BOOKING_EMAIL (default true), SMTP_HOST, SMTP_PORT (default 587),
SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS (default true for port 587), EMAIL_FROM,
EMAIL_FROM_NAME (optional), SMTP_LOCAL_HOSTNAME (default rockyridgeai.com for EHLO/STARTTLS).

SMTP_DEPLOY_VERIFY_TO (optional): if set in production, run_api sends one test message at startup;
process exits with code 1 if sending fails (fail closed on deploy).

BOOKING_NOTIFICATION_TO (optional): if set, new-booking emails are sent to this address
instead of the clinic's booking_notification_email. Use for local/testing; leave unset in
production so each clinic's DB field controls the recipient.

Uses the same SMS_DELAY_SECONDS as sms_client so booking SMS and clinic email align
when a delay is configured.
"""

from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from clients.sms_client import SMS_DELAY_SECONDS

logger = logging.getLogger("dental-receptionist")

SEND_CLINIC_BOOKING_EMAIL = os.getenv("SEND_CLINIC_BOOKING_EMAIL", "true").lower() in ("true", "1", "yes")


def resolve_booking_notification_recipient(clinic_booking_notification_email: str | None) -> str:
    """
    Return the To: address for clinic new-booking emails.
    BOOKING_NOTIFICATION_TO overrides the clinic row when non-empty.
    """
    env_to = os.getenv("BOOKING_NOTIFICATION_TO", "").strip()
    if env_to:
        return env_to
    return (clinic_booking_notification_email or "").strip()


NEW_BOOKING_EMAIL_SUBJECT = "New booking: {clinic_name} — {patient_name} — {when_local}"

def _smtp_local_hostname() -> str:
    return os.getenv("SMTP_LOCAL_HOSTNAME", "rockyridgeai.com").strip() or "rockyridgeai.com"


def _deliver_smtp(to_email: str, subject: str, body: str) -> bool:
    """
    Send one plain-text message using current SMTP_* / EMAIL_* env. Returns False if
    SMTP_HOST or EMAIL_FROM is missing or send raises.
    """
    host = os.getenv("SMTP_HOST", "").strip()
    from_addr = os.getenv("EMAIL_FROM", "").strip()
    if not host or not from_addr:
        return False

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
    from_name = os.getenv("EMAIL_FROM_NAME", "").strip()
    local_hostname = _smtp_local_hostname()

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_addr)) if from_name else from_addr
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, port, timeout=30, local_hostname=local_hostname) as server:
            if use_tls:
                server.starttls()
            if user:
                server.login(user, password)
            server.sendmail(from_addr, [to_email], msg.as_string())
        return True
    except Exception as e:
        logger.error("SMTP send failed: %s", e, exc_info=True)
        return False


NEW_BOOKING_EMAIL_BODY = """New appointment booked

Clinic: {clinic_name}
Appointment ID: {appointment_id}

Patient: {patient_name}
Phone: {patient_phone}
Email: {patient_email}

When: {when_local}
Provider: {provider_name}
Service: {service_name}
"""


def _send_email_sync(to_email: str, subject: str, body: str) -> bool:
    """Send plain-text email via SMTP. Blocking. Returns True on success. Never raises."""
    if not SEND_CLINIC_BOOKING_EMAIL:
        logger.info(
            "Clinic booking email disabled (SEND_CLINIC_BOOKING_EMAIL=false). Would send to %s: %s",
            to_email,
            subject,
        )
        return True

    host = os.getenv("SMTP_HOST", "").strip()
    from_addr = os.getenv("EMAIL_FROM", "").strip()
    if not host or not from_addr:
        logger.warning(
            "SMTP not configured (need SMTP_HOST and EMAIL_FROM) — skipping clinic booking email to %s",
            to_email,
        )
        return False

    return _deliver_smtp(to_email, subject, body)


def verify_smtp_deploy() -> bool:
    """
    If SMTP_DEPLOY_VERIFY_TO is set, send a single test message; return False on failure.
    If unset, return True (no check).
    """
    to = os.getenv("SMTP_DEPLOY_VERIFY_TO", "").strip()
    if not to:
        return True
    host = os.getenv("SMTP_HOST", "").strip()
    from_addr = os.getenv("EMAIL_FROM", "").strip()
    if not host or not from_addr:
        logger.error(
            "SMTP_DEPLOY_VERIFY_TO is set but SMTP_HOST or EMAIL_FROM is missing — deploy check failed",
        )
        return False
    subject = "Dental API deploy SMTP check"
    body = "This message confirms outbound SMTP from a new deployment."
    ok = _deliver_smtp(to, subject, body)
    if ok:
        logger.info("SMTP deploy verification sent successfully to %s", to)
    else:
        logger.error("SMTP deploy verification failed (could not send to %s)", to)
    return ok


async def send_clinic_new_booking_email(
    to_email: str,
    clinic_name: str,
    appointment_id: str,
    patient_name: str,
    patient_phone: str,
    patient_email: str,
    when_local: str,
    provider_name: str,
    service_name: str,
) -> bool:
    """Notify clinic inbox of a new booking. Never raises."""
    to_email = (to_email or "").strip()
    if not to_email:
        return True

    patient_phone = (patient_phone or "").strip() or "—"
    patient_email = (patient_email or "").strip() or "—"
    subject = NEW_BOOKING_EMAIL_SUBJECT.format(
        clinic_name=clinic_name,
        patient_name=patient_name,
        when_local=when_local,
    )
    body = NEW_BOOKING_EMAIL_BODY.format(
        clinic_name=clinic_name,
        appointment_id=appointment_id,
        patient_name=patient_name,
        patient_phone=patient_phone,
        patient_email=patient_email,
        when_local=when_local,
        provider_name=provider_name,
        service_name=service_name,
    )
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_send_email_sync, to_email, subject, body),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        logger.error("Clinic booking email timed out after 30s")
        return False
    except Exception as e:
        logger.error("Clinic booking email error: %s", e, exc_info=True)
        return False


async def send_clinic_booking_email_delayed(
    to_email: str,
    clinic_name: str,
    appointment_id: str,
    patient_name: str,
    patient_phone: str,
    patient_email: str,
    when_local: str,
    provider_name: str,
    service_name: str,
) -> None:
    """Sleep SMS_DELAY_SECONDS then send clinic booking email. For BackgroundTasks."""
    if SMS_DELAY_SECONDS > 0:
        await asyncio.sleep(SMS_DELAY_SECONDS)
    await send_clinic_new_booking_email(
        to_email,
        clinic_name,
        appointment_id,
        patient_name,
        patient_phone,
        patient_email,
        when_local,
        provider_name,
        service_name,
    )
