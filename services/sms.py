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
import re

logger = logging.getLogger(__name__)


def normalize_e164(raw: str | None) -> str | None:
    """Best-effort E.164 for North American (NANP, +1) numbers.

    Accepts common human formats — '(403) 247-6222', '403-247-6222',
    '4032476222', '+14032476222', '1-403-247-6222' — and returns
    '+14032476222'. Returns None when no plausible number can be derived,
    so the caller can skip the send instead of handing the provider garbage.
    """
    if not raw:
        return None
    s = str(raw).strip()
    had_plus = s.startswith("+")
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    if had_plus:
        # Already international — trust the supplied country code.
        return "+" + digits
    if len(digits) == 10:                       # NANP, no country code
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    if 11 <= len(digits) <= 15:                 # already carries a country code
        return "+" + digits
    return None                                 # too short to be a real number


def _provider() -> str:
    return os.getenv("SMS_PROVIDER", "twilio").lower()


def send_sms_raw(*, to: str, body: str, from_: str | None = None) -> str | None:
    """Send one SMS. Returns provider message ID on success, None on failure.

    ``from_`` is the sender number to use. When None, the underlying client
    falls back to its provider-specific env var (``TELNYX_SMS_FROM_NUMBER``
    or ``TWILIO_PHONE_NUMBER``) for back-compat. Per-clinic threading passes
    ``clinic.sms_from_number`` so each clinic sends from its own DID.
    """
    to_e164 = normalize_e164(to)
    if not to_e164:
        logger.warning("SMS not sent: could not normalize 'to' number %r to E.164", to)
        return None
    provider = _provider()
    if provider == "telnyx":
        from clients import telnyx_messaging
        return telnyx_messaging.send_message(to=to_e164, body=body, from_=from_)
    if provider == "twilio":
        from clients import sms_client
        return sms_client._send_via_twilio(to=to_e164, body=body, from_=from_)
    logger.warning("Unknown SMS_PROVIDER=%r; SMS not sent", provider)
    return None
