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


# ---------------------------------------------------------------------------
# Webhook signature verification (Ed25519)
# ---------------------------------------------------------------------------

import base64
import time
import nacl.signing


def _make_signed_payload(signing_key, body: bytes, timestamp: str):
    """Build the (raw, signature_b64, timestamp) tuple Telnyx would send."""
    signed_message = timestamp.encode() + b"|" + body
    signature = signing_key.sign(signed_message).signature
    return body, base64.b64encode(signature).decode(), timestamp


def test_verify_webhook_signature_accepts_valid_signature(monkeypatch):
    """Correctly signed payload + fresh timestamp → True."""
    signing_key = nacl.signing.SigningKey.generate()
    public_key_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", public_key_b64)

    from clients import telnyx_messaging
    ts = str(int(time.time()))
    body, sig, ts = _make_signed_payload(signing_key, b'{"event":"x"}', ts)
    assert telnyx_messaging.verify_webhook_signature(body, sig, ts) is True


def test_verify_webhook_signature_rejects_tampered_body(monkeypatch):
    """Signature for original body must not validate against a tampered body."""
    signing_key = nacl.signing.SigningKey.generate()
    public_key_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", public_key_b64)

    from clients import telnyx_messaging
    ts = str(int(time.time()))
    _, sig, ts = _make_signed_payload(signing_key, b'{"event":"x"}', ts)
    assert telnyx_messaging.verify_webhook_signature(b'{"event":"TAMPERED"}', sig, ts) is False


def test_verify_webhook_signature_rejects_stale_timestamp(monkeypatch):
    """Timestamp drift > 5 minutes → False (replay protection)."""
    signing_key = nacl.signing.SigningKey.generate()
    public_key_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", public_key_b64)

    from clients import telnyx_messaging
    stale_ts = str(int(time.time()) - 600)  # 10 min old
    body, sig, ts = _make_signed_payload(signing_key, b'{"event":"x"}', stale_ts)
    assert telnyx_messaging.verify_webhook_signature(body, sig, ts) is False


def test_verify_webhook_signature_returns_false_when_public_key_missing(monkeypatch):
    """Missing TELNYX_PUBLIC_KEY → False; do not crash."""
    monkeypatch.delenv("TELNYX_PUBLIC_KEY", raising=False)
    from clients import telnyx_messaging
    assert telnyx_messaging.verify_webhook_signature(b"x", "sig", "1") is False
