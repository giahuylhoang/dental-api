# Telnyx SMS — Handoff to chat_api agent

**Date:** 2026-06-09
**From:** SMS reminder + Telnyx migration spec (this branch: `feat/sms-reminder-telnyx` off `feat/holds-foundation`)
**To:** Whoever is building omnichannel chat_api SMS integration

## TL;DR

Telnyx is set up and **verified working end-to-end with production Telnyx infrastructure**. There's a working API key, a Messaging Profile, an SMS-capable number assigned to it, signature verification, and a code path for *reminder replies*. You need to add the **fallthrough path for general SMS conversations** (chat_api/Emma-on-SMS).

## What's already done in the Telnyx portal

- **Account**: existing dental-system Telnyx account (same one used for SIP voice).
- **Messaging Profile**: `dental-sms-prod`, ID `40019eae-7894-48f7-88b5-911cda4ba3ef`.
- **Ed25519 webhook public key**: `NYPuZy/LGS4+d2WZnp8mNkiPlsiDNyRtaLrwWuxc2iI=` (set on the profile).
- **API key**: stored as `TELNYX_API_KEY` in `dental-api/.claude/worktrees/sms-reminder-telnyx/.env.local`. Single key works for all numbers in the account.
- **First SMS number**: `+15874023579` — Emma's existing voice number, now also SMS-enabled, assigned to the profile. One number for voice AND SMS per clinic.
- **Webhook URL** on the profile: currently a placeholder. Was temporarily pointed at an ngrok tunnel during testing — that tunnel is now dead. **You need to set this** to whatever URL your local dev exposes (ngrok or similar) or the prod Cloud Run URL when ready.

### Telnyx Messaging Profile inbound settings — recommended

| Setting | Value |
| --- | --- |
| Webhook URL | `https://<your-host>/webhooks/telnyx/sms-inbound` |
| Webhook Failover URL | blank |
| Webhook API Version | v2 |
| Number Pool | OFF |
| Restrict to mobile numbers | ON |
| MMS fallback / transcoding | OFF |
| Daily spend limit | ON, $20/day |
| Smart Encoding | ON |
| Keywords (STOP/START/HELP) | defaults — handled by Telnyx, never reach your webhook |

## What's in the codebase you can reuse

All under `dental-api/.claude/worktrees/sms-reminder-telnyx/`:

### `clients/telnyx_messaging.py`
- `send_message(*, to, body, from_=None) -> str | None` — fires Telnyx Messaging v2 send. Returns Telnyx message ID. `from_` defaults to `TELNYX_SMS_FROM_NUMBER` env when omitted.
- `verify_webhook_signature(payload, signature_b64, timestamp) -> bool` — Ed25519 verify against `TELNYX_PUBLIC_KEY`. Use this on EVERY inbound webhook before parsing.

### `services/sms.py`
- `send_sms_raw(*, to, body, from_=None) -> str | None` — provider-agnostic facade. Dispatches to Telnyx or Twilio per `SMS_PROVIDER` env. Use THIS, not the Telnyx client directly, so the same flag switches you between providers cleanly.

### `services/sms_templates.py`
- `render(intent, lang, **vars) -> str` — loads `templates/sms/<intent>.<lang>.txt`. Currently 5 intents (`reminder`, `ack_confirmed`, `ack_cancelled`, `ack_reschedule`, `ack_ambiguous`). MVP is English-only.

### `services/reply_parser.py`
- `parse(text) -> tuple[ReplyIntent, str]` — hybrid regex + optional LLM fallback. Returns `(intent, source)`. Stage 2 LLM is gated on `SMS_REPLY_LLM_FALLBACK=true` env.

### `api/webhooks/telnyx.py` — `POST /webhooks/telnyx/sms-inbound`
The webhook already does:
1. Verifies signature → 401 on bad.
2. Filters event types (only `message.received` is processed).
3. Looks up an `AppointmentReminder` matching `Patient.phone == from_phone` AND `Clinic.sms_from_number == to_phone`, last 7 days, no prior reply.
4. **If match**: parses reply → dispatches (CONFIRMED/CANCELLED/RESCHEDULE/AMBIGUOUS) → updates appointment → sends ack SMS.
5. **If no match**: returns `{"routed_to": "fallthrough"}` and does nothing else.

### Schema additions you can lean on
- `Clinic.sms_from_number` (nullable String) — each clinic's E.164 SMS sender.
- `AppointmentReminder` got 9 new columns: `provider`, `outbound_message_id`, `reply_received_at`, `reply_parsed_intent`, `reply_raw_text`, `reschedule_token`, `reschedule_token_used_at`, `reschedule_token_expires_at`, `ambiguous_reply_count`.
- Alembic migrations: `ca70e6da68cd` (reminder columns), `493cc648b838` (Clinic.sms_from_number).

## What's NOT done — your scope

The `fallthrough` branch in `api/webhooks/telnyx.py` is the seam for chat_api integration. Today it just returns `{"routed_to": "fallthrough"}` and exits. You should:

1. **Decide how chat_api consumes the SMS payload.** Options:
   - Forward the payload synchronously to a chat_api endpoint (HTTP POST from this webhook).
   - Insert a row into an `omnichannel_sessions` / `omnichannel_messages` table; chat_api polls or subscribes.
   - Publish to a queue (Pub/Sub / Cloud Tasks).
2. **Map `to.phone_number` to a clinic** using the same `Clinic.sms_from_number` column — so chat_api knows which clinic Emma is replying for.
3. **Map `from.phone_number` to a patient** — same `Patient.phone` lookup as the reminder webhook. If no patient: anonymous chat (Emma collects identity, just like inbound voice).
4. **Use `services/sms.send_sms_raw(to=..., body=..., from_=clinic.sms_from_number)`** for outbound chat replies. Don't reach into `clients/telnyx_messaging` directly — the dispatcher gives you provider switching + per-clinic FROM threading for free.

### Important contract: per-clinic FROM numbers

Each clinic has its own `Clinic.sms_from_number`. When chat_api sends a reply on behalf of a clinic:
- It MUST pass `from_=clinic.sms_from_number` to `send_sms_raw`.
- Otherwise it falls back to the global `TELNYX_SMS_FROM_NUMBER` env, which is fine for dev but wrong in multi-clinic prod.

### Don't duplicate webhook signing logic

If chat_api ever needs its own webhook endpoint (e.g. for a different event type), import `verify_webhook_signature` from `clients/telnyx_messaging.py`. Don't reimplement Ed25519 verify.

## Local dev recipe (worked tonight)

1. `cd dental-api/.claude/worktrees/sms-reminder-telnyx`
2. `.env.local` has all 4 Telnyx vars (copy to your worktree's env).
3. `/Users/giahuyhoangle/Projects/dental-system/dental-api/.venv/bin/python -c "from dotenv import load_dotenv; load_dotenv('.env.local'); import os, uvicorn; os.environ['DATABASE_URL']='sqlite:///./dental_clinic.db'; uvicorn.run('api.main:app', host='127.0.0.1', port=8002)"` (or your own startup script).
4. `ngrok http 8002` → copy the public URL.
5. Telnyx portal → Messaging Profile → Inbound webhook URL → paste `<ngrok-url>/webhooks/telnyx/sms-inbound` (or whatever your endpoint is for chat_api).
6. Save. Send a test SMS to `+15874023579` from your phone. Watch logs.

## Open items I owe but haven't done

- Multi-language SMS templates (pa/hi/ar) — infrastructure exists (`services/sms_templates.py` falls back to English), but the non-English files aren't written yet. Same scope as the Emma voice multilingual work that just shipped.
- Patient locale preference inference (so `render(intent, lang=...)` knows which lang to use).
- Booking confirmation / cancellation SMS still go via Twilio (their high-level wrappers in `clients/sms_client.py` don't pass `from_` to `services/sms`). The TRANSPORT routes through `services/sms.send_sms_raw` → `_send_via_twilio`, so flipping `SMS_PROVIDER=telnyx` sends them via Telnyx using the global env FROM number. Per-clinic threading for those legacy SMS callers is a separate follow-up — not in this spec.
- The legacy `_send_via_twilio` fallback path on `clients/sms_client.py` is still present; it'll get deleted in a post-cutover cleanup spec (probably 1 week after prod flip).

## Quick sanity test (already passed)

End-to-end with real Telnyx:
- Outbound send from +15874023579 to a personal phone — landed.
- Inbound reply "YES" → webhook fired with valid Ed25519 signature → reminder lookup matched → parser classified `confirmed` → appointment status flipped `SCHEDULED` → `CONFIRMED` → ack SMS sent via Telnyx → patient received "Thanks! We'll see you at Wed Jun 10 at 5:48 PM."

If you can get the same round-trip working for chat_api's fallthrough branch, you're done.

## Contact

Open a thread in the sibling chat session that worked on this branch if anything's unclear. The full spec is `docs/superpowers/specs/2026-06-09-sms-reminder-telnyx-design.md`; the plan is `docs/superpowers/plans/2026-06-09-sms-reminder-telnyx.md`.
