# dental-api v1 Router Refactor — Design

**Date:** 2026-05-19
**Status:** Approved (design phase)
**Owner:** Gia Huy

## Goal

Break up `api/main.py` (1,678 lines, 32 routes, inline Pydantic schemas, inline
business logic) into a domain-organized router layout that mirrors the existing
`api/v2/` structure, **without changing any externally observable behavior**.

The v1 surface is consumed in production by the `dental-agent` service via
`clients/calendar_client.py` (`CALENDAR_API_URL`). Every URL, header, request
body, response body, and error envelope must remain byte-compatible after the
refactor.

## Non-Goals

- No URL renames, no response-shape changes, no header changes.
- No changes to `api/v2/`.
- No changes to `frontend/`, `dental-calendar/`, or `dental-agent/`.
- No database schema changes.
- No new endpoints, no removed endpoints.
- Not deleting the empty `api/routes/` directory yet (do that in a follow-up
  cleanup PR so the refactor diff stays focused).

## Constraints (the wire contract)

These properties of the v1 API are load-bearing for `dental-agent` and must
survive the refactor unchanged:

1. **URL paths.** All routes keep their current `/api/...` prefixes. The
   directory name `v1` in the new layout refers to the *contract version*, not
   a URL prefix — same convention `api/v2/` already uses.
2. **Multi-tenancy header.** `X-Clinic-Id` continues to resolve via
   `get_clinic_id` / `get_clinic` dependencies, default value `"default"`,
   404 on unknown clinic.
3. **409 conflict envelope.** The `busy_block` detail shape produced by
   `_busy_block_envelope` (legacy `weekday` field + v2 `weekdays`,
   `specific_date`, `recurrence_until`) is preserved verbatim.
4. **Appointment detail shape.** `_to_appointment_detail` continues to be the
   single serializer for `AppointmentDetailResponse`.
5. **Active appointment statuses.** The set
   `{SCHEDULED, CONFIRMED, PENDING_SYNC, PENDING}` remains the basis for both
   slot computation (`tools/slot_utils`) and conflict detection in
   create/reschedule. These two call sites must continue to share one source
   of truth — they cannot drift during the move.
6. **Background notifications.** `POST /api/calendar/events`,
   `PUT /api/appointments/{id}/cancel`, and
   `PUT /api/appointments/{id}/reschedule` continue to schedule FastAPI
   `BackgroundTasks` for Twilio SMS + SMTP email. Failures must still be
   swallowed and logged — they must never raise back to the request handler.
7. **Resilient entrypoint.** `run_api.py` keeps its try/except fallback to a
   stub `/health` app when `api.main` fails to import (intentional, per
   `CLAUDE.md`).
8. **Test contract.** `tests/test_contract_v1.py` (and the broader v1 surface
   tests under `tests/`) must stay green at every step of the migration. They
   are the gate.

## Current State

```
api/
  main.py          # 1,678 lines: lifespan, middleware, 32 routes, 12 schemas, helpers
  caching.py
  errors.py
  middleware/
  routes/          # EMPTY — abandoned half-refactor
  v2/              # already domain-split: auth, scheduling, clinical, billing, lab, ...
services/          # EMPTY — flagged in CLAUDE.md as a leftover
tools/
  slot_utils.py    # shared by main.py
clients/           # outbound clients (SMS, email)
database/          # models split by area: auth, clinical, ops, v1_1
```

## Target State

```
api/
  main.py                      # ~150 lines: FastAPI app, lifespan, CORS, mount routers
  dependencies.py              # get_clinic_id, get_clinic, get_db re-export
  serializers.py               # _to_appointment_detail, _busy_block_envelope
  errors.py                    # unchanged
  caching.py                   # unchanged
  middleware/                  # unchanged
  v1/
    __init__.py                # aggregates routers for main.py to mount
    calendar/
      router.py                # /api/calendar/slots, /api/calendar/events
      schemas.py
    appointments/
      router.py                # /api/appointments[/...] including /cancel, /status,
                               #   /reschedule, /bulk/date/{date}
      schemas.py
    patients/
      router.py                # /api/patients[/...], /api/patients/verify
      schemas.py
    providers/
      router.py                # /api/providers[/{id}]
    catalog/
      router.py                # /api/services[/{id}]  (folder named `catalog`
                               #   to avoid colliding with top-level services/)
    leads/
      router.py                # /api/leads[/...]
      schemas.py
    clinics/
      router.py                # /api/clinics, /api/clinics/me
      schemas.py
  system.py                    # /health, /api/debug/db-info  (NOT under v1/ —
                               #   these are app-level diagnostics, not part of
                               #   the v1 contract)
  v2/                          # untouched

services/                      # populated during the refactor (see below)
  __init__.py
  appointments.py              # create / reschedule / cancel / status transitions,
                               #   conflict detection (shared with slot computation)
  notifications.py             # background-task scheduling for SMS + email,
                               #   including resolve_booking_notification_recipient
  slots.py                     # thin wrapper around tools/slot_utils so router
                               #   doesn't reach into tools/ directly
```

Pydantic schemas for v1 live next to their router (`v1/<domain>/schemas.py`),
matching how v2 organizes its DTOs. Schemas are **lifted, not rewritten** —
field names, defaults, validators, and `ConfigDict` settings copy across
verbatim.

## Where Business Logic Goes

The split between "lives in the router" and "lives in `services/`" is driven
by whether the logic is non-trivial enough to deserve unit tests without
spinning up the HTTP layer.

**Stays in the router** (thin handlers, one or two DB queries, straight
serialization):

- `GET /api/calendar/slots` (delegates to `services/slots.py`)
- All simple list/get/CRUD for patients, providers, services-catalog, leads,
  clinics
- `/health`, `/api/debug/db-info`

**Moves to `services/appointments.py`:**

- Conflict detection against `ProviderBusyBlock` and active-status
  `Appointment` rows (currently duplicated at `api/main.py:319` and
  `api/main.py:916`). The service exposes one function used by both create
  and reschedule paths.
- Status-transition validation for `PUT /api/appointments/{id}/status`.
- Reschedule orchestration (cancel-old + create-new semantics).
- Bulk delete by date.

**Moves to `services/notifications.py`:**

- `resolve_booking_notification_recipient` (currently inline).
- The functions that schedule the SMS/email `BackgroundTasks`. Routers call a
  single `schedule_booking_notifications(...)` /
  `schedule_cancel_notifications(...)` /
  `schedule_reschedule_notifications(...)` entry point.

CRUD that's truly one ORM call away from the router stays in the router. We
don't introduce a service for `GET /api/providers` just to have one.

## Migration Sequence

Each step is a self-contained change. Contract tests gate every step — the
suite (`uv run pytest tests/test_contract_v1.py tests/test_api.py`) must pass
before merging the step and before starting the next.

1. **Plumbing.** Create `api/dependencies.py` and `api/serializers.py`. Move
   `get_clinic_id`, `get_clinic`, `_busy_block_envelope`,
   `_to_appointment_detail` out of `main.py`. Re-import them in `main.py` so
   nothing else changes. Run tests.

2. **Simplest domains first** — `clinics/` and `providers/`. Create the
   router file, move the routes, move the schemas, register the router in
   `main.py` via `app.include_router(...)`, delete the originals from
   `main.py`. Run tests.

3. **CRUD-shaped domains** — `catalog/` (services-the-resource) and
   `leads/`. Same pattern. Run tests.

4. **Patients.** Includes `/api/patients/verify`. Same pattern. Run tests.

5. **Calendar + appointments together.** This is the heavy step:
   - Extract `services/appointments.py` with conflict detection + status
     transitions + reschedule + bulk-delete.
   - Extract `services/notifications.py` with background-task scheduling.
   - Extract `services/slots.py` (thin wrapper).
   - Move the routers (`calendar/`, `appointments/`).
   - Delete the originals from `main.py`.
   - Run tests, including any tests that explicitly assert on background
     notification scheduling.

6. **Health / debug.** Move `/health` and `/api/debug/db-info` to
   `api/system.py` (sibling of `v1/`, not under it — they are app-level
   diagnostics, not part of the v1 contract). Run tests.

7. **`main.py` cleanup.** Remove unused imports. `main.py` should now be
   ~150 lines: FastAPI app construction, lifespan, CORS, middleware
   registration, and `app.include_router(...)` calls.

8. **Verification pass.** Diff the OpenAPI schema before/after — every path,
   operation ID, request schema, response schema should be identical.
   `test_openapi_sync.py` already exists; extend if needed.

Each step is a separate PR (or separate commit on the refactor branch) so
review stays tractable and revert is cheap.

## Testing Strategy

- `tests/test_contract_v1.py` is the primary gate. It is not modified by this
  refactor — if it fails, the refactor regressed the contract.
- `tests/test_api.py` covers the broader v1 surface. Same rule.
- Existing test fixtures in `tests/conftest.py` (in-memory SQLite, `client`
  fixture seeding the `default` clinic, `client_market_mall` fixture) are
  unchanged.
- New unit tests **may** be added for the extracted `services/` functions
  (e.g. conflict detection given a synthetic set of busy blocks and
  appointments), but the refactor does not depend on them — the HTTP-level
  contract tests already cover behavior end-to-end.
- `test_openapi_sync.py` and the OpenAPI diff in step 8 catch shape drift.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Hidden coupling between two routes via a module-level variable in `main.py` | Plumbing step (1) runs the tests first; any global that breaks shows up immediately. |
| `_to_appointment_detail` mutates state, not just serializes | Read the function before moving it; if it has side effects, leave it in place and only move pure helpers in step 1. |
| Conflict-detection logic isn't actually identical at the two call sites — moving to one shared function changes behavior | Diff the two snippets at `api/main.py:319` and `api/main.py:916` before extracting. If they differ, preserve both behaviors via parameters; do not silently unify. |
| Background-task signatures depend on FastAPI's `BackgroundTasks` injection point | The `services/notifications.py` entry points accept `BackgroundTasks` as a parameter, so the injection still happens at the router boundary. |
| OpenAPI operation IDs change when routes move to a router with a `prefix` or `tags` | Mount routers without a `prefix` (paths already include `/api/...`); set `tags` to match what the OpenAPI doc currently shows for that path (or leave untagged if it currently has no tag). The OpenAPI diff in step 8 verifies this. |
| The empty `api/routes/` directory confuses someone mid-migration | Leave it alone during the refactor; delete in a follow-up cleanup PR. |

## Open Questions

None at design time. Any ambiguity discovered during a step (e.g. two
"identical" code paths turn out to differ) is resolved by **preserving the
existing behavior** and noting it in the PR — not by making a judgment call
that changes the contract.
