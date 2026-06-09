"""Tests for the provider dispatch in services/sms.py."""

from unittest.mock import patch


def test_send_sms_raw_routes_to_telnyx_when_provider_is_telnyx(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")

    with patch("clients.telnyx_messaging.send_message", return_value="msg_xyz") as tx, \
         patch("clients.sms_client._send_via_twilio", return_value=None) as tw:
        from services import sms
        result = sms.send_sms_raw(to="+1", body="hi")

    assert result == "msg_xyz"
    tx.assert_called_once_with(to="+1", body="hi", from_=None)
    tw.assert_not_called()


def test_send_sms_raw_routes_to_twilio_when_provider_is_twilio(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "twilio")

    with patch("clients.telnyx_messaging.send_message", return_value=None) as tx, \
         patch("clients.sms_client._send_via_twilio", return_value="SM123") as tw:
        from services import sms
        result = sms.send_sms_raw(to="+1", body="hi")

    assert result == "SM123"
    tw.assert_called_once_with(to="+1", body="hi", from_=None)
    tx.assert_not_called()


def test_send_sms_raw_defaults_to_twilio_for_back_compat(monkeypatch):
    """When SMS_PROVIDER is unset, default to Twilio (current production)."""
    monkeypatch.delenv("SMS_PROVIDER", raising=False)

    with patch("clients.sms_client._send_via_twilio", return_value="SM_default") as tw:
        from services import sms
        result = sms.send_sms_raw(to="+1", body="hi")

    assert result == "SM_default"
    tw.assert_called_once()


def test_send_sms_raw_returns_none_when_unknown_provider(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "carrier_pigeon")
    from services import sms
    assert sms.send_sms_raw(to="+1", body="hi") is None


# ---------------------------------------------------------------------------
# Per-clinic FROM number threading
# ---------------------------------------------------------------------------


def test_send_sms_raw_forwards_from_to_telnyx(monkeypatch):
    """When the caller passes from_, services.sms forwards it to the Telnyx client."""
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")

    with patch("clients.telnyx_messaging.send_message", return_value="msg") as tx:
        from services import sms
        sms.send_sms_raw(to="+1", body="hi", from_="+14035550000")

    tx.assert_called_once_with(to="+1", body="hi", from_="+14035550000")


def test_send_sms_raw_forwards_from_to_twilio(monkeypatch):
    """When the caller passes from_, services.sms forwards it to the Twilio client."""
    monkeypatch.setenv("SMS_PROVIDER", "twilio")

    with patch("clients.sms_client._send_via_twilio", return_value="SM") as tw:
        from services import sms
        sms.send_sms_raw(to="+1", body="hi", from_="+14035550000")

    tw.assert_called_once_with(to="+1", body="hi", from_="+14035550000")


def test_send_sms_raw_defaults_from_to_none_when_omitted(monkeypatch):
    """Without from_, services.sms passes from_=None so client falls back to env."""
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")

    with patch("clients.telnyx_messaging.send_message", return_value="msg") as tx:
        from services import sms
        sms.send_sms_raw(to="+1", body="hi")

    tx.assert_called_once_with(to="+1", body="hi", from_=None)
