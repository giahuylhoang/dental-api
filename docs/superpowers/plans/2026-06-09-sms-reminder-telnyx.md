# SMS Reminder + Telnyx Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to execute Phase B (tasks B1–B13). Phase A (tasks A1–A5) is executed by the MAIN agent because it touches the existing Twilio code path used in production. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate dental-api's outbound SMS from Twilio to Telnyx behind a unified `services/sms.py` interface (no behavior change), then add a one-shot 24h-before SMS appointment reminder with hybrid regex/LLM reply parsing, status writeback, and a token-based reschedule handoff to `market-mall-website`.

**Architecture:** Phase A is a minimal refactor: new Telnyx HTTP transport, new dispatcher `services/sms.send_sms_raw`, internal swap inside the existing `clients/sms_client.py`. No caller signatures change. Phase B adds a Cloud-Scheduler-triggered scan endpoint, a Telnyx inbound webhook, a hybrid reply parser, and `GET/POST /p/reschedule/{token}` handoff endpoints that compose on `feat/holds-foundation`'s public APIs (`/api/public/slots`, `/api/public/holds`, `DENTAL_API_INTERNAL_SECRET`).

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Alembic, pytest, httpx, PyNaCl (Ed25519 for Telnyx signature verify), Google Gen AI SDK (Gemini 3.1 Flash for LLM fallback).

**Spec reference:** `docs/superpowers/specs/2026-06-09-sms-reminder-telnyx-design.md`

**Base branch:** `feat/holds-foundation` (NOT `main`).

---

## File Structure

| File | Action | Phase | Responsibility |
| --- | --- | --- | --- |
| `clients/telnyx_messaging.py` | Create | A | Telnyx Messaging v2 HTTP client: `send_message(to, body) → message_id`; `verify_webhook_signature(payload, signature, timestamp) → bool` |
| `services/sms.py` | Create | A | Provider dispatcher: `send_sms_raw(to, body) → message_id_or_None`. Reads `SMS_PROVIDER` env (`telnyx` \| `twilio`) and routes to the corresponding client. |
| `clients/sms_client.py` | Modify | A | Replace inline `client.messages.create(...)` calls with `services.sms.send_sms_raw(...)`. All high-level functions keep their signatures. |
| `.env.example` | Modify | A | Document `TELNYX_API_KEY`, `TELNYX_MESSAGING_PROFILE_ID`, `TELNYX_SMS_FROM_NUMBER`, `TELNYX_PUBLIC_KEY`, `SMS_PROVIDER`. |
| `alembic/versions/<new>_appointment_reminder_sms_columns.py` | Create | B | Migration adding 8 columns to `appointment_reminders` + 1 index. |
| `database/ops/models.py` | Modify | B | Add the 8 columns to `AppointmentReminder` model (mirror the migration). |
| `api/v1/appointments/schemas.py` | Modify | B | Add `AppointmentMutationSource` Pydantic enum + optional `source` field on status mutation request models. |
| `api/v1/appointments/router.py` | Modify | B | Thread `source` value into the existing `PUT /cancel`, `/status`, `/reschedule` endpoints. Default `inbound_call` for back-compat. |
| `templates/sms/<intent>.<lang>.txt` | Create | B | Template files. MVP populates `en` for 5 intents: `reminder`, `ack_confirmed`, `ack_cancelled`, `ack_reschedule`, `ack_ambiguous`. Empty placeholders for `pa`, `hi`, `ar` (kept on disk for future iteration). |
| `services/sms_templates.py` | Create | B | `render(intent, lang, **vars) → str`. Loads from `templates/sms/` with `en` fallback. |
| `services/reply_parser.py` | Create | B | `parse(text) → ReplyIntent` (regex matrix first, Gemini Flash fallback for `ambiguous`). |
| `api/cron/reminders.py` | Create | B | `POST /cron/reminders/scan`: pick due appointments (offset + quiet-hours + skip-too-late), insert `AppointmentReminder` row, render reminder template, send via `services.sms`. |
| `api/cron/__init__.py` | Create | B | Package init. |
| `api/webhooks/telnyx.py` | Create | B | `POST /webhooks/telnyx/sms-inbound`: verify Ed25519 signature, extract from/to/text, look up matching reminder, dispatch parser, apply action, send ack. Falls through to existing chat_api SMS path when no matching reminder. |
| `api/webhooks/__init__.py` | Create | B | Package init. |
| `api/public/reschedule.py` | Create | B | `GET /p/reschedule/{token}` → 302 to market-mall-website with signed session blob. `POST /p/reschedule/{token}/commit` → atomically marks old appointment `RESCHEDULED`, accepts new appointment from a prior hold (via holds-foundation API). |
| `api/main.py` | Modify | B | `app.include_router(...)` for cron, webhooks/telnyx, public/reschedule. |
| `tests/clients/test_telnyx_messaging.py` | Create | A | Unit tests for HTTP build + signature verify. |
| `tests/services/test_sms_dispatch.py` | Create | A | Unit tests for `send_sms_raw` provider switch. |
| `tests/services/test_reply_parser.py` | Create | B | Regex matrix + LLM-fallback (mocked Gemini). |
| `tests/api/test_cron_reminders.py` | Create | B | Scan endpoint logic + scheduling rules. |
| `tests/api/test_telnyx_webhook.py` | Create | B | Signature verify + intent dispatch end-to-end with mocked Telnyx + mocked Gemini. |
| `tests/api/test_reschedule_link.py` | Create | B | Token GET/POST flow. |
| `tests/integration/test_sms_reminder_e2e.py` | Create | B | YES → CONFIRMED and RESCHEDULE → token + 302 redirect end-to-end. |

---

## Conventions & shared helpers (read these once, then refer back per task)

**Test fixtures available from `tests/conftest.py`:** `db_engine`, `db_session`, `client` (FastAPI TestClient with `get_db` override; seeds a default clinic at `mm_clinic`).

**Env-var pattern:** raw `os.getenv("FOO", "default")` at module load. No Pydantic Settings.

**Router registration:** `APIRouter(prefix="/api/...")` then `app.include_router(...)` in `api/main.py`.

**Provider env switch (used Phase A + B):**
```python
# services/sms.py reads at call time so tests can monkeypatch
def _provider() -> str:
    return os.getenv("SMS_PROVIDER", "twilio").lower()
```

**httpx mocking:** existing tests use `unittest.mock.patch` against the module-level httpx client. Tests should `monkeypatch.setattr("clients.telnyx_messaging._http_client", MockClient())` style.

---

# Phase A — Telnyx Migration (executed by MAIN agent)

Each Phase A task is one focused commit. Run `pytest -x -q` after each commit to keep the existing Twilio path green.

## Task A1: Telnyx HTTP transport — `send_message`

**Files:**
- Create: `clients/telnyx_messaging.py`
- Create: `tests/clients/test_telnyx_messaging.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/clients/test_telnyx_messaging.py
"""Tests for the Telnyx Messaging v2 HTTP client transport."""

import os
from unittest.mock import MagicMock, patch
import pytest


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/giahuyhoangle/Projects/dental-system/dental-api/.claude/worktrees/sms-reminder-telnyx && pytest tests/clients/test_telnyx_messaging.py -v`
Expected: ImportError (module doesn't exist yet).

- [ ] **Step 3: Implement minimal `clients/telnyx_messaging.py`**

```python
# clients/telnyx_messaging.py
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
    """Single httpx.Client instance per process. Tests monkeypatch this."""
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/clients/test_telnyx_messaging.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add clients/telnyx_messaging.py tests/clients/test_telnyx_messaging.py
git commit -m "feat(telnyx): send_message HTTP transport with TDD coverage

Pure transport client — no body construction. Reads TELNYX_API_KEY,
TELNYX_MESSAGING_PROFILE_ID, TELNYX_SMS_FROM_NUMBER. Returns message
ID on 2xx, None on error or missing env.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task A2: Telnyx Ed25519 webhook signature verification

**Files:**
- Modify: `clients/telnyx_messaging.py`
- Modify: `tests/clients/test_telnyx_messaging.py`

- [ ] **Step 1: Add failing tests for `verify_webhook_signature`**

Append to `tests/clients/test_telnyx_messaging.py`:

```python
import base64
import nacl.signing


def _make_signed_payload(signing_key, body: bytes, timestamp: str):
    """Build the (raw, signature, timestamp) tuple Telnyx would send."""
    signed_message = timestamp.encode() + b"|" + body
    signature = signing_key.sign(signed_message).signature
    return body, base64.b64encode(signature).decode(), timestamp


def test_verify_webhook_signature_accepts_valid_signature(monkeypatch):
    """Correctly signed payload + fresh timestamp → True."""
    signing_key = nacl.signing.SigningKey.generate()
    public_key_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", public_key_b64)

    from clients import telnyx_messaging
    import time
    ts = str(int(time.time()))
    body, sig, ts = _make_signed_payload(signing_key, b'{"event":"x"}', ts)
    assert telnyx_messaging.verify_webhook_signature(body, sig, ts) is True


def test_verify_webhook_signature_rejects_tampered_body(monkeypatch):
    """Signature for original body must not validate against a tampered body."""
    signing_key = nacl.signing.SigningKey.generate()
    public_key_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", public_key_b64)

    from clients import telnyx_messaging
    import time
    ts = str(int(time.time()))
    body, sig, ts = _make_signed_payload(signing_key, b'{"event":"x"}', ts)
    assert telnyx_messaging.verify_webhook_signature(b'{"event":"TAMPERED"}', sig, ts) is False


def test_verify_webhook_signature_rejects_stale_timestamp(monkeypatch):
    """Timestamp drift > 5 minutes → False (replay protection)."""
    signing_key = nacl.signing.SigningKey.generate()
    public_key_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", public_key_b64)

    from clients import telnyx_messaging
    import time
    stale_ts = str(int(time.time()) - 600)  # 10 min old
    body, sig, ts = _make_signed_payload(signing_key, b'{"event":"x"}', stale_ts)
    assert telnyx_messaging.verify_webhook_signature(body, sig, ts) is False


def test_verify_webhook_signature_returns_false_when_public_key_missing(monkeypatch):
    """Missing TELNYX_PUBLIC_KEY → False; do not crash."""
    monkeypatch.delenv("TELNYX_PUBLIC_KEY", raising=False)
    from clients import telnyx_messaging
    assert telnyx_messaging.verify_webhook_signature(b"x", "sig", "1") is False
```

- [ ] **Step 2: Run, expect 4 failures**

Run: `pytest tests/clients/test_telnyx_messaging.py -v -k verify_webhook`
Expected: 4 FAIL (function doesn't exist).

- [ ] **Step 3: Append `verify_webhook_signature` to `clients/telnyx_messaging.py`**

```python
# Append at bottom of clients/telnyx_messaging.py
import base64
import time as _time
import nacl.signing
import nacl.exceptions

MAX_SIGNATURE_AGE_SECONDS = 300  # 5 minutes


def verify_webhook_signature(payload: bytes, signature_b64: str, timestamp: str) -> bool:
    """Verify Telnyx-Signature-ED25519 + Telnyx-Timestamp headers.

    Telnyx signs the bytes `f"{timestamp}|".encode() + payload` with the
    profile's Ed25519 private key. The public key is published once per
    Messaging Profile and stored in TELNYX_PUBLIC_KEY (base64).
    """
    public_key_b64 = os.getenv("TELNYX_PUBLIC_KEY")
    if not public_key_b64:
        return False

    try:
        ts_int = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(_time.time() - ts_int) > MAX_SIGNATURE_AGE_SECONDS:
        return False

    try:
        verify_key = nacl.signing.VerifyKey(base64.b64decode(public_key_b64))
        sig_bytes = base64.b64decode(signature_b64)
        signed_message = timestamp.encode() + b"|" + payload
        verify_key.verify(signed_message, sig_bytes)
        return True
    except (nacl.exceptions.BadSignatureError, ValueError, TypeError):
        return False
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/clients/test_telnyx_messaging.py -v`
Expected: 7 PASS.

- [ ] **Step 5: Add `PyNaCl` to `requirements.txt`/`pyproject.toml`**

Check which manifest the project uses:
```bash
ls pyproject.toml requirements.txt requirements-dev.txt 2>/dev/null
```
Add `pynacl>=1.5.0` to the dependency list (production deps).

- [ ] **Step 6: Commit**

```bash
git add clients/telnyx_messaging.py tests/clients/test_telnyx_messaging.py pyproject.toml requirements.txt
git commit -m "feat(telnyx): Ed25519 webhook signature verification

Adds verify_webhook_signature(payload, signature_b64, timestamp).
Rejects tampered bodies, stale timestamps (>5min drift), and calls
with missing TELNYX_PUBLIC_KEY. PyNaCl added as a dependency.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task A3: `services/sms.py` provider dispatcher

**Files:**
- Create: `services/sms.py`
- Create: `tests/services/test_sms_dispatch.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/services/test_sms_dispatch.py
"""Tests for the provider dispatch in services/sms.py."""

from unittest.mock import patch
import pytest


def test_send_sms_raw_routes_to_telnyx_when_provider_is_telnyx(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")

    with patch("clients.telnyx_messaging.send_message", return_value="msg_xyz") as tx, \
         patch("clients.sms_client._send_via_twilio", return_value=None) as tw:
        from services import sms
        result = sms.send_sms_raw(to="+1", body="hi")

    assert result == "msg_xyz"
    tx.assert_called_once_with(to="+1", body="hi")
    tw.assert_not_called()


def test_send_sms_raw_routes_to_twilio_when_provider_is_twilio(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "twilio")

    with patch("clients.telnyx_messaging.send_message", return_value=None) as tx, \
         patch("clients.sms_client._send_via_twilio", return_value="SM123") as tw:
        from services import sms
        result = sms.send_sms_raw(to="+1", body="hi")

    assert result == "SM123"
    tw.assert_called_once_with(to="+1", body="hi")
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
```

- [ ] **Step 2: Run, expect failures**

Run: `pytest tests/services/test_sms_dispatch.py -v`
Expected: 4 FAIL — `services.sms` and/or `clients.sms_client._send_via_twilio` don't exist.

- [ ] **Step 3: Implement `services/sms.py`**

```python
# services/sms.py
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
```

- [ ] **Step 4: Run tests; will still fail because `_send_via_twilio` doesn't exist**

Run: `pytest tests/services/test_sms_dispatch.py -v`
Expected: All 4 still FAIL (missing `_send_via_twilio`).

- [ ] **Step 5: This is Task A4's territory. STOP here and commit what works.**

```bash
git add services/sms.py tests/services/test_sms_dispatch.py
git commit -m "feat(sms): provider dispatcher services/sms.py (telnyx | twilio)

send_sms_raw(to, body) reads SMS_PROVIDER env at call time.
Default = twilio for back-compat. Failing tests cover all 4 branches
including unknown provider. clients.sms_client._send_via_twilio is
added in the next task.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task A4: Refactor `clients/sms_client.py` to use `services.sms.send_sms_raw` internally

**Files:**
- Modify: `clients/sms_client.py`

Goal: extract the existing Twilio call (`client.messages.create(body=..., from_=..., to=...)`) into a small `_send_via_twilio(to, body) → message_id | None` function. Then refactor each high-level function (`send_booking_confirmation_sms`, `send_cancellation_sms`, etc.) to construct the body locally as today, but call `services.sms.send_sms_raw(to=phone, body=body)` instead of `client.messages.create(...)` directly. This is the swap that makes `SMS_PROVIDER=telnyx` work end-to-end.

- [ ] **Step 1: Read current `clients/sms_client.py` end-to-end to identify every Twilio call site**

Run: `grep -n "client\.messages\.create\|Client(account_sid" clients/sms_client.py`

You should find:
- The Twilio `Client(account_sid, auth_token)` construction (around line 45–60).
- One or more `client.messages.create(body=..., from_=..., to=...)` call sites inside `send_booking_confirmation_sms`, `send_cancellation_sms`, `send_reschedule_confirmation_sms`, `send_whatsapp`, and the `_delayed` variants.

- [ ] **Step 2: Add `_send_via_twilio` near the top of `clients/sms_client.py`**

Insert this directly under the existing module-level imports and env-var loads:

```python
def _send_via_twilio(*, to: str, body: str) -> str | None:
    """Pure Twilio transport. No body construction.

    Returns the Twilio message SID on success, None on failure or when
    the Twilio creds are not configured (so dev runs don't crash).
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_PHONE_NUMBER")
    if not (account_sid and auth_token and from_phone):
        return None
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=body, from_=from_phone, to=to)
        return msg.sid
    except Exception:
        return None
```

- [ ] **Step 3: Replace every `client.messages.create(body=..., from_=..., to=...)` call site**

For each existing function (`send_booking_confirmation_sms`, `send_cancellation_sms`, `send_reschedule_confirmation_sms`, `send_whatsapp`, and any `_delayed` variants that finally call into Twilio), keep all the body-construction logic but replace the final Twilio call with:

```python
from services.sms import send_sms_raw  # at top of file
...
msg_id = send_sms_raw(to=phone, body=body)
return msg_id is not None
```

For functions that previously returned `bool`, keep returning `bool`. For functions that previously returned a dict (e.g., `send_whatsapp`), the WhatsApp path stays on Twilio for now (Telnyx WhatsApp is a separate integration) — call `_send_via_twilio(to=..., body=...)` directly and skip the dispatcher.

- [ ] **Step 4: Run the new dispatch tests**

Run: `pytest tests/services/test_sms_dispatch.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Run the FULL existing test suite to confirm no regressions**

Run: `pytest -x -q --tb=short`
Expected: All previously-green tests stay green. The Twilio path is exercised through the same high-level function signatures — no caller changes.

If anything goes red, the most likely cause is an existing test that mocked `client.messages.create` directly. Update those tests to mock `services.sms.send_sms_raw` (or `clients.sms_client._send_via_twilio`) instead.

- [ ] **Step 6: Commit**

```bash
git add clients/sms_client.py
git commit -m "refactor(sms): route Twilio sends through services.sms.send_sms_raw

Internal transport refactor. Every Twilio send-site in
clients/sms_client.py now calls services.sms.send_sms_raw, which
dispatches to telnyx or twilio per SMS_PROVIDER env. Default stays
twilio. No caller signature changes; no behavior change at default.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task A5: Document env vars + flip-day runbook

**Files:**
- Modify: `.env.example` (or create if missing)
- Modify: `README.md` or `docs/runbooks/` — add a short Telnyx cutover runbook

- [ ] **Step 1: Add Telnyx env vars to `.env.example`**

Append:

```
# --- SMS provider selection ---
# telnyx | twilio. Default twilio. Flip to telnyx after the Telnyx
# number is provisioned and tested. Rollback = flip back to twilio.
SMS_PROVIDER=twilio

# --- Telnyx Messaging (required when SMS_PROVIDER=telnyx) ---
TELNYX_API_KEY=
TELNYX_MESSAGING_PROFILE_ID=
TELNYX_SMS_FROM_NUMBER=
# Ed25519 public key (base64) from the Messaging Profile webhook config
TELNYX_PUBLIC_KEY=
```

- [ ] **Step 2: Create `docs/runbooks/2026-06-09-telnyx-sms-cutover.md`**

```markdown
# Telnyx SMS cutover runbook

## Pre-flight (operational, NOT code)
1. Telnyx Messaging Profile created in Telnyx Portal.
2. Number(s) provisioned with SMS enabled + added to the profile.
3. Webhook URL set to `https://<dental-api-host>/webhooks/telnyx/sms-inbound`.
4. Ed25519 public key copied from profile → Secret Manager as `TELNYX_PUBLIC_KEY`.
5. `TELNYX_API_KEY`, `TELNYX_MESSAGING_PROFILE_ID`, `TELNYX_SMS_FROM_NUMBER` in Secret Manager.

## Cutover
1. Deploy current dental-api with `SMS_PROVIDER=twilio` (no behavior change).
2. Send a manual test SMS via Telnyx Portal to verify end-to-end inbound reception.
3. Flip Cloud Run env: `SMS_PROVIDER=telnyx`. Single env update.
4. Trigger one real booking SMS via test booking; verify SMS lands.
5. Monitor for 1 week.

## Rollback
Flip Cloud Run env back to `SMS_PROVIDER=twilio`. No code change needed.
```

- [ ] **Step 3: Commit**

```bash
git add .env.example docs/runbooks/2026-06-09-telnyx-sms-cutover.md
git commit -m "docs(telnyx): env vars + cutover/rollback runbook

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

**End of Phase A.** Main agent halts here and hands off to subagents for Phase B.

---

# Phase B — Reminder, reply, reschedule handoff (subagent-driven)

Each Phase B task is dispatched as one subagent invocation per the subagent-driven-development pattern. Tasks B1 → B13 are sequential — each one builds on the previous.

## Task B1: Alembic migration — `AppointmentReminder` column additions

**Files:**
- Create: `alembic/versions/<auto>_appointment_reminder_sms_columns.py`
- Modify: `database/ops/models.py:43-52` (mirror columns in the SQLAlchemy model)

- [ ] **Step 1: Generate migration scaffold**

Run: `cd /Users/giahuyhoangle/Projects/dental-system/dental-api/.claude/worktrees/sms-reminder-telnyx && alembic revision -m "appointment reminder sms columns"`

A new file is created under `alembic/versions/`. Note the revision filename.

- [ ] **Step 2: Fill in `upgrade()` and `downgrade()` in the new migration**

```python
"""appointment reminder sms columns

Revision ID: <auto-generated>
Revises: <previous head>
Create Date: 2026-06-09

"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    with op.batch_alter_table("appointment_reminders") as batch:
        batch.add_column(sa.Column("provider", sa.String(), nullable=False, server_default="telnyx"))
        batch.add_column(sa.Column("outbound_message_id", sa.String(), nullable=True))
        batch.add_column(sa.Column("reply_received_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("reply_parsed_intent", sa.String(), nullable=True))
        batch.add_column(sa.Column("reply_raw_text", sa.Text(), nullable=True))
        batch.add_column(sa.Column("reschedule_token", sa.String(), nullable=True))
        batch.add_column(sa.Column("reschedule_token_used_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("reschedule_token_expires_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("ambiguous_reply_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_index(
        "ix_appointment_reminders_reschedule_token",
        "appointment_reminders",
        ["reschedule_token"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_appointment_reminders_reschedule_token", table_name="appointment_reminders")
    with op.batch_alter_table("appointment_reminders") as batch:
        for col in (
            "ambiguous_reply_count",
            "reschedule_token_expires_at",
            "reschedule_token_used_at",
            "reschedule_token",
            "reply_raw_text",
            "reply_parsed_intent",
            "reply_received_at",
            "outbound_message_id",
            "provider",
        ):
            batch.drop_column(col)
```

- [ ] **Step 3: Mirror the columns in `database/ops/models.py`**

Edit `AppointmentReminder` (lines 43-52) to add:

```python
provider = Column(String, nullable=False, default="telnyx")
outbound_message_id = Column(String, nullable=True)
reply_received_at = Column(DateTime, nullable=True)
reply_parsed_intent = Column(String, nullable=True)
reply_raw_text = Column(Text, nullable=True)
reschedule_token = Column(String, nullable=True, index=True)
reschedule_token_used_at = Column(DateTime, nullable=True)
reschedule_token_expires_at = Column(DateTime, nullable=True)
ambiguous_reply_count = Column(Integer, nullable=False, default=0)
```

- [ ] **Step 4: Run migration tests**

Run: `pytest tests/ -k "reminder" -q`
Expected: existing reminder tests still pass; SQLite in-memory schema gets the new columns at table creation.

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/*_appointment_reminder_sms_columns.py database/ops/models.py
git commit -m "feat(db): AppointmentReminder columns for SMS reminder MVP

provider, outbound_message_id, reply_received_at, reply_parsed_intent,
reply_raw_text, reschedule_token (+index), reschedule_token_used_at,
reschedule_token_expires_at, ambiguous_reply_count.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B2: `AppointmentMutationSource` enum + threading

**Files:**
- Modify: `api/v1/appointments/schemas.py`
- Modify: `api/v1/appointments/router.py` (cancel, status, reschedule endpoints)
- Create: `tests/api/test_appointment_mutation_source.py`

- [ ] **Step 1: Failing test**

```python
# tests/api/test_appointment_mutation_source.py
"""PUT /api/appointments/{id}/cancel accepts and records source."""

def test_cancel_with_source_records_outbound_sms_reply(client, db_session, mm_clinic):
    appt = _seed_scheduled_appointment(db_session, mm_clinic)
    resp = client.put(
        f"/api/appointments/{appt.id}/cancel",
        json={"reason": "test", "source": "outbound_sms_reply"},
    )
    assert resp.status_code == 200
    # Verify source was accepted (the endpoint may or may not echo it in
    # the response; the contract is "the request validates"); a follow-up
    # task will surface it in the call log / audit trail.


def test_cancel_without_source_defaults_to_inbound_call(client, db_session, mm_clinic):
    appt = _seed_scheduled_appointment(db_session, mm_clinic)
    resp = client.put(f"/api/appointments/{appt.id}/cancel", json={"reason": "test"})
    assert resp.status_code == 200


def test_cancel_with_bogus_source_rejected(client, db_session, mm_clinic):
    appt = _seed_scheduled_appointment(db_session, mm_clinic)
    resp = client.put(
        f"/api/appointments/{appt.id}/cancel",
        json={"reason": "test", "source": "carrier_pigeon"},
    )
    assert resp.status_code == 422  # Pydantic validation error
```

The `_seed_scheduled_appointment` helper goes at the top of the test file; the subagent should write a minimal seeding helper using `db_session` and the project's clinic/patient/appointment factories (see `tests/conftest.py` for fixtures).

- [ ] **Step 2: Run, expect failures (422 for the bogus-source test, others may pass if endpoint accepts unknown JSON keys)**

Run: `pytest tests/api/test_appointment_mutation_source.py -v`
Expected: at least the bogus-source test FAILs (currently accepts anything).

- [ ] **Step 3: Add enum + thread through schemas**

In `api/v1/appointments/schemas.py`:

```python
from enum import Enum

class AppointmentMutationSource(str, Enum):
    OUTBOUND_SMS_REPLY = "outbound_sms_reply"
    SELF_SERVICE_LINK = "self_service_link"
    INBOUND_CALL = "inbound_call"
    CLINIC_STAFF = "clinic_staff"
    SYSTEM = "system"


# Update existing request models, e.g.:
class AppointmentCancelRequest(BaseModel):
    reason: Optional[str] = None
    source: AppointmentMutationSource = AppointmentMutationSource.INBOUND_CALL


class AppointmentStatusUpdateRequest(BaseModel):
    status: str
    source: AppointmentMutationSource = AppointmentMutationSource.INBOUND_CALL


class AppointmentRescheduleRequest(BaseModel):
    # ... existing fields ...
    source: AppointmentMutationSource = AppointmentMutationSource.INBOUND_CALL
```

In `api/v1/appointments/router.py`, the endpoint functions accept the request model as before. The `source` field is now stored alongside the mutation — either on the appointment's `updated_by` column if one exists, OR in a new `appointment_audit_log` table (NOT in this MVP — for MVP, just accept + log the value; persistence is a follow-up).

For MVP: write `request.source.value` into a log line at the point of mutation. No DB persistence needed yet.

- [ ] **Step 4: Run tests; should now all PASS**

Run: `pytest tests/api/test_appointment_mutation_source.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add api/v1/appointments/schemas.py api/v1/appointments/router.py tests/api/test_appointment_mutation_source.py
git commit -m "feat(appointments): AppointmentMutationSource enum on status mutation requests

Adds optional source field to cancel/status/reschedule request schemas.
Defaults to inbound_call for back-compat. Validates against the enum.
MVP logs the value at point of mutation; DB persistence is a follow-up.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B3: SMS template files + loader

**Files:**
- Create: `templates/sms/reminder.en.txt`
- Create: `templates/sms/ack_confirmed.en.txt`
- Create: `templates/sms/ack_cancelled.en.txt`
- Create: `templates/sms/ack_reschedule.en.txt`
- Create: `templates/sms/ack_ambiguous.en.txt`
- Create: `services/sms_templates.py`
- Create: `tests/services/test_sms_templates.py`

- [ ] **Step 1: Write the 5 English template files**

`templates/sms/reminder.en.txt`:
```
Hi {first_name}, this is {clinic_name}. Reminder: your appointment is {when_human} with {provider_first_name}. Reply YES to confirm, NO to cancel, or RESCHEDULE for options. To pick a new time yourself: {reschedule_link}
```

`templates/sms/ack_confirmed.en.txt`:
```
Thanks! We'll see you at {when_human}. Reply CANCEL if anything changes.
```

`templates/sms/ack_cancelled.en.txt`:
```
Got it — your appointment is cancelled. To book again, call {clinic_phone} or visit {reschedule_link}.
```

`templates/sms/ack_reschedule.en.txt`:
```
Sure thing. Pick a new time here: {reschedule_link} — or call {clinic_phone} to talk to Emma.
```

`templates/sms/ack_ambiguous.en.txt`:
```
Sorry, I didn't catch that. Reply YES to confirm, NO to cancel, or RESCHEDULE for options.
```

(No `pa`/`hi`/`ar` files in MVP — these are added in a future iteration.)

- [ ] **Step 2: Write failing tests for the loader**

```python
# tests/services/test_sms_templates.py
"""Tests for services/sms_templates.py loader + render."""

import pytest


def test_render_reminder_en_substitutes_all_placeholders():
    from services.sms_templates import render
    out = render(
        "reminder", "en",
        first_name="Asim", clinic_name="Market Mall",
        when_human="Tue June 10 at 2 PM",
        provider_first_name="Soheil",
        reschedule_link="https://example.com/p/reschedule/tok123",
    )
    assert "Asim" in out
    assert "Market Mall" in out
    assert "Soheil" in out
    assert "Tue June 10 at 2 PM" in out
    assert "https://example.com/p/reschedule/tok123" in out


def test_render_falls_back_to_english_when_language_missing():
    from services.sms_templates import render
    out_pa = render("ack_confirmed", "pa", when_human="Tue 2 PM")
    out_en = render("ack_confirmed", "en", when_human="Tue 2 PM")
    assert out_pa == out_en  # pa file doesn't exist yet → falls back


def test_render_raises_keyerror_on_unknown_intent():
    from services.sms_templates import render
    with pytest.raises(KeyError):
        render("not_a_real_intent", "en")
```

- [ ] **Step 3: Implement `services/sms_templates.py`**

```python
# services/sms_templates.py
"""Load + render SMS templates from templates/sms/<intent>.<lang>.txt.

Templates use simple {placeholder} substitution via str.format_map.
Missing language files fall back to English. Unknown intent raises
KeyError so misuse is loud.
"""
from __future__ import annotations

from pathlib import Path

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "sms"
_KNOWN_INTENTS = {"reminder", "ack_confirmed", "ack_cancelled", "ack_reschedule", "ack_ambiguous"}


def _path(intent: str, lang: str) -> Path:
    return _TEMPLATE_DIR / f"{intent}.{lang}.txt"


def render(intent: str, lang: str, **vars) -> str:
    if intent not in _KNOWN_INTENTS:
        raise KeyError(f"unknown SMS intent: {intent!r}")
    p = _path(intent, lang)
    if not p.exists():
        p = _path(intent, "en")
    body = p.read_text().rstrip("\n")
    # Tolerate missing placeholders so tests can render with partial vars.
    return body.format_map(_Defaultdict(vars))


class _Defaultdict(dict):
    def __missing__(self, key):
        return "{" + key + "}"
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/services/test_sms_templates.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/sms/ services/sms_templates.py tests/services/test_sms_templates.py
git commit -m "feat(sms): template files + loader (en MVP, pa/hi/ar future)

5 intents: reminder, ack_confirmed, ack_cancelled, ack_reschedule,
ack_ambiguous. Loader falls back to English when language file missing.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B4: `services/reply_parser.py` — regex matrix

**Files:**
- Create: `services/reply_parser.py`
- Create: `tests/services/test_reply_parser.py`

- [ ] **Step 1: Write failing tests for the regex matrix**

```python
# tests/services/test_reply_parser.py
"""Tests for services/reply_parser.py.

Phase 1: regex matrix only. LLM fallback added in B5.
"""

import pytest
from services.reply_parser import parse, ReplyIntent


@pytest.mark.parametrize("text", ["yes", "Y", "yeah", "yep", "ok", "okay", "Confirm", "👍"])
def test_parse_confirmed_via_regex(text):
    intent, source = parse(text)
    assert intent == ReplyIntent.CONFIRMED
    assert source == "regex"


@pytest.mark.parametrize("text", ["no", "N", "nope", "Cancel", "nah"])
def test_parse_cancelled_via_regex(text):
    intent, source = parse(text)
    assert intent == ReplyIntent.CANCELLED


@pytest.mark.parametrize("text", ["reschedule", "I want to move it", "change my appt", "switch to next week", "another day"])
def test_parse_reschedule_via_regex(text):
    intent, source = parse(text)
    assert intent == ReplyIntent.RESCHEDULE_REQUESTED


@pytest.mark.parametrize("text", ["haan", "ji", "haa"])
def test_parse_confirmed_via_hindi_punjabi_latin(text):
    intent, _ = parse(text)
    assert intent == ReplyIntent.CONFIRMED


@pytest.mark.parametrize("text", ["nahi", "nahin", "nai"])
def test_parse_cancelled_via_hindi_punjabi_latin(text):
    intent, _ = parse(text)
    assert intent == ReplyIntent.CANCELLED


def test_parse_returns_ambiguous_for_freeform_without_regex_match():
    """Freeform text not covered by regex → falls through; LLM disabled in this task → AMBIGUOUS."""
    intent, source = parse("can we do something next Tuesday afternoon")
    assert intent == ReplyIntent.AMBIGUOUS
    assert source == "regex"  # LLM not yet wired
```

- [ ] **Step 2: Run, expect failures**

Run: `pytest tests/services/test_reply_parser.py -v`
Expected: All FAIL (module doesn't exist).

- [ ] **Step 3: Implement regex matrix**

```python
# services/reply_parser.py
"""Hybrid SMS reply parser.

Stage 1 (this task, B4): regex matrix over normalized text. Cheap and
deterministic; expected to cover ~95% of replies.

Stage 2 (next task, B5): LLM fallback via Gemini 3.1 Flash for anything
the regex doesn't match.
"""
from __future__ import annotations

import re
from enum import Enum


class ReplyIntent(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    RESCHEDULE_REQUESTED = "reschedule_requested"
    AMBIGUOUS = "ambiguous"


_CONFIRMED_PATTERNS = [
    re.compile(r"^(y|yes|yeah|yep|ok|okay|confirm|sure|👍)$", re.IGNORECASE),
    re.compile(r"^(haan|ji|haa|haanji)$", re.IGNORECASE),   # pa/hi Latin-script
    re.compile(r"^(naam|aiwa|na'?am)$", re.IGNORECASE),     # ar Latin-script
]

_CANCELLED_PATTERNS = [
    re.compile(r"^(n|no|nope|cancel|nah)$", re.IGNORECASE),
    re.compile(r"^(nahi|nahin|nai)$", re.IGNORECASE),       # pa/hi Latin-script
    re.compile(r"^(la|laa)$", re.IGNORECASE),               # ar Latin-script
]

_RESCHEDULE_PATTERNS = [
    re.compile(r"\b(reschedule|move|change|switch|different|another)\b", re.IGNORECASE),
]


def _normalize(text: str) -> str:
    return text.strip()


def parse(text: str) -> tuple[ReplyIntent, str]:
    """Return (intent, parser_source) where source is 'regex' or 'llm'."""
    norm = _normalize(text)
    if not norm:
        return ReplyIntent.AMBIGUOUS, "regex"
    for pat in _CONFIRMED_PATTERNS:
        if pat.fullmatch(norm) or pat.search(norm):
            return ReplyIntent.CONFIRMED, "regex"
    for pat in _CANCELLED_PATTERNS:
        if pat.fullmatch(norm) or pat.search(norm):
            return ReplyIntent.CANCELLED, "regex"
    for pat in _RESCHEDULE_PATTERNS:
        if pat.search(norm):
            return ReplyIntent.RESCHEDULE_REQUESTED, "regex"
    return ReplyIntent.AMBIGUOUS, "regex"
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/services/test_reply_parser.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add services/reply_parser.py tests/services/test_reply_parser.py
git commit -m "feat(sms): regex reply parser for confirm/cancel/reschedule + pa/hi/ar Latin

Stage 1 of hybrid parser. Covers expected ~95% of replies. LLM
fallback (Gemini Flash) added in next task.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B5: `services/reply_parser.py` — LLM fallback (Gemini Flash)

**Files:**
- Modify: `services/reply_parser.py`
- Modify: `tests/services/test_reply_parser.py`

- [ ] **Step 1: Add failing tests for LLM fallback**

Append to `tests/services/test_reply_parser.py`:

```python
from unittest.mock import patch


def test_freeform_text_falls_back_to_llm_when_enabled(monkeypatch):
    monkeypatch.setenv("SMS_REPLY_LLM_FALLBACK", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    with patch("services.reply_parser._classify_via_llm", return_value=ReplyIntent.RESCHEDULE_REQUESTED) as mock_llm:
        intent, source = parse("can we do something next Tuesday afternoon")
    assert intent == ReplyIntent.RESCHEDULE_REQUESTED
    assert source == "llm"
    mock_llm.assert_called_once()


def test_llm_fallback_returns_ambiguous_on_classifier_error(monkeypatch):
    monkeypatch.setenv("SMS_REPLY_LLM_FALLBACK", "true")
    with patch("services.reply_parser._classify_via_llm", side_effect=Exception("boom")):
        intent, source = parse("blah blah")
    assert intent == ReplyIntent.AMBIGUOUS
    assert source == "llm"  # we attempted, just failed


def test_llm_fallback_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SMS_REPLY_LLM_FALLBACK", raising=False)
    with patch("services.reply_parser._classify_via_llm") as mock_llm:
        intent, source = parse("can we do something next Tuesday afternoon")
    mock_llm.assert_not_called()
    assert intent == ReplyIntent.AMBIGUOUS
    assert source == "regex"
```

- [ ] **Step 2: Run, expect 3 failures**

Run: `pytest tests/services/test_reply_parser.py -v -k llm`
Expected: 3 FAIL.

- [ ] **Step 3: Add LLM fallback to `services/reply_parser.py`**

```python
# Append to services/reply_parser.py:
import os
import logging

logger = logging.getLogger(__name__)

_LLM_FALLBACK_PROMPT = (
    "Classify this SMS reply to an appointment confirmation request. "
    "Reply with ONE word from this set: CONFIRMED, CANCELLED, "
    "RESCHEDULE_REQUESTED, AMBIGUOUS.\n\nSMS: {text}"
)


def _classify_via_llm(text: str) -> ReplyIntent:
    """Call Gemini 3.1 Flash to classify. Returns ReplyIntent or AMBIGUOUS on parse failure."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=_LLM_FALLBACK_PROMPT.format(text=text),
    )
    raw = (resp.text or "").strip().upper()
    if raw.startswith("CONFIRMED"):
        return ReplyIntent.CONFIRMED
    if raw.startswith("CANCELLED"):
        return ReplyIntent.CANCELLED
    if raw.startswith("RESCHEDULE"):
        return ReplyIntent.RESCHEDULE_REQUESTED
    return ReplyIntent.AMBIGUOUS
```

Update `parse()` to call LLM when regex returns AMBIGUOUS and the env flag is set:

```python
def parse(text: str) -> tuple[ReplyIntent, str]:
    norm = _normalize(text)
    if not norm:
        return ReplyIntent.AMBIGUOUS, "regex"
    for pat in _CONFIRMED_PATTERNS:
        if pat.fullmatch(norm) or pat.search(norm):
            return ReplyIntent.CONFIRMED, "regex"
    for pat in _CANCELLED_PATTERNS:
        if pat.fullmatch(norm) or pat.search(norm):
            return ReplyIntent.CANCELLED, "regex"
    for pat in _RESCHEDULE_PATTERNS:
        if pat.search(norm):
            return ReplyIntent.RESCHEDULE_REQUESTED, "regex"

    # Stage 2: LLM fallback
    if os.getenv("SMS_REPLY_LLM_FALLBACK", "false").lower() == "true":
        try:
            return _classify_via_llm(norm), "llm"
        except Exception as exc:
            logger.warning("LLM fallback failed: %s", exc)
            return ReplyIntent.AMBIGUOUS, "llm"
    return ReplyIntent.AMBIGUOUS, "regex"
```

- [ ] **Step 4: Run all parser tests**

Run: `pytest tests/services/test_reply_parser.py -v`
Expected: All PASS (regex matrix + LLM fallback tests).

- [ ] **Step 5: Commit**

```bash
git add services/reply_parser.py tests/services/test_reply_parser.py
git commit -m "feat(sms): Gemini Flash LLM fallback for ambiguous SMS replies

Gated on SMS_REPLY_LLM_FALLBACK env (default off). On regex AMBIGUOUS
+ flag on, classify via Gemini 2.5 Flash. Parse errors degrade to
AMBIGUOUS with source='llm' so audit trail shows the attempt.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B6: Cron scan endpoint — pick-due logic + quiet-hours + skip-too-late

**Files:**
- Create: `api/cron/__init__.py` (empty)
- Create: `api/cron/reminders.py`
- Create: `tests/api/test_cron_reminders.py`

- [ ] **Step 1: Failing tests for due-row selection**

```python
# tests/api/test_cron_reminders.py
"""Tests for POST /cron/reminders/scan."""

from datetime import datetime, timedelta, timezone


def _seed_appointment(db_session, mm_clinic, *, hours_out: float, status: str = "SCHEDULED"):
    """Create an appointment N hours from now (UTC). Returns appointment id."""
    # The subagent writes this helper using existing patient/provider factories
    # from tests/conftest.py.
    ...


def test_scan_creates_reminder_for_appointment_24h_out(client, db_session, mm_clinic, monkeypatch):
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    appt_id = _seed_appointment(db_session, mm_clinic, hours_out=24.0)

    # Mock telnyx send so we observe the call but don't hit the network.
    from unittest.mock import patch
    with patch("clients.telnyx_messaging.send_message", return_value="msg_42") as mock_send:
        resp = client.post("/cron/reminders/scan", headers=_internal_secret_headers())

    assert resp.status_code == 200
    # Reminder row created with sent_at populated
    from database.ops.models import AppointmentReminder
    row = db_session.query(AppointmentReminder).filter_by(appointment_id=appt_id).first()
    assert row is not None
    assert row.status == "sent"
    assert row.outbound_message_id == "msg_42"
    mock_send.assert_called_once()


def test_scan_skips_appointment_outside_offset_window(client, db_session, mm_clinic, monkeypatch):
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    _seed_appointment(db_session, mm_clinic, hours_out=72.0)  # too far
    _seed_appointment(db_session, mm_clinic, hours_out=2.0)   # too close (skip-too-late)

    resp = client.post("/cron/reminders/scan", headers=_internal_secret_headers())
    assert resp.status_code == 200
    assert resp.json()["sent_count"] == 0


def test_scan_idempotent_under_overlapping_runs(client, db_session, mm_clinic, monkeypatch):
    """UNIQUE(appointment_id, channel) prevents double-send."""
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    _seed_appointment(db_session, mm_clinic, hours_out=24.0)
    from unittest.mock import patch
    with patch("clients.telnyx_messaging.send_message", return_value="msg"):
        r1 = client.post("/cron/reminders/scan", headers=_internal_secret_headers())
        r2 = client.post("/cron/reminders/scan", headers=_internal_secret_headers())
    assert r1.json()["sent_count"] == 1
    assert r2.json()["sent_count"] == 0  # second scan finds nothing new
```

The `_internal_secret_headers()` helper returns `{"X-Internal-Secret": os.getenv("DENTAL_API_INTERNAL_SECRET", "test_secret")}` and the test sets that env at the top via `monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "test_secret")`. The `_seed_appointment` helper uses the existing conftest factories (look for clinic / provider / patient seeders in `tests/conftest.py` and `tests/test_public_slots_api.py` for templates).

- [ ] **Step 2: Run, expect failures**

Run: `pytest tests/api/test_cron_reminders.py -v`
Expected: All FAIL — endpoint doesn't exist.

- [ ] **Step 3: Implement `api/cron/reminders.py`**

```python
# api/cron/reminders.py
"""Cron endpoint hit by Cloud Scheduler every 5 min.

Picks appointments whose target send time falls in the next 5 minutes
(with quiet-hours deferment and skip-too-late guards) and inserts +
sends an AppointmentReminder row for each.

Auth: X-Internal-Secret header (same DENTAL_API_INTERNAL_SECRET used
by /api/public/* endpoints in the holds branch).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone, time as dtime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from api.dependencies.auth import require_internal_secret
from api.dependencies.db import get_db
from database.ops.models import AppointmentReminder
from database.models import Appointment  # adjust import path to actual location
from services import sms as sms_service
from services import sms_templates


router = APIRouter(prefix="/cron", tags=["cron"])


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _within_quiet_hours(t: datetime, *, start_h: int, end_h: int) -> bool:
    """True if t falls in the daily quiet window [start_h, end_h) clinic-local.

    Quiet window straddles midnight when end_h < start_h.
    """
    h = t.hour
    if start_h < end_h:
        return start_h <= h < end_h
    return h >= start_h or h < end_h


def _next_morning(t: datetime, *, open_h: int) -> datetime:
    """Bump t forward to the next clinic open_h:00, same day or next day."""
    candidate = t.replace(hour=open_h, minute=0, second=0, microsecond=0)
    if candidate <= t:
        candidate += timedelta(days=1)
    return candidate


@router.post("/reminders/scan", dependencies=[Depends(require_internal_secret)])
def scan(db: Session = Depends(get_db)):
    offset_hours = _env_int("REMINDER_OFFSET_HOURS", 24)
    quiet_start = _env_int("QUIET_HOURS_START", 21)
    quiet_end = _env_int("QUIET_HOURS_END", 8)
    min_lead_minutes = _env_int("MIN_LEAD_MINUTES", 30)

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(minutes=5)

    # Pick appointments whose target_send_time would fall in (now, window_end].
    # target_send_time = appointment.start_time - offset_hours
    # → appointment.start_time in (now + offset_hours, window_end + offset_hours].
    range_start = now + timedelta(hours=offset_hours)
    range_end = window_end + timedelta(hours=offset_hours)

    candidates = (
        db.query(Appointment)
        .filter(Appointment.start_time.between(range_start, range_end))
        .filter(Appointment.status == "SCHEDULED")
        .all()
    )

    sent_count = 0
    skipped_too_late = 0
    skipped_quiet_hours_only = 0  # actually deferred, not skipped
    for appt in candidates:
        # Dedup: only one reminder per (appointment, channel).
        existing = (
            db.query(AppointmentReminder)
            .filter_by(appointment_id=appt.id, channel="sms")
            .first()
        )
        if existing is not None:
            continue

        target_send = appt.start_time - timedelta(hours=offset_hours)
        if target_send.tzinfo is None:
            target_send = target_send.replace(tzinfo=timezone.utc)

        # Quiet-hours deferment (clinic-local — simplified to UTC here;
        # real clinic timezone handling layered on once per-clinic tz is
        # exposed on the appointment).
        if _within_quiet_hours(target_send, start_h=quiet_start, end_h=quiet_end):
            target_send = _next_morning(target_send, open_h=quiet_end)

        # Skip if too late.
        if target_send >= appt.start_time - timedelta(minutes=min_lead_minutes):
            # Record the skip for auditability.
            db.add(AppointmentReminder(
                id=str(uuid.uuid4()),
                appointment_id=appt.id,
                channel="sms",
                offset_minutes=offset_hours * 60,
                scheduled_at=target_send,
                status="skipped_too_late",
                provider=os.getenv("SMS_PROVIDER", "twilio"),
            ))
            db.commit()
            skipped_too_late += 1
            continue

        # Build the reminder body.
        reschedule_token = str(uuid.uuid4())
        body = sms_templates.render(
            "reminder", "en",
            first_name=appt.patient.first_name,
            clinic_name=appt.clinic.name,
            when_human=_human_readable_when(appt.start_time, appt.clinic),
            provider_first_name=appt.provider.first_name,
            reschedule_link=_reschedule_link(reschedule_token),
        )

        # Send.
        message_id = sms_service.send_sms_raw(to=appt.patient.phone, body=body)

        reminder = AppointmentReminder(
            id=str(uuid.uuid4()),
            appointment_id=appt.id,
            channel="sms",
            offset_minutes=offset_hours * 60,
            scheduled_at=target_send,
            sent_at=datetime.now(timezone.utc) if message_id else None,
            status="sent" if message_id else "failed",
            failure_reason=None if message_id else "send returned None",
            provider=os.getenv("SMS_PROVIDER", "twilio"),
            outbound_message_id=message_id,
            reschedule_token=reschedule_token,
            reschedule_token_expires_at=appt.start_time + timedelta(hours=48),
        )
        db.add(reminder)
        db.commit()
        if message_id:
            sent_count += 1

    return {
        "sent_count": sent_count,
        "skipped_too_late": skipped_too_late,
        "candidates_total": len(candidates),
    }


def _human_readable_when(ts: datetime, clinic) -> str:
    """Format start_time in clinic-local TZ as 'Tue June 10 at 2 PM'."""
    # The subagent reuses any existing helper in services/notifications.py
    # (look for _format_local_date_time around lines 44-49 there).
    from services.notifications import _format_local_date_time
    date_str, time_str = _format_local_date_time(ts, clinic)
    return f"{date_str} at {time_str}"


def _reschedule_link(token: str) -> str:
    base = os.getenv("DENTAL_API_PUBLIC_BASE_URL", "")
    return f"{base}/p/reschedule/{token}"
```

- [ ] **Step 4: Register the router in `api/main.py`**

Find the v1 router include block (around lines 119-140) and add:

```python
from api.cron.reminders import router as _cron_reminders_router
app.include_router(_cron_reminders_router)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_cron_reminders.py -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add api/cron/ api/main.py tests/api/test_cron_reminders.py
git commit -m "feat(cron): POST /cron/reminders/scan picks due appointments, sends SMS

Offset, quiet-hours deferment, skip-too-late, UNIQUE-constraint dedup,
status writeback. Internal-secret auth. Cloud Scheduler-driven.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B7: Telnyx inbound webhook — signature verify + payload extraction

**Files:**
- Create: `api/webhooks/__init__.py` (empty)
- Create: `api/webhooks/telnyx.py`
- Create: `tests/api/test_telnyx_webhook.py`

- [ ] **Step 1: Failing tests for signature verify on the webhook**

```python
# tests/api/test_telnyx_webhook.py
"""Tests for POST /webhooks/telnyx/sms-inbound."""

import base64
import json
import time
import nacl.signing


def _sign(signing_key, body_bytes, ts):
    msg = ts.encode() + b"|" + body_bytes
    return base64.b64encode(signing_key.sign(msg).signature).decode()


def test_webhook_rejects_invalid_signature(client, monkeypatch):
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
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode())
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
```

- [ ] **Step 2: Run, expect failures (endpoint missing)**

Run: `pytest tests/api/test_telnyx_webhook.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `api/webhooks/telnyx.py` — signature verify + routing**

```python
# api/webhooks/telnyx.py
"""Telnyx inbound SMS webhook.

Verifies Ed25519 signature, extracts message, looks up a matching
AppointmentReminder (within last 7 days, no reply yet). If no match,
the payload is forwarded to the existing chat_api SMS path.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from api.dependencies.db import get_db
from clients import telnyx_messaging
from database.ops.models import AppointmentReminder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/telnyx", tags=["webhooks"])


@router.post("/sms-inbound")
async def sms_inbound(
    request: Request,
    db: Session = Depends(get_db),
    signature: str | None = Header(None, alias="Telnyx-Signature-ED25519"),
    timestamp: str | None = Header(None, alias="Telnyx-Timestamp"),
):
    raw = await request.body()
    if not (signature and timestamp and telnyx_messaging.verify_webhook_signature(raw, signature, timestamp)):
        raise HTTPException(status_code=401, detail="invalid telnyx signature")

    payload = json.loads(raw)
    data = payload.get("data", {})
    if data.get("event_type") != "message.received":
        return {"routed_to": "ignored_event", "event_type": data.get("event_type")}

    msg = data.get("payload", {})
    from_phone = (msg.get("from") or {}).get("phone_number")
    text = msg.get("text") or ""
    message_id = msg.get("id")
    if not from_phone:
        return {"routed_to": "ignored_no_from"}

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    # Concrete query: join AppointmentReminder → Appointment → Patient,
    # filter Patient.phone == from_phone. Subagent verifies relationship
    # names by reading database/models.py for Appointment.patient /
    # Patient.phone before writing the query; if Patient is in a
    # different module, import accordingly.
    from database.models import Appointment, Patient
    reminder = (
        db.query(AppointmentReminder)
        .join(Appointment, AppointmentReminder.appointment_id == Appointment.id)
        .join(Patient, Appointment.patient_id == Patient.id)
        .filter(AppointmentReminder.reply_received_at.is_(None))
        .filter(AppointmentReminder.sent_at >= cutoff)
        .filter(Patient.phone == from_phone)
        .order_by(AppointmentReminder.sent_at.desc())
        .first()
    )

    if reminder is None:
        # No matching reminder — pass through to existing patient-SMS thread system.
        # The chat_api fallthrough is a no-op stub in MVP; later wired via
        # services/chat_api_bridge.py.
        return {"routed_to": "fallthrough"}

    # Action dispatch happens in Task B8.
    return {"routed_to": "reminder_match", "reminder_id": reminder.id, "text": text, "message_id": message_id}
```

The subagent should resolve the SQLAlchemy join path to the patient phone using the actual relationship names — search `database/models.py` for `Appointment.patient` / `patient.phone`.

- [ ] **Step 4: Wire router into `api/main.py`**

Same pattern as Task B6:

```python
from api.webhooks.telnyx import router as _telnyx_webhook_router
app.include_router(_telnyx_webhook_router)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_telnyx_webhook.py -v`
Expected: 2 PASS (signature reject + fallthrough).

- [ ] **Step 6: Commit**

```bash
git add api/webhooks/ api/main.py tests/api/test_telnyx_webhook.py
git commit -m "feat(webhook): Telnyx SMS inbound endpoint with signature verify + routing

Verifies Ed25519 signature. On match: looks up AppointmentReminder by
from_phone within last 7d with no reply yet. On no match: passes
through to chat_api SMS-thread fallthrough (stubbed in MVP).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B8: Telnyx webhook — action dispatch for all 4 intents

**Files:**
- Modify: `api/webhooks/telnyx.py` (add action dispatch after the reminder lookup)
- Modify: `tests/api/test_telnyx_webhook.py` (add 4 intent-dispatch tests)

- [ ] **Step 1: Failing tests for all 4 intents**

Add to `tests/api/test_telnyx_webhook.py` (one test per intent — sketch shown for CONFIRMED, the subagent extends to CANCELLED, RESCHEDULE_REQUESTED, AMBIGUOUS):

```python
def test_webhook_dispatches_confirmed_updates_status_and_sends_ack(client, db_session, mm_clinic, monkeypatch):
    # 1. seed appointment + reminder
    appt = _seed_scheduled_appointment(db_session, mm_clinic, phone="+14035550001")
    reminder = _seed_reminder(db_session, appointment_id=appt.id, sent_at_minutes_ago=60)
    # 2. send YES via webhook
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode())
    body = json.dumps({
        "data": {"event_type": "message.received", "payload": {
            "from": {"phone_number": "+14035550001"},
            "to": [{"phone_number": "+14035550000"}],
            "text": "yes", "id": "msg_in_1",
        }}
    }).encode()
    ts = str(int(time.time()))
    sig = _sign(signing_key, body, ts)
    with patch("clients.telnyx_messaging.send_message", return_value="msg_ack_1") as ack:
        resp = client.post("/webhooks/telnyx/sms-inbound", content=body, headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        })
    # 3. assert appointment now CONFIRMED + ack SMS sent
    db_session.refresh(appt)
    assert appt.status == "CONFIRMED"
    db_session.refresh(reminder)
    assert reminder.reply_parsed_intent == "confirmed"
    assert reminder.reply_received_at is not None
    ack.assert_called_once()
```

The subagent writes equivalents for CANCELLED, RESCHEDULE_REQUESTED, AMBIGUOUS (with the "second ambiguous → no ack" rule).

- [ ] **Step 2: Run, expect failures**

Run: `pytest tests/api/test_telnyx_webhook.py -v -k dispatch`
Expected: FAIL.

- [ ] **Step 3: Add action dispatch to `api/webhooks/telnyx.py`**

Replace the `# Action dispatch happens in Task B8.` placeholder with:

```python
from services.reply_parser import parse, ReplyIntent
from services import sms as sms_service, sms_templates

intent, source = parse(text)

# Persist the reply on the reminder.
reminder.reply_received_at = datetime.now(timezone.utc)
reminder.reply_parsed_intent = intent.value
reminder.reply_raw_text = text

# Dispatch action.
appt = reminder.appointment
clinic_phone = appt.clinic.contact_phone or ""
reschedule_link = f"{os.getenv('DENTAL_API_PUBLIC_BASE_URL','')}/p/reschedule/{reminder.reschedule_token}"

if intent == ReplyIntent.CONFIRMED:
    appt.status = "CONFIRMED"
    ack_body = sms_templates.render("ack_confirmed", "en",
        when_human=_human_readable_when(appt.start_time, appt.clinic))
elif intent == ReplyIntent.CANCELLED:
    appt.status = "CANCELLED"
    ack_body = sms_templates.render("ack_cancelled", "en",
        clinic_phone=clinic_phone, reschedule_link=reschedule_link)
elif intent == ReplyIntent.RESCHEDULE_REQUESTED:
    # Status stays SCHEDULED; the "needs reschedule" semantic is derived.
    ack_body = sms_templates.render("ack_reschedule", "en",
        clinic_phone=clinic_phone, reschedule_link=reschedule_link)
elif intent == ReplyIntent.AMBIGUOUS:
    reminder.ambiguous_reply_count = (reminder.ambiguous_reply_count or 0) + 1
    if reminder.ambiguous_reply_count >= 2:
        ack_body = None  # no auto-reply on second ambiguous; escalate
    else:
        ack_body = sms_templates.render("ack_ambiguous", "en")
else:
    ack_body = None

if ack_body:
    sms_service.send_sms_raw(to=from_phone, body=ack_body)

db.commit()
return {"routed_to": "reminder_match", "intent": intent.value, "source": source}
```

Reuse `_human_readable_when` helper from `api/cron/reminders.py` (or move it to a shared `services/datetime_formatting.py` if both endpoints need it).

- [ ] **Step 4: Run all webhook tests**

Run: `pytest tests/api/test_telnyx_webhook.py -v`
Expected: All PASS (signature reject, fallthrough, 4 intent dispatches).

- [ ] **Step 5: Commit**

```bash
git add api/webhooks/telnyx.py tests/api/test_telnyx_webhook.py
git commit -m "feat(webhook): action dispatch for confirmed/cancelled/reschedule/ambiguous

Updates appointment status (CONFIRMED, CANCELLED), persists reply
metadata on the reminder, sends ack SMS via services/sms with the
right template. Second-ambiguous suppresses auto-reply (escalation
state is derived in queries).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B9: `GET /p/reschedule/{token}` handoff endpoint

**Files:**
- Create: `api/public/reschedule.py`
- Create: `tests/api/test_reschedule_link.py`

- [ ] **Step 1: Failing tests**

```python
# tests/api/test_reschedule_link.py
def test_get_reschedule_valid_token_redirects_to_market_mall_with_session(client, db_session, mm_clinic, monkeypatch):
    monkeypatch.setenv("MARKET_MALL_WEBSITE_BASE_URL", "https://marketmall.example.com")
    appt = _seed_scheduled_appointment(db_session, mm_clinic)
    reminder = _seed_reminder_with_token(db_session, appointment_id=appt.id, token="tok_abc")
    resp = client.get(f"/p/reschedule/tok_abc", follow_redirects=False)
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert location.startswith("https://marketmall.example.com/reschedule?session=")


def test_get_reschedule_expired_token_returns_410(client, db_session, mm_clinic):
    appt = _seed_scheduled_appointment(db_session, mm_clinic)
    _seed_reminder_with_token(
        db_session, appointment_id=appt.id, token="tok_expired",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    resp = client.get("/p/reschedule/tok_expired")
    assert resp.status_code == 410


def test_get_reschedule_used_token_returns_410(client, db_session, mm_clinic):
    appt = _seed_scheduled_appointment(db_session, mm_clinic)
    _seed_reminder_with_token(
        db_session, appointment_id=appt.id, token="tok_used",
        used_at=datetime.now(timezone.utc),
    )
    resp = client.get("/p/reschedule/tok_used")
    assert resp.status_code == 410


def test_get_reschedule_unknown_token_returns_404(client):
    resp = client.get("/p/reschedule/never_existed")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run, expect failures**

Run: `pytest tests/api/test_reschedule_link.py -v -k get_reschedule`
Expected: FAIL.

- [ ] **Step 3: Implement `api/public/reschedule.py`**

```python
# api/public/reschedule.py
"""Token-based reschedule handoff.

GET /p/reschedule/{token}
  - 302 → MARKET_MALL_WEBSITE_BASE_URL/reschedule?session=<signed blob>
  - 404 unknown token
  - 410 expired/used token
"""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone

import nacl.signing
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from api.dependencies.db import get_db
from database.ops.models import AppointmentReminder

router = APIRouter(prefix="/p", tags=["public"])


def _sign_session(payload: dict) -> str:
    """Ed25519-sign a JSON payload with the dental-api private key.

    Reads RESCHEDULE_SESSION_SIGNING_KEY (base64-seed) from env. The
    public key is shared with market-mall-website's BFF out of band.
    """
    seed_b64 = os.environ["RESCHEDULE_SESSION_SIGNING_KEY"]
    sk = nacl.signing.SigningKey(base64.b64decode(seed_b64))
    body = json.dumps(payload, separators=(",", ":")).encode()
    signed = sk.sign(body)
    return base64.urlsafe_b64encode(signed.signature + b"||" + body).decode()


@router.get("/reschedule/{token}")
def get_reschedule(token: str, db: Session = Depends(get_db)):
    reminder = (
        db.query(AppointmentReminder)
        .filter_by(reschedule_token=token)
        .first()
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="token not found")
    now = datetime.now(timezone.utc)
    if reminder.reschedule_token_used_at is not None:
        raise HTTPException(status_code=410, detail="token already used")
    if reminder.reschedule_token_expires_at and reminder.reschedule_token_expires_at <= now:
        raise HTTPException(status_code=410, detail="token expired")

    appt = reminder.appointment
    session = _sign_session({
        "appointment_id": appt.id,
        "patient_id": appt.patient_id,
        "clinic_id": appt.clinic_id,
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + 1800,  # 30-min session TTL
    })
    base = os.environ.get("MARKET_MALL_WEBSITE_BASE_URL", "").rstrip("/")
    return RedirectResponse(url=f"{base}/reschedule?session={session}", status_code=302)
```

- [ ] **Step 4: Register router**

In `api/main.py`:

```python
from api.public.reschedule import router as _public_reschedule_router
app.include_router(_public_reschedule_router)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_reschedule_link.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/public/reschedule.py api/main.py tests/api/test_reschedule_link.py
git commit -m "feat(reschedule): GET /p/reschedule/{token} 302 to market-mall with signed session

Token lookup against AppointmentReminder.reschedule_token. 404 on
unknown, 410 on used/expired. On valid: signs a 30-min Ed25519 session
blob containing appointment+patient+clinic IDs and redirects.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B10: `POST /p/reschedule/{token}/commit` from the BFF

**Files:**
- Modify: `api/public/reschedule.py`
- Modify: `tests/api/test_reschedule_link.py`

- [ ] **Step 1: Failing tests**

Add to `tests/api/test_reschedule_link.py`:

```python
def test_post_commit_marks_token_used_and_swaps_appointment(client, db_session, mm_clinic, monkeypatch):
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "INTSECRET")
    old_appt = _seed_scheduled_appointment(db_session, mm_clinic)
    _seed_reminder_with_token(db_session, appointment_id=old_appt.id, token="tok_commit_ok")
    # Pre-existing hold belonging to the same patient + clinic (created
    # by market-mall via /api/public/holds with the InternalSecret).
    hold_id = _seed_hold(db_session, clinic_id=mm_clinic.id, patient_id=old_appt.patient_id, hours_out=72)

    resp = client.post(
        "/p/reschedule/tok_commit_ok/commit",
        json={"hold_id": hold_id},
        headers={"X-Internal-Secret": "INTSECRET"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "appointment_id" in body
    db_session.refresh(old_appt)
    assert old_appt.status == "RESCHEDULED"


def test_post_commit_returns_410_on_used_token(client, db_session, mm_clinic, monkeypatch):
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "INTSECRET")
    appt = _seed_scheduled_appointment(db_session, mm_clinic)
    _seed_reminder_with_token(
        db_session, appointment_id=appt.id, token="tok_used2",
        used_at=datetime.now(timezone.utc),
    )
    resp = client.post(
        "/p/reschedule/tok_used2/commit",
        json={"hold_id": "anything"},
        headers={"X-Internal-Secret": "INTSECRET"},
    )
    assert resp.status_code == 410
```

- [ ] **Step 2: Run, expect failures**

Run: `pytest tests/api/test_reschedule_link.py -v -k post_commit`
Expected: FAIL.

- [ ] **Step 3: Implement `POST /p/reschedule/{token}/commit`**

```python
# Append to api/public/reschedule.py
from pydantic import BaseModel
from api.dependencies.auth import require_internal_secret
from database.models import Hold  # or wherever holds live (see feat/holds-foundation)


class CommitRequest(BaseModel):
    hold_id: str


@router.post("/reschedule/{token}/commit", dependencies=[Depends(require_internal_secret)])
def post_commit(token: str, body: CommitRequest, db: Session = Depends(get_db)):
    reminder = (
        db.query(AppointmentReminder)
        .filter_by(reschedule_token=token)
        .first()
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="token not found")
    now = datetime.now(timezone.utc)
    if reminder.reschedule_token_used_at is not None or (
        reminder.reschedule_token_expires_at and reminder.reschedule_token_expires_at <= now
    ):
        raise HTTPException(status_code=410, detail="token expired or used")

    old_appt = reminder.appointment
    hold = db.query(Hold).filter_by(id=body.hold_id).first()
    if hold is None or hold.patient_id != old_appt.patient_id or hold.clinic_id != old_appt.clinic_id:
        raise HTTPException(status_code=409, detail="hold mismatch")
    if hold.expires_at and hold.expires_at <= now:
        raise HTTPException(status_code=409, detail="hold expired")

    # Atomically: mark old appointment RESCHEDULED, create new from hold,
    # consume hold, mark token used.
    new_appt = _create_appointment_from_hold(db, hold, predecessor_id=old_appt.id)
    old_appt.status = "RESCHEDULED"
    hold.consumed_at = now
    reminder.reschedule_token_used_at = now
    db.commit()

    return {"appointment_id": new_appt.id, "start_time": new_appt.start_time.isoformat()}


def _create_appointment_from_hold(db, hold, *, predecessor_id):
    """Mint a new SCHEDULED appointment from the hold's slot.

    Reuses the existing appointment-creation helper that
    `api/v1/public_holds/router.py` uses when an inbound web hold gets
    accepted. Subagent should grep `public_holds/router.py` for the
    function it calls inside `POST /api/public/holds` (around lines
    100-120) and reuse the same helper, passing through the hold's
    patient/provider/clinic/start_time/end_time, with status=SCHEDULED
    and a metadata field `predecessor_appointment_id=predecessor_id`
    so the audit trail links new ↔ old.
    """
    raise NotImplementedError("see docstring — wire to existing helper from public_holds")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/api/test_reschedule_link.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add api/public/reschedule.py tests/api/test_reschedule_link.py
git commit -m "feat(reschedule): POST /p/reschedule/{token}/commit consumes hold + swaps appointment

Validates token + hold ownership, atomically marks old appointment
RESCHEDULED, mints new from hold, consumes hold, flips token used.
Internal-secret auth (called by market-mall BFF).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B11: End-to-end integration test — YES flow

**Files:**
- Create: `tests/integration/test_sms_reminder_e2e.py`

- [ ] **Step 1: Write the e2e test**

```python
# tests/integration/test_sms_reminder_e2e.py
"""End-to-end: schedule → SMS sent → patient replies YES → CONFIRMED + ack."""

import base64
import json
import time
from datetime import datetime, timezone
from unittest.mock import patch
import nacl.signing


def test_yes_flow_end_to_end(client, db_session, mm_clinic, monkeypatch):
    # Setup
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode())
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "INT")

    appt = _seed_scheduled_appointment(db_session, mm_clinic, hours_out=24.0, phone="+14035550001")

    # Scan → SMS sent
    with patch("clients.telnyx_messaging.send_message", side_effect=["msg_out_1", "msg_ack_1"]):
        scan_resp = client.post("/cron/reminders/scan", headers={"X-Internal-Secret": "INT"})
    assert scan_resp.status_code == 200
    assert scan_resp.json()["sent_count"] == 1

    # Patient replies YES
    body = json.dumps({"data": {"event_type": "message.received", "payload": {
        "from": {"phone_number": "+14035550001"},
        "to": [{"phone_number": "+14035550000"}],
        "text": "yes", "id": "msg_in_1",
    }}}).encode()
    ts = str(int(time.time()))
    sig = base64.b64encode(signing_key.sign(ts.encode() + b"|" + body).signature).decode()
    with patch("clients.telnyx_messaging.send_message", return_value="msg_ack_1"):
        webhook_resp = client.post("/webhooks/telnyx/sms-inbound", content=body, headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        })
    assert webhook_resp.status_code == 200
    db_session.refresh(appt)
    assert appt.status == "CONFIRMED"


def test_reschedule_flow_redirects_via_token(client, db_session, mm_clinic, monkeypatch):
    signing_key = nacl.signing.SigningKey.generate()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", base64.b64encode(bytes(signing_key.verify_key)).decode())
    monkeypatch.setenv("SMS_PROVIDER", "telnyx")
    monkeypatch.setenv("REMINDER_OFFSET_HOURS", "24")
    monkeypatch.setenv("DENTAL_API_INTERNAL_SECRET", "INT")
    monkeypatch.setenv("MARKET_MALL_WEBSITE_BASE_URL", "https://marketmall.example.com")
    monkeypatch.setenv("RESCHEDULE_SESSION_SIGNING_KEY", base64.b64encode(b"\x00" * 32).decode())

    appt = _seed_scheduled_appointment(db_session, mm_clinic, hours_out=24.0, phone="+14035550001")

    with patch("clients.telnyx_messaging.send_message", side_effect=["msg_out", "msg_ack"]):
        client.post("/cron/reminders/scan", headers={"X-Internal-Secret": "INT"})

    body = json.dumps({"data": {"event_type": "message.received", "payload": {
        "from": {"phone_number": "+14035550001"},
        "to": [{"phone_number": "+14035550000"}],
        "text": "reschedule", "id": "msg_in_2",
    }}}).encode()
    ts = str(int(time.time()))
    sig = base64.b64encode(signing_key.sign(ts.encode() + b"|" + body).signature).decode()
    with patch("clients.telnyx_messaging.send_message", return_value="msg_ack"):
        client.post("/webhooks/telnyx/sms-inbound", content=body, headers={
            "Content-Type": "application/json",
            "Telnyx-Signature-ED25519": sig,
            "Telnyx-Timestamp": ts,
        })

    # Read the token from the persisted reminder row
    from database.ops.models import AppointmentReminder
    reminder = db_session.query(AppointmentReminder).filter_by(appointment_id=appt.id).first()

    resp = client.get(f"/p/reschedule/{reminder.reschedule_token}", follow_redirects=False)
    assert resp.status_code == 302
    assert "marketmall.example.com/reschedule?session=" in resp.headers["location"]
```

- [ ] **Step 2: Run**

Run: `pytest tests/integration/test_sms_reminder_e2e.py -v`
Expected: 2 PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_sms_reminder_e2e.py
git commit -m "test(integration): end-to-end YES + RESCHEDULE flows

YES path: scan → SMS sent → webhook reply → CONFIRMED + ack.
RESCHEDULE path: scan → SMS sent → reply → 302 to market-mall with
signed session blob.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B12: Terraform — Cloud Scheduler job

**Files:**
- Create: `infra/terraform/sms_reminder_scheduler.tf` (or extend an existing TF module if one exists)
- Create: `infra/terraform/README.md` (or extend) noting the pre-apply requirements

- [ ] **Step 1: Write Terraform**

```hcl
# infra/terraform/sms_reminder_scheduler.tf
resource "google_cloud_scheduler_job" "sms_reminder_scan" {
  name        = "sms-reminder-scan-every-5min"
  description = "Triggers dental-api scan for due appointment reminders."
  schedule    = "*/5 * * * *"
  time_zone   = "America/Edmonton"

  http_target {
    http_method = "POST"
    uri         = "${var.dental_api_url}/cron/reminders/scan"

    headers = {
      "X-Internal-Secret" = var.dental_api_internal_secret
      "Content-Type"      = "application/json"
    }

    oidc_token {
      service_account_email = var.cloud_run_invoker_sa_email
      audience              = var.dental_api_url
    }

    body = base64encode("{}")
  }

  retry_config {
    retry_count          = 3
    max_retry_duration   = "300s"
    min_backoff_duration = "30s"
    max_backoff_duration = "120s"
  }
}
```

(Variables `dental_api_url`, `dental_api_internal_secret`, `cloud_run_invoker_sa_email` are inherited from the existing dental-api Terraform module.)

- [ ] **Step 2: Commit (no test — this is infra)**

```bash
git add infra/terraform/sms_reminder_scheduler.tf
git commit -m "infra(scheduler): Cloud Scheduler job for /cron/reminders/scan every 5 min

OIDC-authed POST against dental-api. Three retries on 5xx with
exponential backoff. America/Edmonton timezone.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task B13: Final integration suite + cleanup

**Files:**
- Run the full repo test suite.

- [ ] **Step 1: Run everything**

Run: `pytest -q --tb=short 2>&1 | tail -50`
Expected: All new tests pass. No regression on pre-existing tests.

- [ ] **Step 2: Diff summary**

Run: `git log --oneline ^feat/holds-foundation HEAD && git diff feat/holds-foundation..HEAD --stat`

- [ ] **Step 3: Fill in Completion section of this plan**

Append to "## Completion" below: total commit count, total test count delta, anything surprising during execution.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-06-09-sms-reminder-telnyx.md
git commit -m "docs(plan): completion record for SMS reminder + Telnyx migration

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Completion

(Filled in by the executing agent after Task B13.)

---

## Out-of-band manual verification (post-merge, pre-deploy)

These gate the production cutover but are not part of the implementation plan:

1. Telnyx Messaging Profile + provisioned number in place.
2. All `TELNYX_*` env vars in Secret Manager + injected into Cloud Run.
3. Cloud Scheduler job applied via Terraform.
4. `MARKET_MALL_WEBSITE_BASE_URL` set; `/reschedule` route alive on market-mall.
5. `SMS_PROVIDER=twilio` at deploy; flip to `telnyx` after one round-trip verification.
6. Live SMS test: book real appointment 25h out → wait for scan window → SMS lands → reply YES → status flips CONFIRMED → ack SMS lands.

Deploy posture per the deploy-gate constraint: requires explicit "deploy now" each time. One approval does not carry forward.
