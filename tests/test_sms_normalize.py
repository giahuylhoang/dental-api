"""Tests for E.164 normalization at the SMS dispatcher chokepoint.

Regression coverage for Telnyx error 40310 ("Invalid 'to' address") on
web bookings, where the destination phone arrives in display format
(e.g. '(403) 247-6222') and must be normalized to '+14032476222' before
the provider call.
"""

import pytest

from services import sms
from services.sms import normalize_e164, send_sms_raw


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("(403) 247-6222", "+14032476222"),
        ("403-247-6222", "+14032476222"),
        ("4032476222", "+14032476222"),
        ("+14032476222", "+14032476222"),
        ("1-403-247-6222", "+14032476222"),
        ("", None),
        (None, None),
        ("12345", None),  # too short to be a real number
    ],
)
def test_normalize_e164(raw, expected):
    assert normalize_e164(raw) == expected


def test_send_sms_raw_normalizes_to_before_dispatch(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    captured: dict = {}

    def fake_send_message(*, to, body, from_=None):
        captured["to"] = to
        captured["body"] = body
        captured["from_"] = from_
        return "msg-123"

    from clients import telnyx_messaging

    monkeypatch.setattr(telnyx_messaging, "send_message", fake_send_message)

    result = send_sms_raw(to="(403) 247-6222", body="hi")

    assert result == "msg-123"
    assert captured["to"] == "+14032476222"


def test_send_sms_raw_skips_send_when_not_normalizable(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    called: dict = {"hit": False}

    def fake_send_message(*, to, body, from_=None):
        called["hit"] = True
        return "should-not-happen"

    from clients import telnyx_messaging

    monkeypatch.setattr(telnyx_messaging, "send_message", fake_send_message)

    result = send_sms_raw(to="abc", body="hi")

    assert result is None
    assert called["hit"] is False
