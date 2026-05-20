# Track 1 — Backend foundation: Auth, RBAC, Audit

You are a coding agent working on **one of five parallel tracks** that together extend the dental-api repo into a PMS/CRM for denturist clinics. Read `~/.claude/plans/now-i-want-to-fizzy-valley.md` for full context. Don't read or modify other tracks' files.

## Mission

Add JWT auth, role-based access control, audit logging, and Alembic-managed migrations for new tables. **Existing v1 endpoints under `/api/*` must keep working unauthenticated.** New endpoints under `/api/v2/auth/*` and `/api/v2/admin/*`.

## Hard constraints (CI gate)

1. `pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q` MUST stay green at every commit.
2. Do not edit files in `api/main.py`, `database/models.py`, `tools/`, `clients/`, or `tests/test_api.py` / `tests/test_schema.py` / `tests/test_contract_v1.py`. Add new modules under `database/auth/`, `api/v2/auth/`, `api/v2/admin/`, `tests/track_auth/`.
3. New tables added via a new Alembic migration (`alembic revision -m "track1_auth_rbac_audit"`). Migrations must apply cleanly from `alembic upgrade head` on an empty SQLite or Postgres DB.
4. `V1_REQUIRE_AUTH` env defaults to `false`. When false, `/api/*` behaves identically to v1.

## Deliverables

### New tables (additive)
- `users` — id (UUID), clinic_id (FK), email (unique per clinic), password_hash, full_name, is_active, locked_at?, last_login_at?, created_at, updated_at
- `roles` — id, clinic_id (nullable for system roles), name, permissions (JSON list of dotted scopes, e.g. `["patients.read","appointments.write"]`)
- `user_roles` — composite PK (user_id, role_id)
- `refresh_tokens` — id, user_id, token_hash, issued_at, expires_at, revoked_at?
- `audit_log` — id, clinic_id, user_id?, action (str), entity_type, entity_id, before (JSON), after (JSON), ip?, user_agent?, created_at

Place models under `database/auth/models.py` and import in `database/__init__.py` so `Base.metadata` sees them.

### Endpoints (`api/v2/auth/router.py` and `api/v2/admin/router.py`, mounted from `api/main.py`)
- `POST /api/v2/auth/login` — body `{email, password}`, scoped by `X-Clinic-Id`. Returns `{access_token, refresh_token, expires_in, user: {...}}`. Increment fail counter; lock after 5 fails.
- `POST /api/v2/auth/refresh` — body `{refresh_token}`. Rotates token (revoke old, issue new).
- `POST /api/v2/auth/logout` — revokes the caller's refresh token.
- `GET /api/v2/auth/me` — current user + roles + permissions.
- `POST /api/v2/admin/users` — create user (requires `users.write`).
- `GET /api/v2/admin/users` — list (paginate `?limit&offset`).
- `PUT /api/v2/admin/users/{id}` — update / disable.
- `POST /api/v2/admin/users/{id}/roles` — assign role.
- `GET /api/v2/admin/roles` / `POST` / `PUT /{id}` — manage roles.
- `GET /api/v2/admin/audit-log?entity_type=&entity_id=&user_id=&limit=&offset=` — paginated.

### Cross-cutting modules
- `api/v2/auth/dependencies.py`:
  - `get_current_user(request, db) -> User` — parses Bearer JWT, 401 on invalid/expired.
  - `require_permissions(*perms)` — FastAPI dependency factory.
  - `audit_context(request, current_user)` — populates a contextvar with `(user_id, ip, ua)` for the audit listener.
- `database/auth/audit.py`:
  - SQLAlchemy event listeners (`after_insert`, `after_update`, `after_delete`) on every PHI table (start with `Patient`, `Appointment`, `ClinicalNote` if it exists later, `Lead`, `Document`). Read the audit context to populate `user_id/ip/ua`.
  - Use `inspect(target).attrs` to compute before/after diffs for updates.

### Seed
- `scripts/seed_auth.py` — idempotently creates default roles (`admin`, `denturist`, `assistant`, `front_desk`, `accountant`) with the permission matrix below, plus an admin user `admin@example.com / changeme` for the `default` clinic. Documented; DO NOT run in production.

Permission matrix (v1):
- `admin` → all `*.*`
- `denturist` → `patients.*`, `appointments.*`, `clinical.*`, `lab.*`, `treatment_plans.*`
- `assistant` → `patients.read`, `patients.write`, `appointments.*`, `clinical.read`, `lab.*`
- `front_desk` → `patients.read`, `patients.write`, `appointments.*`, `leads.*`, `communications.*`, `billing.read`
- `accountant` → `billing.*`, `insurance.*`, `patients.read`, `appointments.read`

### Tests (`tests/track_auth/`)
- `test_login_flow.py` — happy path; bad password; nonexistent user; lockout after 5 fails; locked-user 403.
- `test_refresh.py` — rotate token; old refresh rejected; expired refresh rejected.
- `test_require_permissions.py` — denies missing perm with 403; admin permits all.
- `test_audit_log.py` — create/update/delete a `Patient` via v2 endpoints → audit row written with correct `before`/`after`/`user_id/ip/ua`.
- `test_alembic_migration.py` — `alembic upgrade head` then `alembic downgrade -1` round-trip on SQLite.

Use the existing `client` fixture from `tests/conftest.py` plus a new `auth_client` fixture that logs in an admin user and returns a TestClient with the Bearer header preset.

## Success gate

```
pytest tests/track_auth -q && \
pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q && \
DATABASE_URL=sqlite:///./_track1_check.db uv run alembic upgrade head && \
rm -f _track1_check.db
```

All three commands must exit 0. If anything fails, fix and re-run. Loop until green.

## Notes

- JWT signing key from env `JWT_SECRET` (32+ chars). Default in dev: random per-process via `os.urandom`. Tests should pin to a known secret via `monkeypatch.setenv`.
- Access token lifetime 15 min; refresh 14 days.
- Use `passlib[bcrypt]` for hashing. Use `python-jose` for JWT.
- `audit_log.before` / `.after` should be plain JSON-serializable dicts of the changed columns only (not the full row).
- Multi-tenant: `email` is unique per clinic (`UniqueConstraint("clinic_id","email")`).
