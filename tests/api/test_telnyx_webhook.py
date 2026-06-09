"""Tests for POST /webhooks/telnyx/sms-inbound."""

import base64
import json
import time

import nacl.signing


def _sign(signing_key, body_bytes, ts):
    msg = ts.encode() + b"|" + body_bytes
    return base64.b64encode(signing_key.sign(msg).signature).decode()


def test_webhook_rejects_invalid_signature(client, monkeypatch):
    """Bad signature -> 401."""
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", base64.b64encode(b"\x00" * 32).decode())
    body = json.dumps({"data": {"event_type": "message.received", "payload": {}}}).encode()
    ts = str(int(time.time()))
    resp = client.post(
        "/webhooks/telnyx/sms-inbound",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": "bogus",
            "Telnyx-Timestamp": ts,
        },
    )
    assert resp.status_code == 401


def test_webhook_returns_200_on_unmatched_phone_falls_through(client, db_session, monkeypatch):
    """Valid signature + no matching reminder -> 200 fallthrough."""
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY",
        base64.b64encode(bytes(signing_key.verify_key)).decode(),
    )
    body_dict = {
        "data": {
            "event_type": "message.received",
            "payload": {
                "from": {"phone_number": "+19999999999"},  # no reminder for this number
                "to": [{"phone_number": "+14035550000"}],
                "text": "yes",
                "id": "msg_in_1",
            },
        }
    }
    body = json.dumps(body_dict).encode()
    ts = str(int(time.time()))
    sig = _sign(signing_key, body, ts)
    resp = client.post(
        "/webhooks/telnyx/sms-inbound",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["routed_to"] == "fallthrough"


def test_webhook_ignores_non_message_received_events(client, monkeypatch):
    """Telnyx also sends delivery-status events; only 'message.received' is acted on."""
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv(
        "TELNYX_PUBLIC_KEY",
        base64.b64encode(bytes(signing_key.verify_key)).decode(),
    )
    body = json.dumps({"data": {"event_type": "message.sent", "payload": {}}}).encode()
    ts = str(int(time.time()))
    sig = _sign(signing_key, body, ts)
    resp = client.post(
        "/webhooks/telnyx/sms-inbound",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["routed_to"] == "ignored_event"
