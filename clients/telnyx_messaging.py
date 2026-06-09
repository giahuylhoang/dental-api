"""Telnyx Messaging v2 HTTP transport.

Pure transport — no body construction. Body templating happens in
services/sms_templates.py; send dispatching happens in services/sms.py.
"""
from __future__ import annotations

import base64
import logging
import os
import time

import httpx
import nacl.exceptions
import nacl.signing

logger = logging.getLogger(__name__)

TELNYX_API_BASE = "https://api.telnyx.com/v2"
MAX_SIGNATURE_AGE_SECONDS = 300


def _http_client() -> httpx.Client:
    """httpx.Client per call. Tests monkeypatch this function."""
    return httpx.Client(timeout=10.0)


def send_message(*, to: str, body: str, from_: str | None = None) -> str | None:
    """Send one SMS via Telnyx. Returns message ID on success, None on failure.

    Caller is responsible for body construction. We do not chunk long bodies —
    Telnyx auto-segments at the protocol layer.

    ``from_`` is the sender number to use. When None, falls back to the
    ``TELNYX_SMS_FROM_NUMBER`` env var (legacy single-number behavior).
    Per-clinic threading passes ``clinic.sms_from_number`` so each clinic
    sends from its own DID.
    """
    api_key = os.getenv("TELNYX_API_KEY")
    profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
    from_number = from_ or os.getenv("TELNYX_SMS_FROM_NUMBER")

    if not (api_key and profile_id and from_number):
        logger.warning("Telnyx send skipped: missing TELNYX_* env vars")
        return None

    payload = {
        "from": from_number,
        "to": to,
        "text": body,
        "messaging_profile_id": profile_id,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        client = _http_client()
        resp = client.post(
            f"{TELNYX_API_BASE}/messages",
            json=payload,
            headers=headers,
        )
        if resp.status_code >= 300:
            logger.warning("Telnyx send failed: %s %s", resp.status_code, resp.text)
            return None
        data = resp.json()
        return data["data"]["id"]
    except Exception as exc:
        logger.exception("Telnyx send raised: %s", exc)
        return None


def verify_webhook_signature(payload: bytes, signature_b64: str, timestamp: str) -> bool:
    """Verify Telnyx-Signature-ED25519 + Telnyx-Timestamp headers.

    Telnyx signs the bytes ``f"{timestamp}|".encode() + payload`` with the
    profile's Ed25519 private key. The public key is published once per
    Messaging Profile and stored in TELNYX_PUBLIC_KEY (base64).

    Returns False on:
    - missing TELNYX_PUBLIC_KEY env var
    - non-numeric timestamp
    - timestamp drift > MAX_SIGNATURE_AGE_SECONDS (replay protection)
    - signature mismatch / decode error
    """
    public_key_b64 = os.getenv("TELNYX_PUBLIC_KEY")
    if not public_key_b64:
        return False

    try:
        ts_int = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts_int) > MAX_SIGNATURE_AGE_SECONDS:
        return False

    try:
        verify_key = nacl.signing.VerifyKey(base64.b64decode(public_key_b64))
        sig_bytes = base64.b64decode(signature_b64)
        signed_message = timestamp.encode() + b"|" + payload
        verify_key.verify(signed_message, sig_bytes)
        return True
    except (nacl.exceptions.BadSignatureError, ValueError, TypeError):
        return False
