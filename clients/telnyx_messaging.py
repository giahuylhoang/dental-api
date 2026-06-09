"""Telnyx Messaging v2 HTTP transport.

Pure transport — no body construction. Body templating happens in
services/sms_templates.py; send dispatching happens in services/sms.py.
"""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

TELNYX_API_BASE = "https://api.telnyx.com/v2"


def _http_client() -> httpx.Client:
    """httpx.Client per call. Tests monkeypatch this function."""
    return httpx.Client(timeout=10.0)


def send_message(*, to: str, body: str) -> str | None:
    """Send one SMS via Telnyx. Returns message ID on success, None on failure.

    Caller is responsible for body construction. We do not chunk long bodies —
    Telnyx auto-segments at the protocol layer.
    """
    api_key = os.getenv("TELNYX_API_KEY")
    profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
    from_number = os.getenv("TELNYX_SMS_FROM_NUMBER")

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
