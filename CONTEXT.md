# dental-api Context
Last updated: 2026-06-18

## Files
| path | role | edit when |
|---|---|---|
| `api/main.py` | FastAPI app assembly, middleware, lifespan, router mounts | Adding global middleware, health behavior, or application wiring |
| `api/dependencies/` | Request auth, clinic resolution, shared dependencies | Changing tenant scoping, auth, or dependency injection |
| `api/v1/` | Legacy/domain v1 routers for calendar, patients, providers, holds, calls | Adding or fixing v1 HTTP endpoints |
| `api/v2/` | PMS/CRM v2 track routers for auth, clinical, scheduling, settings, reporting, etc. | Working on v2 product surfaces |
| `api/admin/`, `api/portal/`, `api/public/`, `api/webhooks/` | Admin, portal, public, and webhook route groups | Editing non-versioned route surfaces |
| `services/` | Business logic for appointments, holds, notifications, SMS, slots, RAG | Changing behavior behind routers |
| `database/` | SQLAlchemy models, connection, observability, per-track model packages | Changing schema, tenant models, or DB initialization |
| `alembic/` | Alembic migration environment and versions | Adding durable schema migrations |
| `clients/` | Email, SMS/Telnyx, lab numbering adapters | Changing external-service integration |
| `tools/slot_utils.py` | Core availability computation | Editing slot generation or conflict semantics |
| `scripts/` | Seed, migrate, deploy, sync, smoke, and rebuild scripts | Operational changes or local/prod data tasks |
| `tests/` | Pytest suite with SQLite and Postgres fixtures | Adding regression tests for API/service/database behavior |
| `docs/openapi-v2.yaml` | OpenAPI contract snapshot | Updating public API contract docs |

## Data Flow
HTTP requests enter FastAPI routers, resolve clinic/auth dependencies, call `services/`, read/write SQLAlchemy models via `database/`, and use `clients/` for best-effort SMS/email/lab side effects.

## Commands
| command | use |
|---|---|
| `./run_local.sh` | Local dev server with SQLite, schema sync, port 8001 |
| `DATABASE_URL=sqlite:///./dental_clinic.db python scripts/sync_db.py` | Initialize/sync local DB |
| `uv run python run_api.py` | Manual API entrypoint using `PORT` |
| `uv run pytest` | Full test suite |
| `uv run pytest tests/test_file.py::test_name` | Focused test |
| `docker compose -f docker-compose.dev.yml up -d postgres` | Start Postgres/pgvector backend for Postgres-only tests |

## Gotchas
- Every query must scope by clinic; do not add cross-tenant reads or writes.
- SQLite fixtures skip Postgres-only tables; use `pg_client`/`pg_db_session` for arrays, JSONB indexes, pgvector, and Postgres semantics.
- `run_api.py` intentionally falls back to a stub `/health` app on import failure for deploy diagnostics.
- `dental_clinic.db` is an intentional local seed artifact in this repo.

## Hard Rules
- Put business logic in `services/`; keep routers thin.
- Update slot computation and conflict checks together when appointment status semantics change.
- Notifications are best effort and must not raise back to request handlers.
