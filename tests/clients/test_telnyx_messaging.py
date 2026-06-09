"""Tests for the Telnyx Messaging v2 HTTP client transport.

Pure transport — no body construction. Body templating happens in
services/sms_templates.py; send dispatching happens in services/sms.py.
"""

from unittest.mock import MagicMock


def test_send_message_posts_to_telnyx_with_required_fields(monkeypatch):
    """send_message should POST to /v2/messages with from/to/text/messaging_profile_id."""
    monkeypatch.setenv("TELNYX_API_KEY", "KEY_xxx")
    monkeypatch.setenv("TELNYX_MESSAGING_PROFILE_ID", "MP_yyy")
    monkeypatch.setenv("TELNYX_SMS_FROM_NUMBER", "+14035550000")

    from clients import telnyx_messaging

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"id": "msg_abc123"}}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    monkeypatch.setattr(telnyx_messaging, "_http_client", lambda: mock_client)

    msg_id = telnyx_messaging.send_message(to="+14035551234", body="Hello")

    assert msg_id == "msg_abc123"
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://api.telnyx.com/v2/messages"
    sent_body = call_args[1]["json"]
    assert sent_body["from"] == "+14035550000"
    assert sent_body["to"] == "+14035551234"
    assert sent_body["text"] == "Hello"
    assert sent_body["messaging_profile_id"] == "MP_yyy"
    sent_headers = call_args[1]["headers"]
    assert sent_headers["Authorization"] == "Bearer KEY_xxx"


def test_send_message_returns_none_on_http_error(monkeypatch):
    """Non-2xx response → return None (caller handles failure)."""
    monkeypatch.setenv("TELNYX_API_KEY", "KEY")
    monkeypatch.setenv("TELNYX_MESSAGING_PROFILE_ID", "MP")
    monkeypatch.setenv("TELNYX_SMS_FROM_NUMBER", "+1")

    from clients import telnyx_messaging

    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "invalid number"
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    monkeypatch.setattr(telnyx_messaging, "_http_client", lambda: mock_client)

    assert telnyx_messaging.send_message(to="+1", body="x") is None


def test_send_message_returns_none_when_api_key_missing(monkeypatch):
    """Missing TELNYX_API_KEY → no-op, return None, log warning."""
    monkeypatch.delenv("TELNYX_API_KEY", raising=False)
    monkeypatch.setenv("TELNYX_MESSAGING_PROFILE_ID", "MP")
    monkeypatch.setenv("TELNYX_SMS_FROM_NUMBER", "+1")

    from clients import telnyx_messaging
    assert telnyx_messaging.send_message(to="+1", body="x") is None
