"""Unit tests for clinic booking notification email (SMTP mocked)."""

import asyncio
from unittest.mock import patch

from clients import email_client
from clients.email_client import resolve_booking_notification_recipient, send_clinic_new_booking_email


def test_send_clinic_new_booking_email_builds_body_and_calls_smtp():
    sent: dict = {}

    def fake_send(to_email: str, subject: str, body: str) -> bool:
        sent["to"] = to_email
        sent["subject"] = subject
        sent["body"] = body
        return True

    async def run():
        with patch.object(email_client, "_send_email_sync", fake_send):
            return await send_clinic_new_booking_email(
                to_email="frontdesk@clinic.example",
                clinic_name="Test Clinic",
                appointment_id="apt-uuid-1",
                patient_name="Jane Doe",
                patient_phone="4035551212",
                patient_email="jane@example.com",
                when_local="2026-03-31 at 04:00 PM",
                provider_name="Dr Smith",
                service_name="Consultation",
            )

    ok = asyncio.run(run())

    assert ok is True
    assert sent["to"] == "frontdesk@clinic.example"
    assert "Test Clinic" in sent["subject"]
    assert "Jane Doe" in sent["subject"]
    assert "apt-uuid-1" in sent["body"]
    assert "4035551212" in sent["body"]
    assert "jane@example.com" in sent["body"]
    assert "Dr Smith" in sent["body"]
    assert "Consultation" in sent["body"]


def test_send_clinic_new_booking_email_empty_patient_contact_shows_em_dash():
    sent: dict = {}

    def fake_send(to_email: str, subject: str, body: str) -> bool:
        sent["body"] = body
        return True

    async def run():
        with patch.object(email_client, "_send_email_sync", fake_send):
            await send_clinic_new_booking_email(
                to_email="a@b.co",
                clinic_name="C",
                appointment_id="id",
                patient_name="P",
                patient_phone="",
                patient_email="",
                when_local="t",
                provider_name="Pr",
                service_name="Sv",
            )

    asyncio.run(run())

    assert "Phone: —" in sent["body"]
    assert "Email: —" in sent["body"]


def test_resolve_booking_notification_recipient_env_overrides_clinic(monkeypatch):
    monkeypatch.setenv("BOOKING_NOTIFICATION_TO", "override@example.com")
    assert resolve_booking_notification_recipient("clinic@x.com") == "override@example.com"


def test_resolve_booking_notification_recipient_falls_back_to_clinic(monkeypatch):
    monkeypatch.delenv("BOOKING_NOTIFICATION_TO", raising=False)
    assert resolve_booking_notification_recipient("clinic@x.com") == "clinic@x.com"
    assert resolve_booking_notification_recipient(None) == ""
    assert resolve_booking_notification_recipient("  ") == ""
