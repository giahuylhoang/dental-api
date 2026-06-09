"""
Twilio-based SMS client for appointment confirmations.

Env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER.
SEND_BOOKING_SMS (default true) toggles sending on/off.
SMS_DELAY_SECONDS (default 0) delays sending; use with background tasks.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger("dental-receptionist")

SEND_BOOKING_SMS = os.getenv("SEND_BOOKING_SMS", "true").lower() in ("true", "1", "yes")
SMS_DELAY_SECONDS = int(os.getenv("SMS_DELAY_SECONDS", "0"))


def _append_clinic_contact_suffix(
    base: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
) -> str:
    extras: list[str] = []
    addr = (clinic_address or "").strip()
    phone = (contact_phone or "").strip()
    if addr:
        extras.append(f"Address: {addr}")
    if phone:
        extras.append(f"Feel free to call us at {phone}.")
    if not extras:
        return base
    return f"{base} {' '.join(extras)}"


def _send_via_twilio(*, to: str, body: str) -> str | None:
    """Pure Twilio transport. No body construction, no SEND_BOOKING_SMS toggle.

    Called by services.sms.send_sms_raw when SMS_PROVIDER=twilio. Returns
    the Twilio message SID on success, None on failure or when creds are
    not configured.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_phone]):
        logger.warning("Twilio not configured (missing TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_PHONE_NUMBER)")
        return None

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=body, from_=from_phone, to=to)
        return msg.sid
    except Exception as e:
        logger.error("Twilio SMS failed: %s", e, exc_info=True)
        return None


def _send_sms_sync(to_phone: str, body: str) -> bool:
    """Send SMS via the active provider. Blocking. Returns True on success/skip.

    Dispatches through services.sms.send_sms_raw, which routes to Telnyx
    or Twilio based on SMS_PROVIDER env. SEND_BOOKING_SMS=false short-
    circuits before any send.
    """
    if not SEND_BOOKING_SMS:
        logger.info("SMS sending disabled (SEND_BOOKING_SMS=false). Would send: %s", body[:80])
        return True

    from services.sms import send_sms_raw

    msg_id = send_sms_raw(to=to_phone, body=body)
    return msg_id is not None


async def send_booking_confirmation_sms(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    doctor_name: str,
    service_name: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
) -> bool:
    """
    Send booking confirmation SMS via Twilio.
    Returns True on success or when skipped; False on failure.
    Never raises; logs errors. Uses asyncio.to_thread with 10s timeout.
    """
    if not phone or not str(phone).strip():
        return True
    core = (
        f"Hi {patient_name}, your appointment at {clinic_name} with {doctor_name} "
        f"for {service_name} on {date_str} at {time_str} is confirmed."
    )
    body = _append_clinic_contact_suffix(core, clinic_address, contact_phone)
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_send_sms_sync, str(phone).strip(), body),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        logger.error("Twilio SMS timed out after 10s")
        return False
    except Exception as e:
        logger.error("SMS send error: %s", e, exc_info=True)
        return False


async def send_cancellation_sms(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    doctor_name: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
) -> bool:
    """Send cancellation confirmation SMS. Same semantics as send_booking_confirmation_sms."""
    if not phone or not str(phone).strip():
        return True
    reschedule_hint = (
        f"Call us at {contact_phone.strip()} to reschedule."
        if (contact_phone or "").strip()
        else "Call us to reschedule."
    )
    core = (
        f"{clinic_name}: Your appointment with {doctor_name} on {date_str} at {time_str} "
        f"has been cancelled. {reschedule_hint}"
    )
    body = _append_clinic_contact_suffix(core, clinic_address, None)
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_send_sms_sync, str(phone).strip(), body),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        logger.error("Twilio SMS (cancellation) timed out after 10s")
        return False
    except Exception as e:
        logger.error("SMS cancellation send error: %s", e, exc_info=True)
        return False


async def send_reschedule_confirmation_sms(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    doctor_name: str,
    service_name: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
) -> bool:
    """Send reschedule confirmation SMS. Same semantics as send_booking_confirmation_sms."""
    if not phone or not str(phone).strip():
        return True
    core = (
        f"Hi {patient_name}, your appointment at {clinic_name} has been rescheduled to "
        f"{date_str} at {time_str} with {doctor_name} ({service_name})."
    )
    body = _append_clinic_contact_suffix(core, clinic_address, contact_phone)
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_send_sms_sync, str(phone).strip(), body),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        logger.error("Twilio SMS (reschedule) timed out after 10s")
        return False
    except Exception as e:
        logger.error("SMS reschedule send error: %s", e, exc_info=True)
        return False


def send_whatsapp(to: str, body: str) -> dict:
    """Send a WhatsApp message via Twilio using the whatsapp: prefix.

    Uses TWILIO_WHATSAPP_FROM env var; falls back to TWILIO_PHONE_NUMBER.
    Returns a dict with 'sid' on success. Never raises.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM") or os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        logger.warning("Twilio not configured for WhatsApp")
        return {"sid": None}

    from_wa = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
    to_wa = to if to.startswith("whatsapp:") else f"whatsapp:{to}"

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=body, from_=from_wa, to=to_wa)
        return {"sid": msg.sid}
    except Exception as e:
        logger.error("Twilio WhatsApp failed: %s", e, exc_info=True)
        return {"sid": None}


def _patient_opts_in(channel: str, clinic_id: Optional[str], patient_id: Optional[str]) -> bool:
    """Honor v1.1 patient_communication_preferences. Defaults to True for
    legacy callers that don't pass clinic_id+patient_id (preserves v1 behavior)."""
    if not clinic_id or not patient_id:
        return True
    try:
        from database.connection import SessionLocal
        from database.clinical.communication_prefs import is_opted_in

        db = SessionLocal()
        try:
            return is_opted_in(db, clinic_id, patient_id, channel)
        finally:
            db.close()
    except Exception as e:  # never block dispatch on a lookup failure
        logger.warning("Comm prefs lookup failed: %s", e)
        return True


async def send_booking_sms_delayed(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    doctor_name: str,
    service_name: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
    *,
    clinic_id: Optional[str] = None,
    patient_id: Optional[str] = None,
) -> None:
    """Sleep SMS_DELAY_SECONDS, then send booking confirmation. For BackgroundTasks.

    v1.1 — when clinic_id and patient_id are provided, honor the patient's
    SMS opt-in preference. Without those kwargs (legacy callers), defaults
    to opted-in.
    """
    if not _patient_opts_in("sms", clinic_id, patient_id):
        logger.info("SMS booking skipped: patient opted out")
        return
    if SMS_DELAY_SECONDS > 0:
        await asyncio.sleep(SMS_DELAY_SECONDS)
    await send_booking_confirmation_sms(
        phone,
        patient_name,
        date_str,
        time_str,
        doctor_name,
        service_name,
        clinic_name,
        clinic_address,
        contact_phone,
    )


async def _send_hold_reserved_sms(
    to_phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    provider_name: str,
    clinic_name: str,
    clinic_phone: Optional[str] = None,
) -> bool:
    """Web hold: tell the patient the slot is reserved and staff will call to confirm."""
    body = (
        f"Hi {patient_name}, your appointment with {provider_name} at {clinic_name} "
        f"on {date_str} at {time_str} is reserved. Our front desk will call shortly to confirm. "
        f"Questions? Call {(clinic_phone or '').strip()}."
    )
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_send_sms_sync, str(to_phone).strip(), body),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        logger.error("Twilio SMS (hold reserved) timed out after 10s")
        return False
    except Exception as e:
        logger.error("SMS hold reserved send error: %s", e, exc_info=True)
        return False


async def send_hold_reserved_sms_delayed(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    provider_name: str,
    clinic_name: str,
    clinic_phone: Optional[str] = None,
    *,
    clinic_id: Optional[str] = None,
    patient_id: Optional[str] = None,
) -> None:
    """Sleep SMS_DELAY_SECONDS, then send hold-reserved SMS. For BackgroundTasks.

    Web hold: notifies the patient their slot is reserved and staff will call to confirm.
    Honors patient SMS opt-in preference when clinic_id + patient_id are provided.
    """
    if not _patient_opts_in("sms", clinic_id, patient_id):
        logger.info("SMS hold reserved skipped: patient opted out")
        return
    if SMS_DELAY_SECONDS > 0:
        await asyncio.sleep(SMS_DELAY_SECONDS)
    await _send_hold_reserved_sms(
        phone,
        patient_name,
        date_str,
        time_str,
        provider_name,
        clinic_name,
        clinic_phone,
    )


async def send_cancellation_sms_delayed(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    doctor_name: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
    *,
    clinic_id: Optional[str] = None,
    patient_id: Optional[str] = None,
) -> None:
    """Sleep SMS_DELAY_SECONDS, then send cancellation SMS. For BackgroundTasks."""
    if not _patient_opts_in("sms", clinic_id, patient_id):
        logger.info("SMS cancellation skipped: patient opted out")
        return
    if SMS_DELAY_SECONDS > 0:
        await asyncio.sleep(SMS_DELAY_SECONDS)
    await send_cancellation_sms(
        phone,
        patient_name,
        date_str,
        time_str,
        doctor_name,
        clinic_name,
        clinic_address,
        contact_phone,
    )


async def send_reschedule_sms_delayed(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    doctor_name: str,
    service_name: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
    *,
    clinic_id: Optional[str] = None,
    patient_id: Optional[str] = None,
) -> None:
    """Sleep SMS_DELAY_SECONDS, then send reschedule confirmation. For BackgroundTasks."""
    if not _patient_opts_in("sms", clinic_id, patient_id):
        logger.info("SMS reschedule skipped: patient opted out")
        return
    if SMS_DELAY_SECONDS > 0:
        await asyncio.sleep(SMS_DELAY_SECONDS)
    await send_reschedule_confirmation_sms(
        phone,
        patient_name,
        date_str,
        time_str,
        doctor_name,
        service_name,
        clinic_name,
        clinic_address,
        contact_phone,
    )
