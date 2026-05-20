# PMS Module F0 — Backend schema fill + Demo Clinic seed (TDD, prerequisite)

Make `make test-pms-f0` exit 0.

## Why this exists

After M0–M6 every page has *some* working logic, but several pages render empty (`invoicesDb=[]`, `commsDb=[]`) and a few schemas are missing fields the UI in F1–F6 needs. F0 closes the schema gaps and lays down a rich "demo clinic" seed so every downstream module can rely on data being present.

## Success criteria

### Backend schema additions (all NULLABLE / additive)

- `lab_cases.case_number TEXT` — unique, server-generated `LC-YYYY-NNNN` on insert. Existing rows get `NULL` (downgrade-clean).
- `lab_cases.treatment_plan_id` UUID FK → `treatment_plans.id`, nullable.
- `communications.thread_key TEXT` — server-computed on insert as `f"{patient_id}:{channel}"`. Indexed.
- `communications.read_at TIMESTAMP NULL` — `NULL` means unread.
- `communications.attachments JSON DEFAULT '[]'` — list of `{url, mime, size, name}`.
- `Communication.channel` — formalize the enum to include `'whatsapp'` (the send route already accepts it; this just makes the DB enum/check constraint accept it explicitly).

Single Alembic revision: `track_pms_f0_extra_columns`. Must `upgrade` and `downgrade` cleanly on SQLite (test with `tests/track_pms_f0/test_alembic_round_trip`).

### Backend endpoints

- New router `api/v2/settings/router.py`:
  - `GET /api/v2/settings/clinic` → returns `{display_name, timezone, working_hour_start, working_hour_end, address, contact_phone, booking_notification_email}`. Reads from the `Clinic` row resolved by `X-Clinic-Id` (use existing `get_clinic` dependency).
  - `PUT /api/v2/settings/clinic` body partial — patches the same fields. Returns the updated config.
  - `GET /api/v2/settings/integrations` → `{sms: {enabled: bool}, email: {enabled: bool}, whatsapp: {enabled: bool}}` derived from env (`TWILIO_ACCOUNT_SID`, `SMTP_HOST`, `TWILIO_WHATSAPP_FROM`).
  - Add `Clinic.display_name TEXT NULL` column (defaults to existing clinic id if null on read).
- Extend `api/v2/communications/router.py`:
  - `PATCH /api/v2/communications/threads/{thread_key}/read` — sets `read_at = now()` for all messages in that thread (filtered by `clinic_id`). Returns `{updated: <count>}`.
- Wire the new settings router into `api/main.py` mount table.

### Demo Clinic seed script

`scripts/seed_demo_clinic.py`:
- Idempotent: if `default` clinic already has `>5` invoices, exit 0 with `"already seeded"`.
- Uses `Faker` (Python `faker` library — add to `pyproject.toml`).
- Creates in the `default` clinic:
  - 6 providers (denturist, doctor, assistant titles)
  - 30 patients with name/phone/email/dob/address
  - 5 lab vendors
  - 8 services
  - 25 invoices spanning statuses (draft 4, issued 8, partial 6, paid 6, void 1) over the past 90 days
  - 60+ communications spread across SMS / Email / WhatsApp; mix of inbound and outbound; ~8 unread (`read_at = NULL`); group into ~12 threads
  - 12 lab cases distributed across all 5 statuses (draft, sent, in_progress, returned, remake) with realistic vendor + due_back_at + auto-generated case_numbers
  - 15 leads spread NEW(5)/CONTACTED(4)/QUALIFIED(3)/CONVERTED(2)/LOST(1), with random source
  - 8 treatment plans across all statuses (draft/presented/accepted/in_progress/completed/declined), each with 2–5 items
- Wire into `scripts/sync_db.py` so `./run_local.sh` produces a populated demo on first run (only when DB is empty, controlled by env `SEED_DEMO=1`, default on for SQLite local dev).

### Mock parity (frontend)

- Centralize fixtures in new `frontend/src/mocks/seedFixtures.ts`. Export typed arrays: `seedInvoices`, `seedCommunications`, `seedLabCases`, `seedLeads`, `seedTreatmentPlans`, `seedPatients`. Match the backend schema shapes (server-side fields like `thread_key`, `read_at`, `attachments`, `case_number`).
- Update `frontend/src/mocks/ops.ts`:
  - `invoicesDb` initialized from `seedInvoices` (≥10 rows).
  - `commsDb` initialized from `seedCommunications` (≥30 rows across 3 channels).
  - Add a handler for `PATCH /api/v2/communications/threads/:thread_key/read` (returns `{updated: N}`, mutates `commsDb` to set `read_at`).
- Add a handler for `GET /api/v2/settings/clinic` returning a fixture; `PUT` echoes the body merged into the fixture; `GET /api/v2/settings/integrations` returns `{sms:{enabled:true}, email:{enabled:true}, whatsapp:{enabled:true}}`.

## Tests first (`tests/track_pms_f0/`)

Create `tests/track_pms_f0/__init__.py` (empty) and `tests/track_pms_f0/test_f0_endpoints.py`:

```python
def test_lab_case_number_auto_generated(client_with_lab_setup): ...
    # POST /api/v2/lab/cases → response includes case_number matching r"LC-\d{4}-\d{4}"

def test_lab_case_links_to_treatment_plan(client_with_plan_and_lab): ...
    # POST /api/v2/lab/cases with {treatment_plan_id: ...} → GET returns the link

def test_communication_thread_key_computed(client): ...
    # POST /api/v2/communications/send → response.thread_key == f"{patient_id}:{channel}"

def test_communication_read_at_nullable_default_null(client): ...

def test_thread_mark_read_endpoint(client): ...
    # send 3 messages on same thread, PATCH /threads/{thread_key}/read → all 3 read_at != null

def test_settings_get_returns_clinic_config(client): ...

def test_settings_put_updates_clinic_config(client): ...
    # PUT {display_name: 'Smile Co'} → GET returns it

def test_settings_integrations_returns_provider_health(client, monkeypatch): ...
    # set TWILIO_ACCOUNT_SID env → integrations.sms.enabled is True

def test_seed_demo_clinic_idempotent(): ...
    # call scripts.seed_demo_clinic.main() twice; second is a no-op

def test_alembic_round_trip(): ...
    # alembic upgrade head, then downgrade -1, then upgrade head — no errors
```

## Implementation files

- `alembic/versions/<id>_track_pms_f0_extra_columns.py` (new)
- `database/clinical/models.py` — `LabCase.case_number`, `LabCase.treatment_plan_id`
- `database/ops/models.py` — `Communication.thread_key`, `read_at`, `attachments`; `Clinic.display_name`
- `clients/lab_case_numbering.py` (new) — `next_lab_case_number(session, clinic_id) -> str`
- `api/v2/lab/router.py` — call numbering on create; expose `treatment_plan_id`
- `api/v2/communications/router.py` — set `thread_key` on insert; add `PATCH /threads/{thread_key}/read`
- `api/v2/settings/router.py` (new) — `GET /clinic`, `PUT /clinic`, `GET /integrations`
- `api/main.py` — mount the settings router
- `scripts/seed_demo_clinic.py` (new)
- `scripts/sync_db.py` — invoke seed when SQLite + empty
- `frontend/src/mocks/seedFixtures.ts` (new)
- `frontend/src/mocks/ops.ts` — initialize from fixtures + add settings + read handlers
- `docs/openapi-v2.yaml` — re-sync via `cd frontend && npm run gen:api`

## Constraints

- v1 contract MUST stay green (`tests/test_contract_v1.py`).
- All existing M0–M6 + P0–P5 tests MUST stay green.
- Alembic round-trip required.
- Seed script must not crash if optional services/providers tables already have rows — be additive, key off phone/email uniqueness.
- Don't import `faker` at api/main.py module load — only inside the seed script.

```bash
make test-pms-f0
```
