"""Provider-agnostic SMS dispatcher.

Reads SMS_PROVIDER env at call time (so tests can monkeypatch) and
routes to clients.telnyx_messaging.send_message (telnyx) or
clients.sms_client._send_via_twilio (twilio). Default = twilio for
back-compat until the prod cutover.

This module is intentionally tiny. Body construction stays inside
clients/sms_client.py (the existing high-level functions). When those
functions need to send, they now call services.sms.send_sms_raw
instead of touching Twilio directly.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _provider() -> str:
    return os.getenv("SMS_PROVIDER", "twilio").lower()


def send_sms_raw(*, to: str, body: str) -> str | None:
    """Send one SMS. Returns provider message ID on success, None on failure."""
    provider = _provider()
    if provider == "telnyx":
        from clients import telnyx_messaging
        return telnyx_messaging.send_message(to=to, body=body)
    if provider == "twilio":
        from clients import sms_client
        return sms_client._send_via_twilio(to=to, body=body)
    logger.warning("Unknown SMS_PROVIDER=%r; SMS not sent", provider)
    return None
