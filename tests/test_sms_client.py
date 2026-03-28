"""Unit tests for SMS body templates (Twilio mocked)."""

import asyncio
from unittest.mock import patch

from clients.sms_client import (
    send_booking_confirmation_sms,
    send_cancellation_sms,
    send_reschedule_confirmation_sms,
)


def test_booking_sms_core_and_optional_clinic_contact():
    captured: dict = {}

    def fake_send(to_phone: str, body: str) -> bool:
        captured["to"] = to_phone
        captured["body"] = body
        return True

    async def run():
        with patch("clients.sms_client._send_sms_sync", fake_send):
            await send_booking_confirmation_sms(
                "5551234567",
                "Sam",
                "2026-03-31",
                "4:00 PM",
                "Denturist Nadeem",
                "General Consultation",
                "Market Mall Denture Clinics",
                clinic_address="3625 Example Trail NW",
                contact_phone="(403) 555-0100",
            )

    asyncio.run(run())

    b = captured["body"]
    assert "Hi Sam" in b
    assert "Market Mall Denture Clinics" in b
    assert "Denturist Nadeem" in b
    assert "General Consultation" in b
    assert "2026-03-31" in b and "4:00 PM" in b
    assert "is confirmed." in b
    assert "Address: 3625 Example Trail NW" in b
    assert "Feel free to call us at (403) 555-0100." in b
    assert captured["to"] == "5551234567"


def test_booking_sms_without_address_or_phone():
    captured: dict = {}

    def fake_send(to_phone: str, body: str) -> bool:
        captured["body"] = body
        return True

    async def run():
        with patch("clients.sms_client._send_sms_sync", fake_send):
            await send_booking_confirmation_sms(
                "5551234567",
                "Sam",
                "2026-03-31",
                "4:00 PM",
                "Dr X",
                "Cleaning",
                "Default Clinic",
            )

    asyncio.run(run())

    b = captured["body"]
    assert "is confirmed." in b
    assert "Address:" not in b
    assert "Feel free to call us" not in b


def test_cancellation_sms_uses_contact_phone_and_address():
    captured: dict = {}

    def fake_send(to_phone: str, body: str) -> bool:
        captured["body"] = body
        return True

    async def run():
        with patch("clients.sms_client._send_sms_sync", fake_send):
            await send_cancellation_sms(
                "5551234567",
                "Sam",
                "2026-03-31",
                "4:00 PM",
                "Dr X",
                "Clinic Name",
                clinic_address="1 Main St",
                contact_phone="999-000-1111",
            )

    asyncio.run(run())

    b = captured["body"]
    assert "has been cancelled." in b
    assert "Call us at 999-000-1111 to reschedule." in b
    assert "Address: 1 Main St" in b


def test_cancellation_sms_generic_reschedule_without_phone():
    captured: dict = {}

    def fake_send(to_phone: str, body: str) -> bool:
        captured["body"] = body
        return True

    async def run():
        with patch("clients.sms_client._send_sms_sync", fake_send):
            await send_cancellation_sms(
                "5551234567",
                "Sam",
                "2026-03-31",
                "4:00 PM",
                "Dr X",
                "Clinic Name",
            )

    asyncio.run(run())

    assert "Call us to reschedule." in captured["body"]


def test_reschedule_sms_appends_contact_like_booking():
    captured: dict = {}

    def fake_send(to_phone: str, body: str) -> bool:
        captured["body"] = body
        return True

    async def run():
        with patch("clients.sms_client._send_sms_sync", fake_send):
            await send_reschedule_confirmation_sms(
                "5551234567",
                "Sam",
                "2026-04-01",
                "2:00 PM",
                "Dr Y",
                "Follow-up",
                "Clinic Z",
                clinic_address="9 Oak Ave",
                contact_phone="111-222-3333",
            )

    asyncio.run(run())

    b = captured["body"]
    assert "rescheduled to" in b
    assert "Address: 9 Oak Ave" in b
    assert "Feel free to call us at 111-222-3333." in b
