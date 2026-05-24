# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

Local dev (SQLite, auto-syncs schema, runs on port 8001):
```bash
./run_local.sh
```

Manual run (PORT defaults to 8000; `run_api.py` is the entrypoint that always binds to PORT):
```bash
DATABASE_URL=sqlite:///./dental_clinic.db python scripts/sync_db.py   # init + seed
uv run python run_api.py                                              # or: uvicorn api.main:app --reload --port 8001
```

Tests (pytest config in `pyproject.toml`, `testpaths = ["tests"]`):
```bash
uv run pytest                              # full suite
uv run pytest tests/test_api.py            # single file
uv run pytest tests/test_api.py::test_x    # single test
uv run pytest -k slot                      # by keyword
```

Tests have **two backends** via `tests/conftest.py` — pick the right fixture for what you're testing:

- **SQLite (in-memory, default)** — fixtures `client`, `db_session`, `db_engine`, `client_market_mall`. Fast, no real DB needed, used by most tests. `client` overrides `get_db` and seeds the `default` clinic; `client_market_mall` additionally seeds `market-mall-denture` (providers 101/102, busy blocks, service 700). Tables that can't compile on SQLite (e.g. `rag_docs` with pgvector, `clinic_routing` with `TEXT[]` / `JSONB`) are skipped via `_SQLITE_SKIP_TABLES`.
- **Postgres + pgvector** — fixtures `pg_client`, `pg_db_session`, `pg_engine`. Connects to `TEST_DATABASE_URL` (default `postgresql://postgres:dev@localhost:5433/dental_test`); skips automatically if unavailable. Use this whenever you're testing tables/columns that require Postgres-specific types (arrays, JSONB-with-GIN, pgvector, etc.) — running `docker compose -f docker-compose.dev.yml up -d postgres` from this repo brings up the dev DB on port 5433.

When adding a table that uses Postgres-only types, add its name to `_SQLITE_SKIP_TABLES` and write its tests against `pg_client` / `pg_db_session`.

DB migration for existing PG instances:
```bash
DATABASE_URL=postgresql://... python scripts/migrate_add_clinics.py
DATABASE_URL=postgresql://... python scripts/migrate_clinic_contact_fields.py
```

Deployment target is Google Cloud Run — see `DEPLOY_GOOGLE_CLOUD.md`. Cloud Run requires the Unix-socket DSN form: `postgresql://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE`.

## Architecture

**Single FastAPI app (`api/main.py`) with SQLAlchemy ORM.** The DB is the source of truth; there is no external calendar sync (despite the `calendar_event_id` column and `/api/calendar/*` endpoint names — these are vestigial naming).

### Multi-tenancy (critical)

Every request is scoped by clinic via the `X-Clinic-Id` header (default: `"default"`). This is enforced by the `get_clinic` dependency (`api/dependencies.py`), which 404s if the clinic row doesn't exist. **Every query in the API filters by `clinic_id`** — when adding endpoints or queries, you must scope by `clinic.id` or you'll leak data across tenants. Per-clinic config (timezone, working hours, address, contact phone, booking notification email) lives on the `Clinic` row, not in env vars.

Tests reflect this: the `client` fixture seeds the `default` clinic before any request can succeed.

### Slot computation

`tools/slot_utils.get_available_slots` computes availability **from the DB** by intersecting:
- Per-clinic working hours (`hour_start`, `hour_end`) and timezone
- `ProviderBusyBlock` rows (recurring weekly *unavailable* windows — note: busy blocks mean UNAVAILABLE, not available)
- Existing `Appointment` rows with status in `{SCHEDULED, CONFIRMED, PENDING_SYNC, PENDING}`

The same "active statuses" set is used for conflict detection in `services/appointments.check_conflicts_for_create` and `check_conflicts_for_reschedule`. When changing status semantics, update both the slot computation and the conflict checks together.

### Background notifications

`POST /api/calendar/events`, `PUT /appointments/{id}/cancel`, and `PUT /appointments/{id}/reschedule` schedule **FastAPI `BackgroundTasks`** (in-process, not a queue) for:
- Twilio SMS to the patient (`clients/sms_client.py`) — toggled by `SEND_BOOKING_SMS`, delayed by `SMS_DELAY_SECONDS`.
- SMTP email to the clinic on new bookings (`clients/email_client.py`) — recipient resolved by `resolve_booking_notification_recipient`: `BOOKING_NOTIFICATION_TO` env var overrides the per-clinic `clinic.booking_notification_email` (use the env var only for testing; leave it unset in prod).

Notifications must never raise back to the request handler — they're best-effort and logged on failure.

### Database connection

`database/connection.py` resolves `DATABASE_URL` in this priority order: `POSTGRES_URL` → `POSTGRES_PRISMA_URL` → `POSTGRES_URL_NON_POOLING` → `DATABASE_URL` → `sqlite:////tmp/dental_clinic.db`. It also normalizes `postgres://` → `postgresql://` and strips Supabase-only `supa=` query params. `init_db()` is called from the FastAPI lifespan, so tables are created on startup; failures are logged but don't crash the app.

### Resilient entrypoint

`run_api.py` always binds to `PORT` even if `api.main` fails to import — it falls back to a stub app that only serves `/health`. This is intentional so Cloud Run / Railway health checks pass and you can debug a misconfigured deploy via logs rather than a crash loop. Don't "fix" this by removing the try/except.

## Repo layout

- `api/` — FastAPI app (`main.py`), shared deps (`dependencies.py`), serializers, middleware, and per-version routers under `api/v1/<domain>/` and `api/v2/<track>/`.
- `services/` — business logic that v1 routers delegate to (appointments conflict checks, notifications, slot wrappers).
- `database/` — SQLAlchemy models, connection, observability hooks, and per-track sub-packages (`auth/`, `clinical/`, `ops/`).
- `clients/` — external-service adapters (Twilio SMS, SMTP email, lab case numbering).
- `tools/` — `slot_utils.py` (the actual slot computation; `services/slots.py` is a thin wrapper).
- `alembic/` — schema migrations. `versions/316d68e5e670_baseline_v1_schema.py` is the baseline; pre-baseline migrations under `scripts/migrate_*.py` are kept for historical reference but should not be re-run on greenfield databases.
- `scripts/` — operational shells (`provision_db.sh`, `seed_db.sh`, `smoke_tests.sh`, gitignored `deploy.sh`), schema sync (`sync_db.py`), seed scripts (`seed_*.py`), and historical pre-baseline migrations.
- `tests/` — pytest suite (286 passing). Uses in-memory SQLite via `tests/conftest.py`.
- `docs/superpowers/` — design specs and implementation plans for refactors.

## Things to know

- Provider was renamed from "Doctor"; the `Provider` model is generic (denturist, doctor, assistant, etc.) and `provider.title` + `provider.name` are joined for display (`"Dr Smith"`).
- Default timezone fallback throughout is `America/Edmonton`.
- `tmp/` is an archive of older docs/frontend/scripts — don't add new code there.
- Business logic lives in `services/` (`appointments.py`, `notifications.py`, `slots.py`). `api/v1/<domain>/router.py` modules are thin HTTP layers that delegate to `services/`; `api/main.py` is now just the FastAPI app + middleware + router mounts (~190 lines).
- `dental_clinic.db` is committed (local SQLite seed) and intentionally tracked.
- The CRM/PMS frontend used to live at `frontend/`; it now lives in the sibling repo `dental-system/dental-crm-frontend/`.
