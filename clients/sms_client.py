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


def _send_sms_sync(to_phone: str, body: str) -> bool:
    """Send SMS via Twilio. Blocking. Returns True on success, False on failure. Never raises."""
    if not SEND_BOOKING_SMS:
        logger.info("SMS sending disabled (SEND_BOOKING_SMS=false). Would send: %s", body[:80])
        return True

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_phone]):
        logger.warning("Twilio not configured (missing TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_PHONE_NUMBER)")
        return False

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(body=body, from_=from_phone, to=to_phone)
        return True
    except Exception as e:
        logger.error("Twilio SMS failed: %s", e, exc_info=True)
        return False


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
) -> None:
    """Sleep SMS_DELAY_SECONDS, then send booking confirmation. For BackgroundTasks."""
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


async def send_cancellation_sms_delayed(
    phone: str,
    patient_name: str,
    date_str: str,
    time_str: str,
    doctor_name: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
) -> None:
    """Sleep SMS_DELAY_SECONDS, then send cancellation SMS. For BackgroundTasks."""
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
) -> None:
    """Sleep SMS_DELAY_SECONDS, then send reschedule confirmation. For BackgroundTasks."""
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
