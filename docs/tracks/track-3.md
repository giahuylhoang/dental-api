# Track 3 — Backend ops: Scheduling, Billing, Insurance, Communications, CRM

You are a coding agent working on **one of five parallel tracks** that together extend the dental-api repo into a PMS/CRM for denturist clinics. Read `~/.claude/plans/now-i-want-to-fizzy-valley.md` for full context. Don't read or modify other tracks' files.

## Mission

Add operations: enhanced scheduling (multi-resource, recurring, reminders, waitlist), billing (invoices/payments), Canadian insurance (predetermination + claim state machine), communications log, marketing CRM, and lead-to-patient conversion. All under `/api/v2/scheduling/*`, `/api/v2/billing/*`, `/api/v2/insurance/*`, `/api/v2/communications/*`, `/api/v2/crm/*`.

## Hard constraints (CI gate)

1. `pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q` MUST stay green at every commit. Any byte-for-byte change to v1 response shapes is a regression.
2. Do not edit `api/main.py`'s existing route bodies. You may register new routers from `api/main.py` (one-line `include_router` add). Add new modules under `database/ops/`, `api/v2/scheduling/`, `api/v2/billing/`, `api/v2/insurance/`, `api/v2/communications/`, `api/v2/crm/`, `tests/track_ops/`.
3. New tables added via Alembic migration `track3_ops`. Apply cleanly on empty SQLite + Postgres.
4. Reuse existing helpers — don't duplicate:
   - Conflict detection rules: see `api/main.py:316-358` (active statuses tuple) and `tools/slot_utils.py:20`.
   - Notification helpers: `clients/sms_client.py`, `clients/email_client.py`. Use the `_delayed` variants for scheduling reminders. Honor `SMS_DELAY_SECONDS`, `SEND_BOOKING_SMS`, `SEND_CLINIC_BOOKING_EMAIL` env vars.
   - DB session: `database/connection.get_db`. Clinic dep: `api/main.py:43`.
5. Same auth-soft policy as Track 2: gate behind `V2_REQUIRE_AUTH=true`.

## Deliverables

### New tables (`database/ops/models.py`)

Scheduling:
- `operatories` — id, clinic_id, name, equipment_tags JSON, is_active
- `appointment_resources` — id, appointment_id (FK appointments), operatory_id (FK)
- `appointment_recurrences` — id, clinic_id, parent_appointment_id, rule (RRULE string), generated_through_date
- `appointment_reminders` — id, appointment_id, channel (sms|email), offset_minutes, scheduled_at, sent_at?, status (pending|sent|failed|cancelled), failure_reason?
- `waitlist_entries` — id, clinic_id, patient_id, requested_window_start, requested_window_end, provider_pref?, service_id?, priority, status (open|filled|expired|cancelled), created_at

Recall (post-treatment recare):
- `recall_rules` — id, clinic_id, name, trigger_event (denture_delivered|reline|annual|custom), offset_days, channel (sms|email|both)
- `recalls` — id, clinic_id, patient_id, rule_id, due_at, sent_at?, status (pending|sent|completed|cancelled)

Billing:
- `invoices` — id, clinic_id, patient_id, appointment_id?, treatment_plan_id?, status (draft|issued|partial|paid|void), subtotal, gst, total, balance, issued_at?, due_at?, currency (default "CAD")
- `invoice_lines` — id, invoice_id, sequence, procedure_code, description, qty, unit_price, total
- `payments` — id, invoice_id, method (cash|card|cheque|etransfer|insurance), amount, received_at, reference, notes

Insurance (CDAnet-aware shapes; transport not in v1):
- `insurance_claims` — id, clinic_id, invoice_id, carrier, kind (predetermination|claim), assignment_of_benefits bool, status (draft|submitted|accepted|adjudicated|paid|rejected|partial), submitted_at?, adjudicated_at?, paid_at?, response_payload JSON
- `claim_events` — id, claim_id, kind, occurred_at, payload JSON

Communications:
- `communications` — id, clinic_id, patient_id, channel (sms|email|inbound_sms|inbound_email), direction (out|in), body, status (queued|sent|delivered|failed|received), related_appointment_id?, related_invoice_id?, created_at, sent_at?
- `marketing_campaigns` — id, clinic_id, name, audience_query JSON, schedule_at, channel, body_template, status (draft|scheduled|sending|sent|cancelled)

CRM:
- `lead_events` — id, lead_id, kind (note|status_change|email_sent|sms_sent|converted), occurred_at, payload JSON. The existing `Lead` table stays unchanged.

### Endpoints

Scheduling (`api/v2/scheduling/router.py`):
- `POST /api/v2/scheduling/appointments` — body extends v1 with `operatory_id?`, `recurrence_rule?` (RRULE). Conflict detection now considers BOTH provider AND operatory busy.
- `POST /api/v2/scheduling/appointments/{id}/cancel` (with `cascade` flag for recurrences).
- `POST /api/v2/scheduling/appointments/{id}/reschedule`.
- `GET /api/v2/scheduling/operatories` / `POST` / `PUT` / `DELETE`.
- `POST /api/v2/scheduling/waitlist` / `GET` / `DELETE /{id}` / `POST /{id}/fill`.
- `GET /api/v2/scheduling/calendar?start=&end=&provider_id=&operatory_id=` — combined view.
- `POST /api/v2/scheduling/recall-rules` / `GET` / `PUT /{id}` / `DELETE /{id}`.
- `GET /api/v2/scheduling/recalls?status=`.

The reminder scheduler is a startup background task launched from `api.main.lifespan`. Loop wakes every 60s, finds `appointment_reminders` due in next minute, dispatches via `clients/sms_client` or `clients/email_client`, marks `sent`/`failed`. Idempotent on restart (skip rows already `sent`).

Billing (`api/v2/billing/router.py`):
- `POST /api/v2/billing/invoices` — body `{patient_id, appointment_id?, treatment_plan_id?, lines: [{procedure_code, qty, unit_price, description?}], gst_rate?}`. Computes `subtotal`, `gst`, `total`. Stays `draft`.
- `POST /api/v2/billing/invoices/{id}/issue` — sets `issued_at`, status `issued`, stamps `due_at = issued_at + 30d`.
- `POST /api/v2/billing/invoices/{id}/payments` — body `{method, amount, reference?}`. Updates `balance` and status (`partial`|`paid`).
- `POST /api/v2/billing/invoices/{id}/void`.
- `GET /api/v2/billing/invoices?patient_id=&status=`.

Insurance (`api/v2/insurance/router.py`):
- `POST /api/v2/insurance/claims` — kind=predetermination|claim. Stays `draft`. Computes patient/insurance split from `treatment_plan_items.insurance_coverage_pct` if treatment plan attached.
- `POST /api/v2/insurance/claims/{id}/submit` — sets `submitted_at`, status `submitted`. (Stub: no real CDAnet transport — log a `claim_event{kind:'submit_stub'}`.)
- `POST /api/v2/insurance/claims/{id}/adjudicate` — body `{response_payload, paid_amount, status: accepted|rejected|partial}`.
- `POST /api/v2/insurance/claims/{id}/mark-paid` — body `{paid_amount}`.
- `GET /api/v2/insurance/claims?patient_id=&status=`.

Communications (`api/v2/communications/router.py`):
- `POST /api/v2/communications/send` — body `{patient_id, channel, body, related_appointment_id?}`. Logs row and dispatches via existing helpers (NEW: an `email_client.send_patient_message` helper to add — keep payloads sanitized). Reuse `_send_sms_sync` from `clients/sms_client.py` with the same env toggles.
- `GET /api/v2/communications?patient_id=&channel=`.
- Inbound webhook stubs: `POST /api/v2/communications/inbound/sms` and `/inbound/email` — accept Twilio/SMTP webhook payloads; create `inbound_*` rows. Auth via shared-secret header `X-Webhook-Secret`.

CRM (`api/v2/crm/router.py`):
- `POST /api/v2/crm/leads/{id}/convert` — body `{create_patient: bool}`. If true, copies name/phone/email into a new `patients` row in same clinic, sets `Lead.status=CONVERTED`, writes `lead_events` row. Idempotent: returns existing patient if already converted.
- `POST /api/v2/crm/leads/{id}/events` — log a `note`/`status_change`/etc.
- `GET /api/v2/crm/leads/{id}/events`.
- `POST /api/v2/crm/marketing-campaigns` / `GET` / `POST /{id}/send`.

### Tests (`tests/track_ops/`)

- `test_multi_resource_conflict.py` — operatory busy ⇒ 409 even if provider free; provider busy ⇒ 409 even if operatory free.
- `test_recurring_generation.py` — RRULE `FREQ=WEEKLY;COUNT=4` produces 4 appointments; busy block prevents one ⇒ 409 on that occurrence (skip vs fail strategy: fail).
- `test_reminder_scheduler.py` — mock the dispatch calls; advance fake clock; reminders fire at offset; failure marks row `failed` with reason; restart doesn't re-send.
- `test_invoice_math.py` — 3 lines × varied qty; GST 5% (Alberta GST; no PST); patient-portion vs insurance-portion correct.
- `test_claim_state_machine.py` — submit, adjudicate, mark-paid; rejected path sets `paid_amount=0`; transitions out of `paid` are rejected.
- `test_lead_conversion.py` — first call creates patient; second call returns same patient (idempotent). Source preserved.
- `test_v1_regression.py` — full byte-equivalence: load `tests/test_api.py` as a module and run every assertion still passes (no diff). Or simpler: assert all v1 endpoint shapes via `tests/test_contract_v1.py`.

Use the existing `client_market_mall` fixture; add a `seed_billing` fixture that creates an invoice + payments for math tests.

## Success gate

```
pytest tests/track_ops -q && \
pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q && \
DATABASE_URL=sqlite:///./_track3_check.db uv run alembic upgrade head && \
rm -f _track3_check.db
```

All must exit 0. Loop until green.

## Notes

- Alberta GST rate is 5%, no PST. Make GST configurable per invoice (`gst_rate` body field, default 0.05).
- Currency stays "CAD" v1.
- For RRULE parsing, use `python-dateutil`'s `rrule` (already a transitive dep).
- For idempotent reminder dispatch, scheduler must hold a row-level transaction when marking `sent` (use `SELECT FOR UPDATE` on Postgres — fall back to optimistic check on SQLite).
- The reminder scheduler must NOT block app startup. Launch via `asyncio.create_task` in `lifespan`. On shutdown, cancel the task.
- For waitlist `fill`: pick the highest-priority open entry whose window overlaps the now-open slot; if multiple, FIFO by `created_at`.
- Mark conversion in `LeadEvent` (NOT a column on `Lead`). Don't change `Lead`'s schema.
