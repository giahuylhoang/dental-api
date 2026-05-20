# PMS Module M0 — Backend gap-fill (TDD: tests first)

You are kiro-cli running headless. Make `make test-pms-m0` exit 0.

The gate runs:
1. File-existence check on test files (you must write tests first)
2. `uv run pytest tests/track_pms_m0 -q` — your tests must pass
3. `uv run pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q` — v1 contract
4. `cd frontend && npm run gen:api && npm run build`

## Repo facts

- Repo root: `/Users/giahuyhoangle/Projects/dental-api`
- FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Alembic + uv. Multi-tenant via `X-Clinic-Id`.
- v2 routers under `api/v2/*`, mounted in `api/main.py`.
- Tests use **in-memory SQLite** seeded by `tests/conftest.py` (`client` fixture, `default` clinic).
- Use `uv run pytest`, `uv run alembic`.
- Existing migration head: `d4e5f6a7b8c9`.

## Success criteria

1. Add nullable column `appointments.chief_complaint TEXT` (additive — must NOT break v1 contract).
2. Add nullable columns `treatment_plan_items.tooth_number INTEGER`, `treatment_plan_items.care_notes TEXT`.
3. Endpoint `POST /api/v2/crm/leads` — body `{first_name, last_name, phone, email?, source?, notes?}`. Returns the new lead.
4. Endpoint `PUT /api/v2/crm/leads/{lead_id}` — body `{owner_id?, status?, notes?, ...}`. Partial update.
5. Endpoint `POST /api/v2/crm/leads/{lead_id}/activities` — body `{kind: 'note'|'call'|'email'|'meeting', body, ...}`. Returns activity row. Use `lead_events` table that already exists in `database/ops/models.py`.
6. Endpoint `GET /api/v2/crm/leads/{lead_id}/activities` — list activities for the lead, sorted by created_at DESC.
7. `clients/sms_client.py` extended: new function `send_whatsapp(to: str, body: str) -> dict` using the **same** Twilio client but with `whatsapp:` prefix on `from_` and `to`. Use env `TWILIO_WHATSAPP_FROM` (fall back to `TWILIO_PHONE_NUMBER`).
8. Communications endpoint must accept `channel='whatsapp'` (the channel field is already a free-form String). When `channel=='whatsapp'`, dispatch via `send_whatsapp` instead of `send_sms`.
9. One Alembic revision: `alembic revision -m "track_pms_m0_extra_columns"` with explicit revision id and `down_revision = 'd4e5f6a7b8c9'`. `upgrade()` adds the columns; `downgrade()` removes them. Round-trip clean.
10. Update `docs/openapi-v2.yaml` so the new lead create/update/activity endpoints are documented (frontend `npm run gen:api` consumes this).

## Tests first

Create `tests/track_pms_m0/__init__.py` (empty) and `tests/track_pms_m0/test_m0_endpoints.py` with at minimum:

```python
def test_chief_complaint_persists(client):
    # Create patient, provider, service, then POST appointment with chief_complaint='tooth pain'.
    # GET it back; assert chief_complaint comes back unchanged.
    ...

def test_treatment_plan_item_tooth_number_and_care_notes(client):
    # POST a treatment plan with one item that has tooth_number=14 and care_notes="root canal candidate".
    # GET; assert the item carries the same values.
    ...

def test_v1_appointment_response_does_NOT_leak_chief_complaint(client):
    # The v1 GET /api/appointments/{id} response shape MUST NOT include chief_complaint key.
    ...

def test_crm_create_lead(client):
    # POST /api/v2/crm/leads with name+phone+source. Status 201 (or 200). Body has id and the values back.
    ...

def test_crm_update_lead_owner(client):
    # POST a lead, then PUT /api/v2/crm/leads/{id} with owner_id. GET; owner_id is set.
    ...

def test_crm_activity_create_and_list(client):
    # POST a lead, then POST /api/v2/crm/leads/{id}/activities with kind=note + body.
    # GET .../activities; list contains 1 entry.
    ...

def test_send_whatsapp_uses_whatsapp_prefix(monkeypatch):
    # monkeypatch twilio Client.messages.create; call send_whatsapp(to='+15551234567', body='hi').
    # assert .create was called with from_=startswith('whatsapp:') and to='whatsapp:+15551234567'.
    ...

def test_send_communication_channel_whatsapp_routes_to_send_whatsapp(client, monkeypatch):
    # monkeypatch send_whatsapp; POST /api/v2/communications/send with channel='whatsapp'; assert send_whatsapp was called.
    ...
```

Make every test self-contained. Use the `client` fixture for HTTP. Use direct `monkeypatch` of imports for the `send_whatsapp` test (no real Twilio call).

## v1 protection (CRITICAL)

- v1 endpoints (`/api/*`) must continue returning their existing keysets. The `tests/test_contract_v1.py` snapshot tests are the enforcement gate.
- New columns are nullable AND only echoed back via v2 endpoints (not added to v1 response Pydantic models).

## Migration

Use Alembic, not `Base.metadata.create_all`. Verify round-trip:

```bash
DATABASE_URL=sqlite:///./_check.db uv run alembic upgrade head
DATABASE_URL=sqlite:///./_check.db uv run alembic downgrade -1
DATABASE_URL=sqlite:///./_check.db uv run alembic upgrade head
rm -f _check.db
```

When `make test-pms-m0` exits 0, you are done.
