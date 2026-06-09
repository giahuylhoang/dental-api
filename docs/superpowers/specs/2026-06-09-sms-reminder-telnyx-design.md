# SMS Appointment Reminder (Telnyx) — Design Spec

**Date:** 2026-06-09
**Author:** Brainstormed with user 2026-06-09
**Status:** Draft — awaiting user review

**Base branch:** `feat/holds-foundation` (the holds work is required dependency; the SMS reminder leans on `/api/public/slots`, `/api/public/holds`, and `DENTAL_API_INTERNAL_SECRET`).

## Goal

Send a one-shot SMS reminder to each patient about 24 hours before their scheduled appointment (env-configurable; expected to be tuned between 24h and 48h per clinic preference). The reminder asks for a simple reply (`YES` / `NO` / `RESCHEDULE`) that the system parses and acts on automatically — updating appointment status, sending an acknowledgement, and surfacing a self-service reschedule link that's consumed by `market-mall-website`.

The 24h+ window gives patients enough time to actually call or reschedule before the appointment — a 5h window is too tight for working patients to act on.

All SMS (this new reminder + the existing booking, cancellation, reschedule notifications) migrate from Twilio to **Telnyx** in this spec, behind a unified `services/sms.py` interface and gated by a `SMS_PROVIDER` env flag for safe rollback.

## Non-goals (explicit)

- Outbound voice calls. Reserved for **phase 2**, which will branch off `dental-agent`'s `v3-realtime-model`.
- A patient-facing reschedule web page. Handled separately by `market-mall-website`.
- Multi-reminder cadence (72h + 24h + day-of). Single reminder only in MVP.
- Per-clinic / per-appointment-type configurable timing. Global env-var offset.
- SMS opt-out management. Document as a known gap; do not block MVP.
- A new Cloud Run service or new GCP project. Must reuse existing `dental-api-v2`.

## Architecture

Five components. All but #1 live in `dental-api-v2`.

| # | Component | Path | Cost |
| --- | --- | --- | --- |
| 1 | Cloud Scheduler job `sms-reminder-scan-every-5min` | GCP (Terraform) | ~$0.10/mo |
| 2 | `POST /cron/reminders/scan` endpoint | `dental-api/api/cron/reminders.py` (new) | $0 |
| 3 | `POST /webhooks/telnyx/sms-inbound` endpoint | `dental-api/api/webhooks/telnyx.py` (new) | $0 |
| 4 | Reply parser (regex → LLM fallback) | `dental-api/services/reply_parser.py` (new) | ~$0.10/mo at MVP volume |
| 5 | Reschedule-link handoff endpoints (`GET /p/reschedule/{token}`) | `dental-api/api/public/reschedule.py` (new) | $0 |

Telnyx migration adds two more pieces of plumbing, used by everything above plus the existing booking/cancel/reschedule notifications:

| Path | Responsibility |
| --- | --- |
| `dental-api/clients/telnyx_messaging.py` (new) | Telnyx Messaging v2 API client (send, webhook signature verify) |
| `dental-api/services/sms.py` (new) | Provider-agnostic facade. `send_sms(to, body, *, context)` dispatches to `clients.telnyx_messaging` or legacy `clients.sms_client` (Twilio) based on `SMS_PROVIDER` env. |

## Reminder timing — the rule

```python
target_send_time = appointment.start_time - timedelta(hours=REMINDER_OFFSET_HOURS)  # default 24, expected 24-48

# Quiet-hours deferment (per clinic timezone)
quiet_start = time(QUIET_HOURS_START)  # default 21:00
quiet_end   = time(QUIET_HOURS_END)    # default 08:00

if target_send_time falls in quiet hours (clinic-local):
    target_send_time = next 08:00 in clinic-local TZ

# Skip if too late to be useful
if target_send_time >= appointment.start_time - timedelta(minutes=MIN_LEAD_MINUTES):  # default 30
    mark AppointmentReminder.status = "skipped_too_late"; SKIP
else:
    SEND
```

Env vars: `REMINDER_OFFSET_HOURS`, `QUIET_HOURS_START`, `QUIET_HOURS_END`, `MIN_LEAD_MINUTES`. All global for MVP.

## Data model changes

Existing `AppointmentReminder` table gets columns added (Alembic migration):

| Column | Type | Notes |
| --- | --- | --- |
| `provider` | enum(`telnyx`, `twilio`) | Defaults `telnyx` for new rows. Lets old Twilio rows coexist during cutover. |
| `outbound_message_id` | str (nullable) | Telnyx message ID (or Twilio SID for legacy rows). Used to correlate inbound reply. |
| `reply_received_at` | timestamp (nullable) | Set when webhook fires for a reminder on this `to` number. |
| `reply_parsed_intent` | enum(`confirmed`, `cancelled`, `reschedule_requested`, `ambiguous`) | nullable until reply arrives |
| `reply_raw_text` | text (nullable) | Verbatim caller text for audit + LLM-fallback retraining |
| `reschedule_token` | UUID (nullable) | Populated when the SMS body contains the link; null when offset is `>24h` and the link isn't useful yet (we always populate in MVP) |
| `reschedule_token_used_at` | timestamp (nullable) | Single-use; flips dead on commit |
| `reschedule_token_expires_at` | timestamp | Default `appointment.start_time + 48h` |
| `ambiguous_reply_count` | int (default 0) | Increments each time we receive an `ambiguous`-classified reply for this reminder. Used to gate the second disambiguation prompt. |

Index: `UNIQUE(appointment_id, channel)` (already exists) prevents double-queue under overlapping scheduler runs. Add: `INDEX(reschedule_token)` for `/p/reschedule/{token}` lookups.

**Status writeback:** existing `PUT /api/appointments/{id}/{cancel,reschedule}` payloads get an optional `source` field:

```
enum AppointmentMutationSource {
    outbound_sms_reply,
    self_service_link,
    inbound_call,        # default for back-compat
    clinic_staff,
    system,
}
```

The dashboard (a future iteration) uses this to distinguish patient-driven changes from staff-driven ones.

## SMS templates

Templates are stored in `dental-api/templates/sms/` as `<intent>.<lang>.txt` with `{placeholder}` slots. **MVP sends English only.** Template files for `pa`, `hi`, `ar` are written in this spec so the infrastructure is ready, but the selector is hard-coded to `en` until a follow-up iteration wires up patient-locale lookup (Emma's voice multilingual work will eventually populate that).

**Reminder (outbound):**
> Hi {first_name}, this is {clinic_name}. Reminder: your appointment is {when_human} with {provider_first_name}. Reply **YES** to confirm, **NO** to cancel, or **RESCHEDULE** for options. To pick a new time yourself: {reschedule_link}

**Ack on YES:**
> Thanks! We'll see you at {when_human}. Reply CANCEL if anything changes.

**Ack on NO:**
> Got it — your appointment is cancelled. To book again, call {clinic_phone} or visit {reschedule_link}.

**Ack on RESCHEDULE:**
> Sure thing. Pick a new time here: {reschedule_link} — or call {clinic_phone} to talk to Emma.

**Ack on AMBIGUOUS (sent once per reminder; further freeform replies escalate to clinic dashboard, no auto-reply):**
> Sorry, I didn't catch that. Reply **YES** to confirm, **NO** to cancel, or **RESCHEDULE** for options.

Non-English variants are word-for-word translations of the above. Numbers, names, and the reschedule link must be preserved verbatim across translations — same rule as Emma's voice multilingual directive.

## Reply parsing flow

```
SMS arrives at /webhooks/telnyx/sms-inbound
  ↓
verify Telnyx-Signature-ED25519 header against TELNYX_PUBLIC_KEY  →  reject if mismatch
  ↓
extract from/to/text from Telnyx payload
  ↓
look up AppointmentReminder by to=<our_number> AND from_phone=<patient>
  AND reply_received_at IS NULL
  AND outbound_message_sent_at > now - 7 days
  ↓ found                              ↓ not found
  parse → classify intent              forward payload to chat_api SMS path
  ↓                                    (existing patient SMS thread handling
  apply action + record               in /api/v2/communications)
```

**Parser:**
1. Normalize text: lowercase, strip whitespace, strip emoji.
2. Try regex matrix:
   - `confirmed`: `^(y|yes|yeah|yep|ok|okay|confirm|👍)$`, `^(haan|ji|haa)$` (pa/hi Latin), `^(naam|aiwa)$` (ar Latin)
   - `cancelled`: `^(n|no|nope|cancel|nah)$`, `^(nahi|nahin|nai)$` (pa/hi Latin), `^(la|laa)$` (ar Latin)
   - `reschedule_requested`: `\b(reschedule|move|change|switch|different|another)\b`
3. If no regex match → LLM intent classification (Gemini 3.1 Flash, ~$0.0001/call):
   - Prompt: "Classify this SMS reply to an appointment confirmation as one of: CONFIRMED, CANCELLED, RESCHEDULE_REQUESTED, AMBIGUOUS. Reply: {text}"
   - Response parsed; falls back to AMBIGUOUS on parse error.

**Action by intent:**
- `confirmed` → `PUT /api/appointments/{id}/status` with `status=CONFIRMED, source=outbound_sms_reply` + send ack-YES SMS
- `cancelled` → `PUT /api/appointments/{id}/cancel` with `source=outbound_sms_reply` + send ack-NO SMS
- `reschedule_requested` → keep `SCHEDULED` (still on books until they actually pick a new slot) + send ack-RESCHEDULE SMS with link. The "needs reschedule" state is **derived**, not a new column — `AppointmentReminder.reply_parsed_intent='reschedule_requested'` is the source of truth; the eventual dashboard query is `SELECT a.* FROM appointments a JOIN appointment_reminders r ON r.appointment_id=a.id WHERE r.reply_parsed_intent='reschedule_requested' AND r.reschedule_token_used_at IS NULL AND a.status='SCHEDULED'`.
- `ambiguous` → if first ambiguous reply for this reminder: send disambiguation prompt and **increment** an `AppointmentReminder.ambiguous_reply_count` column (default 0). If `ambiguous_reply_count >= 2`: do not auto-reply; the "needs human review" state is again derived (`reply_parsed_intent='ambiguous' AND ambiguous_reply_count >= 2`). No new appointment column.

## Telnyx migration plan

**Phase A: build the unified facade alongside Twilio (no behavior change yet)**

1. New `clients/telnyx_messaging.py` with `send(to, body, *, messaging_profile_id, webhook_url) -> message_id` and `verify_webhook_signature(body, signature, timestamp) -> bool`.
2. New `services/sms.py` exporting `send_sms(to, body, *, context: SmsContext) -> SendResult`. Switches on `SMS_PROVIDER` env (default `twilio` until cutover).
3. Refactor `services/notifications.py` callers (booking confirmation, cancellation, reschedule confirmation) to use `services/sms.py` instead of importing Twilio directly.
4. Tests stay green (still on Twilio path).

**Phase B: cutover**

5. Telnyx number + Messaging Profile provisioned (operational pre-deploy gate).
6. `TELNYX_API_KEY`, `TELNYX_MESSAGING_PROFILE_ID`, `TELNYX_SMS_FROM_NUMBER`, `TELNYX_PUBLIC_KEY` added to Secret Manager + Cloud Run env.
7. Flip `SMS_PROVIDER=telnyx` in prod env.
8. Monitor for 1 week. Rollback = flip env var back to `twilio`.

**Phase C: cleanup (separate follow-up PR, NOT this spec)**

9. Delete Twilio client + remove `SMS_PROVIDER` flag.

## Reschedule-link contract (handoff to `market-mall-website`)

The link in the reminder SMS points at `https://api.example.com/p/reschedule/{token}` on `dental-api-v2`. This dental-api endpoint is the **identity-validation hop**; the actual slot picker UI lives in `market-mall-website` and reuses the holds-foundation public endpoints.

**`GET /p/reschedule/{token}`** (public, no Firebase Auth)
- 200 → redirect (HTTP 302) to `${MARKET_MALL_WEBSITE_BASE_URL}/reschedule?session={signed_session_blob}` where `signed_session_blob` carries:
  - `appointment_id`
  - `patient_id`
  - `clinic_id`
  - `internal_secret_hash` (so the BFF can call `/api/public/slots` and `/api/public/holds` on behalf of the patient using `DENTAL_API_INTERNAL_SECRET`)
  - 30-minute TTL on the signed session
- 410 → token expired, used, or appointment status no longer mutable. Render a small HTML page explaining to call the clinic.

**`POST /p/reschedule/{token}/commit`** (called by `market-mall-website` BFF after patient picks a slot via `/api/public/holds`)
- Body: `{hold_id: str}`
- Validates: token still valid, hold belongs to the same patient + clinic, hold not expired.
- Atomically: marks old appointment `RESCHEDULED`, creates new from the hold, marks token `used_at`, marks hold consumed.
- 200 → returns new appointment shape.
- 410 → token already used / expired.
- 409 → hold expired / does not match.

market-mall-website's role:
1. Receives the redirect with `signed_session_blob`.
2. Renders slot picker by calling `GET /api/public/slots?clinic_id=...&start=...&end=...` with the `Internal-Secret` header reconstituted from the session blob.
3. On user selection, calls `POST /api/public/holds` to reserve.
4. Calls `POST /p/reschedule/{token}/commit` to commit. Releases the hold on cancel/timeout.

This way the SMS reminder spec doesn't duplicate slot-picker logic — it composes on the holds-foundation primitives.

## Webhook security

- **Inbound webhook signature**: `POST /webhooks/telnyx/sms-inbound` must verify `Telnyx-Signature-ED25519` and `Telnyx-Timestamp` headers using `TELNYX_PUBLIC_KEY`. Reject on mismatch or timestamp drift >5 minutes.
- **Cron endpoint auth**: `POST /cron/reminders/scan` accepts requests only when the `X-CloudScheduler-JobName` header matches the configured job AND the `Authorization` header carries an OIDC token for the dental-api service account (standard Cloud Scheduler → Cloud Run pattern).
- **Reschedule token signing**: token is a UUIDv4 stored in DB (not signed JWT). Lookup-based revocation via `reschedule_token_used_at`. The signed_session_blob handed off to market-mall-website is signed (Ed25519, dental-api private key) so the BFF can trust it.

## Pre-deploy gates (operational)

These are NOT code; they block the production cutover but do not block the spec, plan, or local implementation:

1. Telnyx Messaging Profile created.
2. Telnyx number(s) provisioned and added to the profile.
3. `TELNYX_API_KEY`, `TELNYX_PUBLIC_KEY`, `TELNYX_MESSAGING_PROFILE_ID`, `TELNYX_SMS_FROM_NUMBER` in Secret Manager + injected into Cloud Run.
4. Cloud Scheduler job created via Terraform: target = `dental-api-v2` URL, OIDC auth, cadence `*/5 * * * *`.
5. `MARKET_MALL_WEBSITE_BASE_URL` set; the `/reschedule` route exists on market-mall-website (separate team).
6. SMS_PROVIDER stays `twilio` until cutover; flip atomically as one env update.

## Test surface

**Unit:**
- `services/reply_parser.py` — full regex matrix in 4 languages, LLM fallback with mocked client.
- `services/sms.py` — both provider paths via mocked client, env-flag switching.
- `clients/telnyx_messaging.py` — request building, signature verification (positive + tampered + replay-window violation).
- `api/cron/reminders.py` — quiet-hours deferment, MIN_LEAD_MINUTES skip, status-guard before send, UNIQUE-constraint dedup.

**Integration:**
- End-to-end: create appointment 24.5h from now (or `REMINDER_OFFSET_HOURS + 0.5h` to keep the test offset-agnostic) → call scan endpoint → mock Telnyx send → simulate Telnyx webhook with `YES` → appointment status flips CONFIRMED, ack SMS attempted.
- Same but with `RESCHEDULE` → status stays SCHEDULED, `needs_reschedule` flag set, ack SMS attempted.

**Manual (dev stack):**
- Local dental-api with a stubbed Telnyx client logging to stdout. Trigger scan via curl. Inspect log. Simulate webhook via curl. Verify DB state.

## Phasing within this spec

Two sub-tasks; both ship in the same branch but as separate commits to allow incremental review:

1. **Phase A (Telnyx migration)**: unified facade + provider flag, all existing SMS callers refactored. No new behavior. Verifiable independently.
2. **Phase B (reminder + reply + reschedule link)**: scan endpoint, webhook endpoint, parser, reschedule-link handoff. Depends on Phase A.

Either phase can be merged to `feat/holds-foundation` independently if the other isn't ready.

## Risks

| Risk | Mitigation |
| --- | --- |
| Telnyx send rejected because number isn't messaging-enabled at deploy. | Pre-deploy gate #1–3 above; cannot flip `SMS_PROVIDER=telnyx` until verified by a dev SMS round-trip. |
| Reply webhook collides with the existing chat_api SMS thread path (same `To` number). | Routing rule: if no unreplied `AppointmentReminder` exists for the `From` within 7 days, forward payload to chat_api. Document explicitly. |
| Phone consent — patient never opted in to reminders. | MVP assumes implicit consent for patients with `phone` on file. Add `sms_opt_out` field as a follow-up; document gap in spec. |
| Race: clinic staff cancels appointment between queue and send. | Scan endpoint re-checks status under row lock immediately before send. |
| Token leak via shared SMS history. | Short TTL (48h after appointment), single-use, scoped to one appointment + clinic. Acceptable for this use case. |
| LLM fallback drift over time. | Persist `reply_raw_text` for every reply; periodic review of `ambiguous` clusters to extend the regex matrix. |
| Cloud Scheduler hits dental-api at scale-to-zero cold start. | Scheduler retries on 5xx; cold-start cost is ~2s, well within scan endpoint timeout (30s). |

## Out of scope (for separate later specs)

- **Phase 2: outbound voice agent** — calls patients who didn't reply to SMS. Branches off `dental-agent`'s `v3-realtime-model`, reuses inbound v3 prompt + tools, adds an outbound-only entrypoint and Telnyx outbound SIP trunk. Will reference this spec as upstream.
- Multi-reminder cadence (72h + 24h + day-of).
- Per-clinic / per-appointment-type configurable timing.
- SMS opt-out management.
- Patient locale preference inference (Emma's multilingual voice work hints at it; SMS picks it up later).
- Dashboard for clinic-staff review of `needs_human_review` flagged appointments.

## Deploy posture

Local-commit-only at first. No push to origin, no Cloud Run deploy. Production cutover requires:

1. Phase A + Phase B unit + integration tests green.
2. Operational pre-deploy gates 1–6 above all satisfied.
3. Explicit "deploy now" from the user per the deploy-gate constraint.
4. `SMS_PROVIDER` flipped from `twilio` to `telnyx` only after verification of a Telnyx-stack SMS round-trip in production.

Approval for one deploy does not carry to subsequent deploys.
