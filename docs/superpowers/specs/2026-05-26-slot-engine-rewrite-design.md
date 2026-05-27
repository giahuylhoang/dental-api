# Slot Engine Rewrite — Design

**Status:** Approved (sections 1–4 confirmed)
**Owner:** dental-api
**Replaces:** `tools/slot_utils.py` (296-line single function)

## Problem

The current slot engine in `tools/slot_utils.py` consults only `clinic.working_hour_start/end` (single int) and `ProviderBusyBlock` (block-list). It **ignores** the per-weekday `clinic_operating_hours` table, the `clinic_closures` table, the per-weekday `provider_availability` table, and the `provider_time_off` table — all of which exist in the schema and were intended to drive scheduling.

Concrete production symptoms (probed against `dental-api-v2-database` 2026-05-26):
- Slots appear for Saturday and Sunday even though the clinic is closed.
- Both Soheil and Nadeem return identical 9 AM – 5 PM slots every weekday despite having totally different working schedules.
- Friday evening slots (17:00–18:30) never appear because `clinic.working_hour_end=17` is a single integer.
- The `ProviderBusyBlock` model references `weekdays`, `specific_date`, `recurrence_until`, `label` columns that **no alembic migration creates** — slot queries 500'd in production until we patched via raw `ALTER TABLE`.

## Goals

1. Slot computation respects all 6 schema sources: `clinic_operating_hours`, `clinic_closures`, `provider_availability`, `provider_busy_blocks`, `provider_time_off`, `appointments`.
2. Per-weekday clinic hours work (including lunch carve-outs).
3. Per-provider schedules work (Soheil's Wed half day, Nadeem's Friday morning, etc.).
4. The missing `provider_busy_blocks` columns get a real alembic migration so fresh DBs aren't broken.
5. Public API surface (`/api/calendar/slots` request/response shape) is **unchanged** so v3 voice agent + portal need zero updates.

## Non-Goals

- Removing `clinic.working_hour_start/end` columns from the model. (Defer one release.)
- Per-provider lunch overrides. (YAGNI — clinic-level lunch is enough until a clinic asks.)
- Postgres-only SQL optimization (CTEs / `generate_series`). Engine stays portable; SQLite tests must keep passing.
- Rewriting `find_busy_block_overlap`'s callers in `services/appointments.py`. Keep the function name + signature; rewrite its body.

## Foundational Decisions

| # | Question | Decision |
|---|---|---|
| 1 | What happens when config is missing? | **(C) Hybrid:** `clinic_operating_hours` is **required** (no fallback to legacy `working_hour_start/end`); `provider_availability` is **optional** (empty rows = "match clinic hours"). |
| 2 | Cutover strategy? | **(A) In-place rewrite.** Same signature, same callers, same endpoint. No feature flag, no parallel endpoint. The current engine is already broken in production; there's nothing worth shadow-comparing. |
| 3 | Lunch breaks? | **(A) Respect the `clinic_operating_hours.lunch_start`/`lunch_end` columns** that already exist. Carve `[lunch_start, lunch_end]` out of the day window for all providers. |
| Internal architecture? | **(1) Layered composable helpers.** Break the rewrite into small pure helpers, each owning one concern. |

## Architecture

New package `services/slot_engine/`:

```
services/slot_engine/
  __init__.py              # re-exports get_available_slots, find_busy_block_overlap
  engine.py                # orchestrator (~50 lines)
  windows.py               # clinic_day_window, provider_day_window
  subtract.py              # busy_blocks_for, time_off_for, appointments_for
  chunk.py                 # chunk_into_slots
  intervals.py             # IntervalSet primitive (list[(start,end)] with subtract+intersect)
  types.py                 # dataclasses for inputs/outputs
```

**Shim:** `tools/slot_utils.py` becomes a 3-line re-export from `services.slot_engine` so existing imports (`from tools.slot_utils import get_available_slots`, `find_busy_block_overlap`) keep working without touching callers. The shim is deleted one release later after we confirm nothing else imports `tools.slot_utils`.

**Timezone discipline:** the orchestrator resolves a single `tz = pytz.timezone(timezone_str or clinic.timezone or "America/Edmonton")` at the entry. Every datetime that flows into a helper is timezone-aware. No naïve datetimes inside the package.

**Public surface preserved:**
- `get_available_slots(db, start_datetime, end_datetime, *, provider_id=None, provider_name=None, slot_minutes=30, clinic_id=None, timezone_str=None, hour_start=None, hour_end=None)`
  - Same call shape as today.
  - `hour_start`/`hour_end` kwargs are **accepted and silently ignored**, with a one-time `DeprecationWarning` log per process. Removed in a follow-up release after confirming no callers pass them.
- `find_busy_block_overlap(db, clinic_id, provider_id, start_dt, end_dt, tz) -> Optional[ProviderBusyBlock]` — same signature, rewritten body that uses `subtract.busy_blocks_for(...)`.
- Output shapes:
  - `{"providers": [{"provider_id": int, "title": str, "slots": [iso, ...]}, ...]}` when neither `provider_id` nor `provider_name` is given.
  - `{"provider": {"provider_id": int, "title": str}, "slots": [iso, ...]}` when one is given.

## Helper Contracts

### `intervals.IntervalSet`

Thin wrapper around `list[tuple[datetime, datetime]]`. All intervals are **half-open `[start, end)`** and timezone-aware. Empty interval set is valid.

- `IntervalSet.from_window(start, end) -> IntervalSet` — single-interval constructor; returns empty if `start >= end`.
- `subtract(other: IntervalSet) -> IntervalSet` — returns `self - other`. Used to carve out lunch / busy blocks / time off / appointments.
- `intersect(other: IntervalSet) -> IntervalSet` — returns `self ∩ other`. Used to narrow daily window by provider availability.
- `is_empty -> bool`
- `intervals -> list[tuple[datetime, datetime]]` (sorted, non-overlapping)

~40 lines. No DB access. Fully unit-testable.

### `windows.clinic_day_window(clinic_id, date, db, tz) -> IntervalSet`

Returns the intervals when the clinic is potentially open on `date`.

Algorithm:
1. Query `clinic_closures` overlapping `date` → if any, return empty.
2. Query `clinic_operating_hours` for `(clinic_id, day_of_week=date.weekday())`.
   - If no row → return empty (fail closed) AND log `WARN` (deduped per `(clinic_id, day_of_week)` per process).
   - If `is_closed=True` → return empty.
3. Build `IntervalSet.from_window(date+open_at, date+close_at)` (timezone-aware).
4. If both `lunch_start` and `lunch_end` set on the row, subtract `IntervalSet.from_window(date+lunch_start, date+lunch_end)`. If only one of the two is set, log `WARN` and ignore lunch entirely.

### `windows.provider_day_window(provider_id, clinic_id, date, daily_window, db, tz) -> IntervalSet`

Narrows `daily_window` to a provider's working hours.

Algorithm:
1. Query `provider_availability` for `(provider_id, clinic_id, weekday=date.weekday())`.
2. **If no rows → return `daily_window` unchanged.** (Decision C: provider with no availability config = available during all clinic hours.)
3. Else build a union `IntervalSet` from each row's `[start_hour:start_minute, end_hour:end_minute)` and return `union.intersect(daily_window)`.

### `subtract.busy_blocks_for(provider_id, clinic_id, date, tz, db) -> IntervalSet`

Returns busy intervals from `provider_busy_blocks` for `date`.

A block applies to `date` if:
- `specific_date == date` (one-off), OR
- `weekdays` JSON list contains `date.weekday()` AND (`recurrence_until is None` OR `recurrence_until >= date`), OR
- legacy `weekday` int equals `date.weekday()` AND `specific_date is None` (backwards-compat for pre-migration rows).

If both `specific_date == date` and the row's `weekdays` would also match, `specific_date` wins (the one-off semantics override the recurrence on that day).

Each applying block contributes `IntervalSet.from_window(date+start_time, date+end_time)`; return the union.

### `subtract.time_off_for(provider_id, clinic_id, date, tz, db) -> IntervalSet`

Returns the intersection of `[provider_time_off.start_at, end_at)` rows with `date`. Multi-day vacations contribute the clipped `[date 00:00, date 23:59]` ∩ `[start_at, end_at)` per overlapping date.

### `subtract.appointments_for(provider_id, clinic_id, date, tz, db) -> IntervalSet`

Returns intervals from `appointments` where `status IN (SCHEDULED, CONFIRMED, PENDING_SYNC, PENDING)` (same active-status filter as the current engine). Midnight-crossing appointments are clipped to `date` per overlap.

### `chunk.into_slots(interval_set, slot_minutes) -> list[datetime]`

For each interval `[s, e)` in `interval_set`, emit `s, s+Δ, s+2Δ, …` while `start + Δ ≤ e`. Returns flat sorted list of timezone-aware datetimes. The orchestrator calls `.isoformat()` at the response boundary.

### `engine.get_available_slots(...)`

Orchestrator (~50 lines):

```python
tz = pytz.timezone(timezone_str or clinic.timezone or "America/Edmonton")
providers = resolve_providers(clinic_id, provider_id, provider_name, db)

# Clamp the search window once. All helpers receive timezone-aware datetimes.
request_window = IntervalSet.from_window(start_datetime, end_datetime)

results = {p.id: [] for p in providers}
for date in date_range(start_datetime, end_datetime, tz):
    daily = clinic_day_window(clinic_id, date, db, tz)
    if daily.is_empty:
        continue
    for provider in providers:
        win = provider_day_window(provider.id, clinic_id, date, daily, db, tz)
        win = win.subtract(busy_blocks_for(provider.id, clinic_id, date, tz, db))
        win = win.subtract(time_off_for(provider.id, clinic_id, date, tz, db))
        win = win.subtract(appointments_for(provider.id, clinic_id, date, tz, db))
        # Clip both ends to the request window (handles mid-day start / end).
        win = win.intersect(request_window)
        results[provider.id].extend(chunk_into_slots(win, slot_minutes))

return shape_response(providers, results, provider_id, provider_name)
```

`find_busy_block_overlap(db, clinic_id, provider_id, start_dt, end_dt, tz)` becomes:

```python
def find_busy_block_overlap(db, clinic_id, provider_id, start_dt, end_dt, tz):
    request = IntervalSet.from_window(start_dt, end_dt)
    for date in date_range_inclusive(start_dt, end_dt, tz):
        blocks = busy_blocks_for(provider_id, clinic_id, date, tz, db)
        if not request.intersect(blocks).is_empty:
            return _first_matching_block_row(...)  # original row for caller's error message
    return None
```

## Behavior Matrix

The rule for every behavior: there's exactly one place that decides it. If a behavior isn't listed below, it's a bug to add to this matrix.

| Behavior | Decided by | Result |
|---|---|---|
| Clinic has no `clinic_operating_hours` row for the requested weekday | `clinic_day_window` | Empty (fail closed). Log `WARN` once per `(clinic, weekday, process)`. |
| Clinic has a `clinic_closures` row covering the date | `clinic_day_window` | Empty (no slots for any provider that day). |
| Clinic open with lunch (`lunch_start`/`lunch_end` set) | `clinic_day_window` | Day window = `[open, lunch_start)` + `[lunch_end, close)` |
| Clinic open with only one of `lunch_start`/`lunch_end` set | `clinic_day_window` | Malformed config → ignore lunch entirely + log `WARN`. |
| Provider has no `provider_availability` rows for the weekday | `provider_day_window` | Returns clinic day window unchanged (graceful default per decision C). |
| Provider has multiple `provider_availability` rows for the same weekday (split shift) | `provider_day_window` | Union them, then intersect with clinic day window. |
| Provider availability extends beyond clinic hours | `provider_day_window` | Intersection clips to clinic hours. |
| `provider_busy_blocks` row with `specific_date` AND `weekdays` both set, on a date matching both | `busy_blocks_for` | `specific_date` wins. |
| Legacy `provider_busy_blocks` row (only `weekday` int, no `weekdays` JSON) | `busy_blocks_for` | Treat as recurring weekly block on that single weekday. |
| `provider_busy_blocks.recurrence_until` is in the past | `busy_blocks_for` | Block does not apply on/after that date. |
| `provider_time_off` spans midnight or multiple days | `time_off_for` | Clip to `[date 00:00, date 23:59]` per overlapping date. |
| Appointment with `status IN (CANCELLED, COMPLETED, NO_SHOW)` | `appointments_for` | Ignored. |
| Appointment crosses midnight | `appointments_for` | Clip per overlapping date. |
| Request `start_datetime` or `end_datetime` is mid-day | orchestrator | Per-day windows intersected with `[start_datetime, end_datetime)`. First/last day get clipped to the request bounds. |
| Request `slot_minutes` doesn't divide the window evenly | `chunk.into_slots` | Emit whole `slot_minutes` slots that fit; discard trailing partial. |
| `provider_id` provided, no matching row | `resolve_providers` | `{"provider": {"provider_id": <id>, "title": null}, "slots": []}` |
| `provider_name` provided, no `ILIKE` match | `resolve_providers` | `{"provider": {"provider_id": null, "title": null}, "slots": []}` |
| Neither `provider_id` nor `provider_name` | `resolve_providers` | `{"providers": [...]}` with all active providers for the clinic. |
| No active providers in DB | `resolve_providers` | `{"providers": []}` (200 OK, empty list). |
| `start_datetime` parse fails | orchestrator | `{"providers": []}` (same as today). |
| Range > 90 days | orchestrator | Allowed but log `WARN`. No hard cap. |
| Clinic has no `timezone` AND no `timezone_str` kwarg | orchestrator | Fall back to `"America/Edmonton"`. |

## Migration

New alembic revision `h2i3j4k5l6m7_provider_busy_blocks_v2_columns.py` (revises `g1h2i3j4k5l6`).

```python
def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Idempotent against prod (where we patched via raw ALTER TABLE earlier)
        # AND a fresh DB. ADD COLUMN IF NOT EXISTS is Postgres 9.6+.
        op.execute("ALTER TABLE provider_busy_blocks ALTER COLUMN weekday DROP NOT NULL")
        op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS weekdays VARCHAR")
        op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS specific_date DATE")
        op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS recurrence_until DATE")
        op.execute("ALTER TABLE provider_busy_blocks ADD COLUMN IF NOT EXISTS label VARCHAR")
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_provider_busy_blocks_specific_date "
            "ON provider_busy_blocks (clinic_id, provider_id, specific_date) "
            "WHERE specific_date IS NOT NULL"
        )
    # SQLite path: skip. Test conftest creates the full schema via models.

def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_provider_busy_blocks_specific_date")
        op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS label")
        op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS recurrence_until")
        op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS specific_date")
        op.execute("ALTER TABLE provider_busy_blocks DROP COLUMN IF EXISTS weekdays")
        op.execute("ALTER TABLE provider_busy_blocks ALTER COLUMN weekday SET NOT NULL")
```

The `IF NOT EXISTS` clauses make the migration idempotent against the manual patch I applied via raw `ALTER TABLE` during diagnosis — production already has the columns, and the migration just records them in `alembic_version`.

## Tests

### Per-helper unit tests (new) — `tests/services/test_slot_engine/`

- `test_intervals.py` — `IntervalSet.subtract`/`intersect` (zero-width, fully-contained, edge-touching `[a,b)` vs `[b,c)`, non-overlapping, multiple overlaps)
- `test_clinic_day_window.py` — closed day, lunch carve, missing config (asserts WARN logged), `clinic_closures` overrides, malformed one-sided lunch
- `test_provider_day_window.py` — no availability rows (returns daily window), split shift, availability extending past clinic hours (clipped), availability that's a subset of clinic hours
- `test_busy_blocks_for.py` — recurring weekly (`weekdays=[0,2]`), one-off (`specific_date`), legacy single `weekday`, expired `recurrence_until`, specific_date+weekdays both set on a date matching both
- `test_time_off_for.py` — single day, multi-day, partial-day, midnight-crossing
- `test_appointments_for.py` — active vs cancelled status filter, midnight-crossing appointment
- `test_chunk_into_slots.py` — non-dividing windows, empty interval set, multiple disjoint intervals
- `test_resolve_providers.py` — by id (found/not-found), by name (case-insensitive partial match), none provided, clinic with zero providers

### Integration tests (new) — `tests/test_slot_engine_integration.py`

Concrete scenarios mirroring the Market Mall schedule:
- "Soheil Mon" → empty (no availability)
- "Soheil Tue" → slots 9:00–17:00 in 30-min chunks
- "Soheil Wed" → slots 9:00–12:00 only (half day)
- "Soheil Fri" → slots 15:00, 15:30, 16:00, 16:30, 17:00, 17:30, 18:00 (Soheil 15:00–18:30, clinic 9–18:30 on Fri; half-open `[start, end)` excludes the slot at 18:30)
- "Nadeem Fri" → slots 9:00–12:00 only
- "Sat / Sun any provider" → empty (clinic closed)
- "Existing 10:00-11:00 appointment" → 10:00 and 10:30 slots disappear for that provider
- "Clinic with no operating_hours rows" → empty + WARN logged exactly once across N requests
- "Multi-day time-off" → all overlapped days return empty for that provider

### Replaced — `tests/test_busy_block_enforcement.py`

The old file tests internal shapes of the old algorithm. We delete it and replace with the per-helper + integration coverage above.

### Unchanged — `tests/portal/test_schedule.py`

Tests the public output shape via the portal endpoint. Should pass without modification since we're preserving the API contract.

## Rollout

Single PR. Commits within the PR (this ordering keeps each commit individually mergeable for `git bisect`):

1. **Alembic migration alone** — `h2i3j4k5l6m7_provider_busy_blocks_v2_columns.py`. Idempotent. Production already has the columns from the patch; this just records them in `alembic_version` so a fresh DB won't drift.
2. **`services/slot_engine/` package + unit tests** — pure addition, no callers wired up yet.
3. **Switch over** — rewrite `tools/slot_utils.py` body into a shim that delegates to `services.slot_engine`. Add the integration test file. Delete `tests/test_busy_block_enforcement.py`.

`dental-api/cloudbuild.yaml` requires no changes: the existing `migrate` step runs `alembic upgrade head` which picks up the new revision automatically.

### Post-deploy verification

Re-run the slot probes from the diagnostic session against `https://dental-api-v2-...run.app/api/calendar/slots` with `X-Clinic-Id: market-mall-denture`:

| Probe | Expected outcome |
|---|---|
| Wednesday 13:00 for Soheil | absent (half day, only 9:00–12:00) |
| Friday 13:30 for Soheil | absent (Soheil only works Fri 15:00–18:30) |
| Friday 18:00 for Soheil | present (last slot before close at 18:30 on Fri) |
| Friday 14:00 for Nadeem | absent (Nadeem only works Friday morning, 9:00–12:00) |
| Saturday / Sunday any provider | empty (`{"providers":[{"provider_id":1,"title":"Denturist","slots":[]},…]}`) — or providers omitted entirely; either is acceptable |
| Monday 10:00 for Nadeem | present |
| Wednesday 09:30 for Soheil | present |

If any of these don't match, roll back via the Cloud Run revision history (`gcloud run services update-traffic dental-api-v2 --to-revisions=<prev-revision>=100`) and `alembic downgrade -1` if the DB needs it (the migration is reversible).

## Out of Scope (Follow-ups)

- Drop `clinic.working_hour_start/end` columns from the model. (Defer one release to confirm nothing reads them.)
- Delete `tools/slot_utils.py` shim. (Same one-release deferral.)
- Per-provider lunch overrides. (YAGNI.)
- Caching layer for clinic_operating_hours / provider_availability lookups. (Profile first; at our scale these are sub-ms queries.)
- Postgres-only SQL optimization (CTEs, `generate_series`). (Project supports SQLite tests; revisit only if profiling shows the orchestrator loop is the bottleneck.)
